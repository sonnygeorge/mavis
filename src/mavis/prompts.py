from jinja2 import Environment, FileSystemLoader, Template

from mavis.globals import PROMPTS_DIR_PATH
from mavis.schema import ActionScene, VLMPrompt, ActionSceneSpecs

_env = Environment(loader=FileSystemLoader(PROMPTS_DIR_PATH))


class Templates:
    # Generate scene specs prompts
    GENERATE_SCENE_SPECS_SYSTEM: Template = _env.get_template(
        "generate_scene_specs_system.txt"
    )
    GENERATE_SCENE_SPECS_USER: Template = _env.get_template(
        "generate_scene_specs_user.txt"
    )
    # Generate scene setup code prompts
    GENERATE_SCENE_PARAMS_SYSTEM: Template = _env.get_template(
        "generate_scene_params_system.txt"
    )
    GENERATE_SCENE_PARAMS_USER: Template = _env.get_template(
        "generate_scene_params_user.txt"
    )
    # Modify pose prompt
    MODIFY_POSE: Template = _env.get_template("modify_pose.txt")
    # Add background prompt
    ADD_BACKGROUND: Template = _env.get_template("add_background.txt")
    # Check object preserved prompt
    CHECK_OBJECT_PRESERVED: Template = _env.get_template("check_object_preserved.txt")
    # Check pose edit is improvement prompt
    CHECK_POSE_EDIT_IS_IMPROVEMENT: Template = _env.get_template(
        "check_pose_edit_is_improvement.txt"
    )


def render_generate_scene_specs_prompt(action_scene: ActionScene) -> VLMPrompt:
    system_prompt = Templates.GENERATE_SCENE_SPECS_SYSTEM.render()
    readable_action = action_scene.as_readable_string()
    user_prompt = Templates.GENERATE_SCENE_SPECS_USER.render(action=readable_action)
    return VLMPrompt(system=system_prompt, user=user_prompt)


def render_generate_scene_setup_code_prompt(
    action_scene: ActionScene,
    scene_characteristics: str,
    scene_specs: ActionSceneSpecs,
) -> VLMPrompt:
    system_prompt = Templates.GENERATE_SCENE_PARAMS_SYSTEM.render()
    readable_action = action_scene.as_readable_string()
    readable_scene_specs = scene_specs.as_readable_string()
    user_prompt = Templates.GENERATE_SCENE_PARAMS_USER.render(
        action=readable_action,
        blender_objects=action_scene.object_strs,
        scene_characteristics=scene_characteristics,
        scene_specs=readable_scene_specs,
    )
    return VLMPrompt(system=system_prompt, user=user_prompt)


def _join_list_grammatically(items: list[str]) -> str:
    """Join a list of strings with commas and 'and', e.g. ['a', 'b', 'c'] -> 'a, b, and c'."""
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def render_add_background_prompt(background_type: str, action_scene: ActionScene) -> str:
    objects_str = _join_list_grammatically(action_scene.object_strs)
    return Templates.ADD_BACKGROUND.render(
        background_type=background_type,
        objects_str=objects_str,
    )


def render_check_object_preserved_prompt(
    object_name: str, action_scene: ActionScene
) -> str:
    all_objects_str = _join_list_grammatically(
        [f"a {name}" for name in action_scene.object_strs]
    )
    return Templates.CHECK_OBJECT_PRESERVED.render(
        all_objects_str=all_objects_str,
        object=object_name,
    )


def render_modify_pose_prompt(object_name: str, pose_specs: list[str]) -> str:
    return Templates.MODIFY_POSE.render(
        object=object_name,
        pose_specs=pose_specs,
    )


def render_check_pose_edit_is_improvement_prompt(
    object_name: str, pose_specs: list[str]
) -> str:
    return Templates.CHECK_POSE_EDIT_IS_IMPROVEMENT.render(
        object=object_name,
        pose_specs=pose_specs,
    )
