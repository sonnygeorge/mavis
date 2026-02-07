from jinja2 import Environment, FileSystemLoader, Template

from mavis.globals import PROMPTS_DIR_PATH
from mavis.schema import ActionScene, VLMPrompt, ActionSceneSpecs

env = Environment(loader=FileSystemLoader(PROMPTS_DIR_PATH))


TEMPLATES: dict[str, Template] = {
    # Generate scene specs prompts
    "generate_scene_specs_system": env.get_template("generate_scene_specs_system.txt"),
    "generate_scene_specs_user": env.get_template("generate_scene_specs_user.txt"),
    # Generate scene setup code prompts
    "generate_scene_params_system": env.get_template("generate_scene_params_system.txt"),
    "generate_scene_params_user": env.get_template("generate_scene_params_user.txt"),
    # Modify pose prompt
    "modify_pose": env.get_template("modify_pose.txt"),
    # Add background prompt
    "add_background": env.get_template("add_background.txt"),
}


def render_generate_scene_specs_prompt(action_scene: ActionScene) -> VLMPrompt:
    system_prompt = TEMPLATES["generate_scene_specs_system"].render()
    readable_action = action_scene.as_readable_string()
    user_prompt = TEMPLATES["generate_scene_specs_user"].render(action=readable_action)
    return VLMPrompt(system=system_prompt, user=user_prompt)


def render_generate_scene_setup_code_prompt(
    action_scene: ActionScene,
    scene_characteristics: str,
    scene_specs: ActionSceneSpecs,
) -> VLMPrompt:
    system_prompt = TEMPLATES["generate_scene_params_system"].render()
    readable_action = action_scene.as_readable_string()
    readable_scene_specs = scene_specs.as_readable_string()
    user_prompt = TEMPLATES["generate_scene_params_user"].render(
        action=readable_action,
        blender_objects=action_scene.object_strs,
        scene_characteristics=scene_characteristics,
        scene_specs=readable_scene_specs,
    )
    return VLMPrompt(system=system_prompt, user=user_prompt)


def _grammatical_join(items: list[str]) -> str:
    """Join a list of strings with commas and 'and', e.g. ['a', 'b', 'c'] -> 'a, b, and c'."""
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def render_add_background_prompt(
    background_type: str, action_scene: ActionScene
) -> str:
    objects_str = _grammatical_join(action_scene.object_strs)
    return TEMPLATES["add_background"].render(
        background_type=background_type,
        objects_str=objects_str,
    )


def render_modify_pose_prompt(object_name: str, pose_specs: list[str]) -> str:
    return TEMPLATES["modify_pose"].render(
        object_name=object_name,
        pose_specs=pose_specs,
    )
