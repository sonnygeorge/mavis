import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

N_POVS = 6

IMG_RESOLUTION_X = 512
IMG_RESOLUTION_Y = 512


OBJAVERSE_DIR_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "objaverse"
OBJAVERSE_SHAPES_DIR_PATH = OBJAVERSE_DIR_PATH / "shapes"
BASE_SCENE_PATH = OBJAVERSE_DIR_PATH / "base_scene.blend"

PROMPTS_DIR_PATH = Path(__file__).resolve().parent / "prompts"

TEMP_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "temp.json"

OUTPUT_DIR_PATH = Path(__file__).resolve().parent.parent.parent / "outputs"
OUTPUT_RENDERS_DIR_PATH = OUTPUT_DIR_PATH / "renders"
OUTPUT_MASKS_DIR_PATH = OUTPUT_DIR_PATH / "masks"
OUTPUT_EDITS_DIR_PATH = OUTPUT_DIR_PATH / "edits"
FINAL_OUTPUTS_DIR_PATH = OUTPUT_DIR_PATH / "final"
SCENE_SPECS_DIR_PATH = OUTPUT_DIR_PATH / "scene_specs"

CUR_RUN_UID_ENV_VAR = "CUR_MAVIS_RUN_UID"


@dataclass
class BlenderObject:
    name: str  # e.g. "dog"
    file: str  # e.g. "dog.blend"
    scale: float
    group: Literal["small", "medium", "large"]
    default_orientation: Optional[str] = None

    @property
    def object_path(self) -> Path:
        return OBJAVERSE_SHAPES_DIR_PATH / self.file / "Object" / self.name


_blender_object_data = json.load(open(OBJAVERSE_DIR_PATH / "properties.json"))

BLENDER_OBJECTS: dict[str, BlenderObject] = {
    name: BlenderObject(**data) for name, data in _blender_object_data.items()
}


@dataclass
class ObjectPlacementSpec:
    """Specification for placing an object in a Blender scene.

    Attributes:
        object_name: Name of the object to place.
        target_location: (x, y, z) location of the object.
        target_facing_direction: Optional Euler angles (x, y, z) in radians for
            object rotation. If None, no rotation is applied.
        touching_ground: Whether the object should be touching the ground.
    """

    object_name: str
    target_location: list[float]
    target_facing_direction: list[float] | None
    touching_ground: bool
