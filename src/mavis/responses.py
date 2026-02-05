import json

from mavis.globals import BLENDER_OBJECTS, ObjectPlacementSpec
from mavis.schema import ActionSceneSpecs


def parse_generate_scene_specs_response(response: str) -> tuple[str, ActionSceneSpecs]:
    scene_characteristics_end = response.find("```json")
    scene_characteristics = response[:scene_characteristics_end].strip()

    json_start = response.find("```json")
    json_end = response.find("```", json_start + 1)  # Skip opening fence to find closing
    content_start = json_start + len("```json")
    json_str = response[content_start:json_end].strip()
    action_specs = ActionSceneSpecs(**json.loads(json_str))

    return scene_characteristics, action_specs


def parse_generate_scene_params_response(response: str) -> list:
    """Parse LLM response into a list of placement-spec dicts.

    Raises ValueError if no ```json block, JSON is invalid, parsed value is not a list,
    any object_name is not in BLENDER_OBJECTS, or any spec fails ObjectPlacementSpec(**spec).
    """
    json_start_marker = response.find("```json")
    if json_start_marker == -1:
        raise ValueError("Response does not contain a ```json code block")
    json_start = json_start_marker + len("```json")
    json_end = response.find("```", json_start)
    if json_end == -1:
        raise ValueError("Response has unclosed ```json code block")
    json_str = response[json_start:json_end].strip()
    data = json.loads(json_str)
    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON list of placement specs, got {type(data).__name__}"
        )

    for i, spec in enumerate(data):
        if not isinstance(spec, dict):
            raise ValueError(
                f"Placement spec at index {i} must be an object, got {type(spec).__name__}"
            )
        parsed = ObjectPlacementSpec(**spec)
        if parsed.object_name not in BLENDER_OBJECTS:
            raise ValueError(
                f"Placement spec at index {i}: unknown object_name {parsed.object_name!r}. "
            )

    return data
