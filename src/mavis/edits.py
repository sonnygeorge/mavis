import os
import random
import requests

import fal_client

from mavis.globals import OUTPUT_EDITS_DIR_PATH, IMG_EDITS_MODEL
from mavis.prompts import render_add_background_prompt, render_modify_pose_prompt


BG_TYPES = [
    "sandy",
    "grassy",
    "snowy",
    "visually minimal empty warehouse",
]


def add_background(
    render_id: str, run_uid: str, render_path: os.PathLike, action_scene
) -> os.PathLike:
    print(f"Adding background to render {render_id}...")
    background_type = random.choice(BG_TYPES)
    prompt = render_add_background_prompt(background_type, action_scene).strip()
    render_url = fal_client.upload_file(render_path)
    result = fal_client.subscribe(
        # "xai/grok-imagine-image/edit",
        IMG_EDITS_MODEL,
        arguments={
            "prompt": prompt,
            # "image_url": render_url,
            "image_urls": [render_url],
        },
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
) -> os.PathLike:
    print(f"Modifying pose of {object_name}...")
    prompt = render_modify_pose_prompt(
        object_name=object_name, pose_specs=pose_specs
    ).strip()
    start_img_url = fal_client.upload_file(start_img_path)
    mask_url = fal_client.upload_file(masks[object_name])
    result = fal_client.subscribe(
        IMG_EDITS_MODEL,
        arguments={
            "prompt": prompt,
            # "image_url": start_img_url,
            "image_urls": [start_img_url, mask_url],
        },
        with_logs=True,
    )
    edits_dir = OUTPUT_EDITS_DIR_PATH / run_uid / render_id
    edits_dir.mkdir(parents=True, exist_ok=True)
    save_path = edits_dir / f"{object_name}.png"
    with open(save_path, "wb") as f:
        f.write(requests.get(result["images"][0]["url"]).content)
    return save_path
