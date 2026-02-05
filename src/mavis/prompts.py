from jinja2 import Environment, FileSystemLoader, Template

from mavis.constants import PROMPTS_DIR_PATH
from mavis.schema import ActionScene, PromptPair, BlenderObject, ActionSceneSpecs

env = Environment(loader=FileSystemLoader(PROMPTS_DIR_PATH))


TEMPLATES: dict[str, Template] = {
    # Generate scene specs prompts
    "generate_scene_specs_system": env.get_template("generate_scene_specs_system.txt"),
    "generate_scene_specs_user": env.get_template("generate_scene_specs_user.txt"),
    # Generate scene setup code prompts
    "generate_scene_setup_code_system": env.get_template(
        "generate_scene_setup_code_system.txt"
    ),
    "generate_scene_setup_code_user": env.get_template(
        "generate_scene_setup_code_user.txt"
    ),
}


def render_generate_scene_specs_prompt(action_scene: ActionScene) -> PromptPair:
    system_prompt = TEMPLATES["generate_scene_specs_system"].render()
    readable_action = action_scene.as_readable_string()
    user_prompt = TEMPLATES["generate_scene_specs_user"].render(action=readable_action)
    return PromptPair(system=system_prompt, user=user_prompt)


def render_generate_scene_setup_code_prompt(
    action_scene: ActionScene,
    scene_characteristics: str,
    scene_specs: ActionSceneSpecs,
) -> PromptPair:
    system_prompt = TEMPLATES["generate_scene_setup_code_system"].render()
    readable_action = action_scene.as_readable_string()
    readable_blender_objects = [
        action_scene.who.as_readable_string(),
        action_scene.what.as_readable_string(),
        action_scene.where.what.as_readable_string(),
        action_scene.to_whom.as_readable_string(),
    ]
    readable_scene_specs = scene_specs.as_readable_string()
    user_prompt = TEMPLATES["generate_scene_setup_code_user"].render(
        action=readable_action,
        blender_objects=readable_blender_objects,
        scene_characteristics=scene_characteristics,
        scene_specs=readable_scene_specs,
    )
    return PromptPair(system=system_prompt, user=user_prompt)
