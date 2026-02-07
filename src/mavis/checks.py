import os

from mavis.schema import ActionScene, BinaryResponse, VLMPrompt, YesNo
from mavis.vlm import VLM


def objects_are_preserved(
    image_path: os.PathLike, action_scene: ActionScene, vlm: VLM
) -> bool:
    print("Checking object preservation...")
    for object_str in action_scene.object_strs:
        prompt = f"Is there exactly one {object_str} in the scene? (Yes/No)"
        response = vlm.generate_structured(
            prompt=VLMPrompt(user=prompt, image_paths=[image_path]),
            response_format=BinaryResponse,
        )
        if response.answer == YesNo.no:
            print(f"Scene judged to not have exactly one {object_str}.")
            return False
    return True


_is_object_animate_cache = {}


def is_object_animate(object_name: str, vlm: VLM) -> bool:
    if object_name in _is_object_animate_cache:
        return _is_object_animate_cache[object_name]

    prompt = f'Is a "{object_name}" an animate thing? I.e., does it move of its own accord? (Yes/No)'
    response = vlm.generate_structured(
        prompt=VLMPrompt(user=prompt),
        response_format=BinaryResponse,
    )
    is_animate = response.answer == YesNo.yes

    _is_object_animate_cache[object_name] = is_animate
    return is_animate
