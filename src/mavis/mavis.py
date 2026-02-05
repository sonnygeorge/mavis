import json

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
from mavis.globals import TEMP_JSON_PATH


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


    # TODO: The rest of the pipeline

    # # 4. Setup scene
    # with BlenderEnv() as blender:
    #     blender.setup_scene(scene_setup_code)

    #     # 5. Determine set of diverse camera positions
    #     camera_positions = determine_camera_positions()

    #     # 6. Render scene from camera positions
    #     all_rendered_images, all_masks = render_scene(blender, camera_positions)

    # output_images = []
    # for rendered_image, masks in zip(all_rendered_images, all_masks):
    #     # 7. Inpaint background
    #     cur_img = inpaint_background(rendered_image, masks)

    #     # 8. Inpaint pose requirements
    #     for pose_spec in scene_specs.pose:
    #         cur_img = inpaint_pose_spec(cur_img, masks, pose_spec)

    #     output_images.append(cur_img)

    # return output_images
