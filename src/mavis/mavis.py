import json
import os
import subprocess
import sys
import shutil
import warnings
from pathlib import Path
from datetime import datetime
from requests.exceptions import HTTPError

from fal_client.client import FalClientHTTPError

from PIL import Image

from tenacity import retry, stop_after_attempt

from mavis.schema import ActionScene, ActionSceneSpecs
from mavis.vlm import VLM
from mavis.edits import add_background, modify_pose
from mavis.checks import objects_are_preserved, is_object_animate, pose_edit_is_improvement
from mavis.prompts import (
    render_generate_scene_specs_prompt,
    render_generate_scene_setup_code_prompt,
)
from mavis.utils import get_completed_renders
from mavis.responses import (
    parse_generate_scene_specs_response,
    parse_generate_scene_params_response,
)
from mavis.globals import (
    BASE_SCENE_PATH,
    SCENE_SPECS_DIR_PATH,
    TEMP_JSON_PATH,
    CUR_RUN_UID_ENV_VAR,
    FINAL_OUTPUTS_DIR_PATH,
)


# TODO: (a "someday" improvement)
# Exponential backoff on rate limit errors
# Immediate retry on output parsing errors


class MaxRetries:
    GENERATE_SCENE_SPECS = 3
    GENERATE_SCENE_PARAMS = 3
    ADD_BACKGROUND = 4
    MODIFY_STATE = 3


def assess_generation_feasibility(action_scene: ActionScene) -> tuple[bool, str | None]:
    # TODO: Implement
    return True, None


@retry(stop=stop_after_attempt(MaxRetries.GENERATE_SCENE_SPECS))
def generate_scene_specs(
    vlm: VLM, action_scene: ActionScene
) -> tuple[str, ActionSceneSpecs]:
    prompts = render_generate_scene_specs_prompt(action_scene)
    response = vlm.generate(prompts)
    scene_characteristics, scene_specs = parse_generate_scene_specs_response(response)
    return scene_characteristics, scene_specs


@retry(stop=stop_after_attempt(MaxRetries.GENERATE_SCENE_PARAMS))
def generate_scene_params(
    vlm: VLM,
    action_scene: ActionScene,
    scene_characteristics: str,
    action_scene_specs: ActionSceneSpecs,
) -> str:
    prompts = render_generate_scene_setup_code_prompt(
        action_scene,
        scene_characteristics,
        action_scene_specs,
    )
    response = vlm.generate(prompts)
    return parse_generate_scene_params_response(response)


def invoke_and_await_scene_render_subprocess() -> None:
    """Run Blender in background to render the scene from TEMP_JSON_PATH.

    Requires Blender in PATH, or set BLENDER_EXE in the environment (e.g. on macOS:
    BLENDER_EXE="/Applications/Blender.app/Contents/MacOS/Blender").
    """
    blender_exe = os.environ.get("BLENDER_EXE", "blender")
    project_root = Path(__file__).resolve().parent.parent.parent
    subprocess.run(
        [
            blender_exe,
            "--background",
            str(BASE_SCENE_PATH),
            "--python",
            "src/mavis/render_scene.py",
        ],
        cwd=project_root,
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def run(
    vlm: VLM, action_scene: ActionScene, n_camera_positions: int = 1
) -> list[Image.Image]:

    # 1. Assess generation feasibility
    generation_is_feasible, reason = assess_generation_feasibility(action_scene)
    if not generation_is_feasible:
        raise ValueError(f"Generation is not feasible: {reason}")

    # Create short UID for the run and set the env variable
    run_uid = f"{datetime.now().strftime('%y%m%d%H%M%S')}_{action_scene.shorthand_str}"
    os.environ[CUR_RUN_UID_ENV_VAR] = run_uid
    print(f"Beginning pipeline run with UID={run_uid} and action scene:")
    print(action_scene.as_readable_string())

    # 2. Generate scene specs
    scene_characteristics, action_scene_specs = generate_scene_specs(vlm, action_scene)

    # Save scene specs as JSON to SCENE_PARAMS_DIR_PATH
    SCENE_SPECS_DIR_PATH.mkdir(parents=True, exist_ok=True)
    with open(SCENE_SPECS_DIR_PATH / f"{run_uid}.json", "w") as f:
        json.dump(action_scene_specs.model_dump(), f, indent=3)

    # 3. Generate scene params
    obj_placement_specs = generate_scene_params(
        vlm, action_scene, scene_characteristics, action_scene_specs
    )

    # # TODO: Remove this convenient hardcoded artifact used for quicker testing
    # obj_placement_specs = [
    #     {
    #         "object_name": "person",
    #         "target_location": [-3.0, 0.0, 0.0],
    #         "target_facing_direction": [0.0, 0.0, 0.0],
    #         "touching_ground": True,
    #     },
    #     {
    #         "object_name": "laptop",
    #         "target_location": [1.0, 0.0, 1.45],
    #         "target_facing_direction": [0.55, -0.2, 0.7],
    #         "touching_ground": False,
    #     },
    #     {
    #         "object_name": "couch",
    #         "target_location": [0.0, 0.0, 0.0],
    #         "target_facing_direction": [0.0, 0.0, 1.57079632679],
    #         "touching_ground": True,
    #     },
    #     {
    #         "object_name": "tree",
    #         "target_location": [4.2, 0.0, 0.0],
    #         "target_facing_direction": [0.0, 0.0, 0.0],
    #         "touching_ground": True,
    #     },
    # ]

    with open(TEMP_JSON_PATH, "w") as f:
        json.dump(obj_placement_specs, f)

    # 4. Invoke Blender to render the scene (reads TEMP_JSON_PATH, saves renders))
    invoke_and_await_scene_render_subprocess()

    # 5. Make edits to rendered images
    edits_were_successful = {}
    for render_id, render_path, masks in get_completed_renders(run_uid):
        # 5.1. Add background
        bg_added_successfully = False
        for try_number in range(1, MaxRetries.ADD_BACKGROUND + 1):
            try:
                img_with_bg_path = add_background(
                    render_id=render_id,
                    run_uid=run_uid,
                    render_path=render_path,
                    action_scene=action_scene,
                    try_number=try_number,
                )
            # Sometimes images trigger false positive of content violation policies
            except (HTTPError, FalClientHTTPError) as e:
                warnings.warn(f"HTTP error: {e}")
                break

            if objects_are_preserved(img_with_bg_path, action_scene, vlm):
                bg_added_successfully = True
                break

        if not bg_added_successfully:
            warnings.warn(
                f"Failed to add background for render {render_id} after "
                f"{MaxRetries.ADD_BACKGROUND} retries. Skipping this render."
            )
            edits_were_successful[render_id] = False
            print(f"FAILED: edits aborted for render {render_id}.")
            continue

        # 5.2. Modify poses
        cur_img_path = img_with_bg_path
        for object_name, pose_specs in action_scene_specs.state.items():
            pose_was_successfully_modified = False
            # Combine state and orientation specs to get "pose" specs
            pose_specs = pose_specs + action_scene_specs.orientation[object_name]
            obj_is_animate = is_object_animate(object_name, vlm)
            for try_number in range(1, MaxRetries.MODIFY_STATE + 1):
                try:
                    modified_pose_img_path = modify_pose(
                        render_id=render_id,
                        run_uid=run_uid,
                        start_img_path=cur_img_path,
                        object_name=object_name,
                        pose_specs=pose_specs,
                        masks=masks,
                        try_number=try_number,
                    )
                    if objects_are_preserved(modified_pose_img_path, action_scene, vlm):
                        pose_was_successfully_modified = True
                        if not obj_is_animate and not pose_edit_is_improvement(
                            pre_edit_path=cur_img_path,
                            post_edit_path=modified_pose_img_path,
                            object_name=object_name,
                            pose_specs=pose_specs,
                            vlm=vlm,
                        ):
                            print(
                                f"Pose edit for inanimate object '{object_name}' "
                                f"deemed worse than original — keeping pre-edit image."
                            )
                        else:
                            cur_img_path = modified_pose_img_path
                        break
                # Sometimes images trigger false positive of content violation policies
                except (HTTPError, FalClientHTTPError) as e:
                    warnings.warn(f"HTTP error: {e}")
                    break
            if not pose_was_successfully_modified:
                break

        if not pose_was_successfully_modified:
            warnings.warn(
                f"Failed to modify pose for object {object_name} after "
                f"{MaxRetries.MODIFY_STATE} retries. Skipping this render."
            )
            edits_were_successful[render_id] = False
            print(f"FAILED: edits aborted for render {render_id}.")
            continue

        edits_were_successful[render_id] = True
        print(f"SUCCESS: edits made to render {render_id}.")

        # If edits were successful, copy the final image to the final output dir
        final_output_dir = FINAL_OUTPUTS_DIR_PATH / run_uid
        final_output_dir.mkdir(parents=True, exist_ok=True)
        if edits_were_successful[render_id]:
            shutil.copy(cur_img_path, final_output_dir / f"{render_id}.png")

    print(f"Edits were successful: {edits_were_successful}")
