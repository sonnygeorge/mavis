import os
import random
import requests

import fal_client

from mavis.globals import OUTPUT_EDITS_DIR_PATH
from mavis.prompts import render_add_background_prompt, render_modify_pose_prompt


BG_TYPES = [
    "sandy",
    "visually minimal empty green landscape",
    "grassy",
    "empty open industrial space",
    "snowy",
    "plain grassy field",
    "empty cracked dry lake bed",
    "empty tundra",
    "open empty landscape",
    "empty hangar",
    "empty city park",
    "empty indoor tiled space",
    "empty parking lot",
    "empty gravelled area",
    "empty industrial space with concrete floor",
    "plain grassy",
    "visually minimal empty warehouse",
    "empty indoor brick floor space",
    "visually minimal flat arid desert",
    "empty commercial office space",
    "empty minimal skate park",
]

TAKES_ONLY_ONE_IMAGE = {"xai/grok-imagine-image/edit"}

BG_MODEL_SELECTION_DISTRIBUTION_BY_MIN_TRY = {
    1: {
        "fal-ai/hunyuan-image/v3/instruct/edit": 0.2,
        "fal-ai/gpt-image-1.5/edit": 0.15,
        "fal-ai/gemini-25-flash-image/edit": 0.15,
        "fal-ai/flux-2/edit": 0.1,
        "fal-ai/flux-2/turbo/edit": 0.3,
        "xai/grok-imagine-image/edit": 0.1,
    },
    3: {
        "fal-ai/gpt-image-1.5/edit": 0.2,
        "xai/grok-imagine-image/edit": 0.2,
        "fal-ai/hunyuan-image/v3/instruct/edit": 0.2,
        "fal-ai/gemini-25-flash-image/edit": 0.2,
        "fal-ai/flux-2/turbo/edit": 0.07,
        "fal-ai/flux-2/edit": 0.13,
    },
}

POSE_MODEL_SELECTION_DISTRIBUTION_BY_MIN_TRY = {
    1: {
        "fal-ai/hunyuan-image/v3/instruct/edit": 0.2,
        "fal-ai/gpt-image-1.5/edit": 0.15,
        "fal-ai/gemini-25-flash-image/edit": 0.4,
        "fal-ai/flux-2/edit": 0.05,
        "xai/grok-imagine-image/edit": 0.2,
    },
    3: {
        "fal-ai/nano-banana/edit": 0.4,
        "xai/grok-imagine-image/edit": 0.2,
        "fal-ai/hunyuan-image/v3/instruct/edit": 0.2,
        "fal-ai/gemini-25-flash-image/edit": 0.2,
    },
}


def _select_model(
    try_number: int,
    distribution_by_min_try: dict[int, dict[str, float]],
) -> str:
    """Select an image editing model from a weighted distribution based on try number.

    Uses the distribution whose key is the highest value <= try_number.
    E.g. try 1-2 use the key-1 distribution, try 3+ use the key-3 distribution.
    """
    applicable_key = max(k for k in distribution_by_min_try if k <= try_number)
    distribution = distribution_by_min_try[applicable_key]
    models = list(distribution.keys())
    weights = list(distribution.values())
    return random.choices(models, weights=weights, k=1)[0]


def add_background(
    render_id: str,
    run_uid: str,
    render_path: os.PathLike,
    action_scene,
    try_number: int = 1,
) -> os.PathLike:
    background_type = random.choice(BG_TYPES)
    model = _select_model(try_number, BG_MODEL_SELECTION_DISTRIBUTION_BY_MIN_TRY)
    print(f"Adding {background_type} background to render {render_id} (model={model})...")
    prompt = render_add_background_prompt(background_type, action_scene).strip()
    render_url = fal_client.upload_file(render_path)
    image_arg = (
        {"image_url": render_url}
        if model in TAKES_ONLY_ONE_IMAGE
        else {"image_urls": [render_url]}
    )
    result = fal_client.subscribe(
        model,
        arguments={"prompt": prompt, **image_arg},
        with_logs=True,
    )
    edits_dir = OUTPUT_EDITS_DIR_PATH / run_uid / render_id
    edits_dir.mkdir(parents=True, exist_ok=True)
    save_path = edits_dir / "background.png"
    with open(save_path, "wb") as f:
        f.write(requests.get(result["images"][0]["url"]).content)
    return save_path


def modify_pose(
    render_id: str,
    run_uid: str,
    start_img_path: os.PathLike,
    object_name: str,
    pose_specs: list[str],
    masks: dict[str, os.PathLike],
    try_number: int = 1,
) -> os.PathLike:
    model = _select_model(try_number, POSE_MODEL_SELECTION_DISTRIBUTION_BY_MIN_TRY)
    print(
        f"Modifying pose of {object_name} to be: {' | '.join(pose_specs)} (model={model})..."
    )
    prompt = render_modify_pose_prompt(
        object_name=object_name, pose_specs=pose_specs
    ).strip()
    start_img_url = fal_client.upload_file(start_img_path)
    mask_url = fal_client.upload_file(masks[object_name])
    image_arg = (
        {"image_url": start_img_url}
        if model in TAKES_ONLY_ONE_IMAGE
        else {"image_urls": [start_img_url, mask_url]}
    )
    result = fal_client.subscribe(
        model,
        arguments={"prompt": prompt, **image_arg},
        with_logs=True,
    )
    edits_dir = OUTPUT_EDITS_DIR_PATH / run_uid / render_id
    edits_dir.mkdir(parents=True, exist_ok=True)
    save_path = edits_dir / f"{object_name}.png"
    with open(save_path, "wb") as f:
        f.write(requests.get(result["images"][0]["url"]).content)
    return save_path
