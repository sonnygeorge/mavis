import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image
from tenacity import retry, stop_after_attempt

from mavis.schema import ActionScene, ActionSceneSpecs
from mavis.llm import LLM
from mavis.prompts import (
    render_generate_scene_specs_prompt,
    render_generate_scene_setup_code_prompt,
)
from mavis.responses import (
    parse_generate_scene_specs_response,
    parse_generate_scene_params_response,
)
from mavis.globals import BASE_SCENE_PATH, TEMP_JSON_PATH


# TODO: (a "someday" improvement)
# Exponential backoff on rate limit errors
# Immediate retry on output parsing errors


def assess_generation_feasibility(action_scene: ActionScene) -> tuple[bool, str | None]:
    # TODO: Implement
    return True, None


@retry(stop=stop_after_attempt(3))
def generate_scene_specs(
    llm: LLM, action_scene: ActionScene
) -> tuple[str, ActionSceneSpecs]:
    prompts = render_generate_scene_specs_prompt(action_scene)
    response = llm.generate(prompts)
    scene_characteristics, scene_specs = parse_generate_scene_specs_response(response)
    return scene_characteristics, scene_specs


@retry(stop=stop_after_attempt(3))
def generate_scene_params(
    llm: LLM,
    action_scene: ActionScene,
    scene_characteristics: str,
    action_scene_specs: ActionSceneSpecs,
) -> str:
    prompts = render_generate_scene_setup_code_prompt(
        action_scene,
        scene_characteristics,
        action_scene_specs,
    )
    response = llm.generate(prompts)
    return parse_generate_scene_params_response(response)


def invoke_blender_render() -> None:
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
    llm: LLM, action_scene: ActionScene, n_camera_positions: int = 1
) -> list[Image.Image]:
    # 1. Assess generation feasibility
    generation_is_feasible, reason = assess_generation_feasibility(action_scene)
    if not generation_is_feasible:
        raise ValueError(f"Generation is not feasible: {reason}")

    # 2. Generate scene specs
    scene_characteristics, action_scene_specs = generate_scene_specs(llm, action_scene)

    print("\nSCENE CHARACTERISTICS:\n", scene_characteristics)
    print("\nACTION SCENE SPECS:\n", action_scene_specs)

    # 3. Generate scene params
    obj_placement_specs = generate_scene_params(
        llm, action_scene, scene_characteristics, action_scene_specs
    )

    print("\nOBJ PLACEMENT SPECS:\n", obj_placement_specs)

    with open(TEMP_JSON_PATH, "w") as f:
        json.dump(obj_placement_specs, f)

    # 4. Invoke Blender to render the scene (reads TEMP_JSON_PATH, saves output)
    invoke_blender_render()

    # TODO: The rest of the pipeline

    # output_images = []
    # for rendered_image, masks in zip(all_rendered_images, all_masks):
    #     # 7. Inpaint background
    #     cur_img = inpaint_background(rendered_image, masks)

    #     # 8. Inpaint pose requirements
    #     for pose_spec in scene_specs.pose:
    #         cur_img = inpaint_pose_spec(cur_img, masks, pose_spec)

    #     output_images.append(cur_img)

    # return output_images
