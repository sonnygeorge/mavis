import os

from mavis.globals import OUTPUT_RENDERS_DIR_PATH, OUTPUT_MASKS_DIR_PATH


def get_completed_renders(
    run_uid: str,
) -> list[tuple[str, os.PathLike, dict[str, os.PathLike]]]:
    render_dir = OUTPUT_RENDERS_DIR_PATH / run_uid
    masks_base_dir = OUTPUT_MASKS_DIR_PATH / run_uid
    for f in render_dir.glob("*.png"):
        masks_dir = masks_base_dir / f.stem
        masks = {f.stem: f for f in masks_dir.glob(f"*.png")}
        yield f.stem, f, masks
