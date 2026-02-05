import json

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


def parse_generate_scene_params_response(response: str) -> dict:
    json_start = response.find("```json") + len("```json")
    json_end = response.find("```", json_start + 1)  # Skip opening fence to find closing
    json_str = response[json_start:json_end].strip()
    return json.loads(json_str)
