import os

from mavis.prompts import (
    render_check_object_preserved_prompt,
    render_check_pose_edit_is_improvement_prompt,
)
from mavis.schema import (
    ActionScene,
    BinaryResponse,
    ImageChoice,
    ImageComparisonResponse,
    VLMPrompt,
    YesNo,
)
from mavis.vlm import VLM


OBJECT_PRESERVATION_CONFIDENCE_THRESHOLD = 0.9  # 0.75


def objects_are_preserved(
    image_path: os.PathLike, action_scene: ActionScene, vlm: VLM
) -> bool:
    print("Checking object preservation...")
    for object_str in action_scene.object_strs:
        prompt = render_check_object_preserved_prompt(object_str, action_scene)
        response = vlm.generate_structured(
            prompt=VLMPrompt(user=prompt, image_paths=[image_path]),
            response_format=BinaryResponse,
        )
        is_no = response.answer == YesNo.no
        is_confident = response.confidence >= OBJECT_PRESERVATION_CONFIDENCE_THRESHOLD
        if is_no and is_confident:
            print(
                f"Scene judged to not have exactly one {object_str} "
                f"(confidence: {response.confidence:.2f})."
            )
            return False
        elif is_no:
            print(
                f"VLM said #{object_str}s != 1, but confidence is low "
                f"({response.confidence:.2f} < {OBJECT_PRESERVATION_CONFIDENCE_THRESHOLD}) "
                f"— passing anyway."
            )
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


def pose_edit_is_improvement(
    pre_edit_path: os.PathLike,
    post_edit_path: os.PathLike,
    object_name: str,
    pose_specs: list[str],
    vlm: VLM,
) -> bool:
    """Ask a VLM whether a pose edit improved the image for an inanimate object.

    Shows the pre-edit image (first) and post-edit image (second) and asks which
    better satisfies the pose specs. Returns True if the edited image is preferred.
    """
    print(f"Checking if pose edit improved {object_name}...")
    prompt = render_check_pose_edit_is_improvement_prompt(object_name, pose_specs)
    response = vlm.generate_structured(
        prompt=VLMPrompt(
            user=prompt,
            image_paths=[pre_edit_path, post_edit_path],
        ),
        response_format=ImageComparisonResponse,
    )
    edit_is_better = response.answer == ImageChoice.second
    is_confident = response.confidence > 0.75
    print(
        f"VLM preferred {'edited' if edit_is_better else 'original'} image for "
        f"{object_name} (confidence: {response.confidence:.2f})."
    )
    if edit_is_better and not is_confident:
        print(
            f"Confidence too low ({response.confidence:.2f} <= 0.75) "
            f"— not accepting edit as improvement."
        )
    return edit_is_better and is_confident
