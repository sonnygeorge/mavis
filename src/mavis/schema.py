from functools import cache
from typing import Optional
from pydantic import BaseModel, field_validator

import bpy

from .constants import OBJAVERSE_SHAPES_DIR_PATH


class BlenderObjectDimensions(BaseModel):
    """Dimensions of a 3D object in Blender units."""

    x: float  # width
    y: float  # height
    z: float  # depth


@cache
def _get_blender_object_dimensions(
    object_name: str, model: str
) -> BlenderObjectDimensions:
    """Load .blend and return dimensions (cached per object/model)."""
    bpy.ops.wm.open_mainfile(filepath=str(OBJAVERSE_SHAPES_DIR_PATH / model))
    dims = bpy.data.objects[object_name].dimensions
    result = BlenderObjectDimensions(x=dims.x, y=dims.y, z=dims.z)
    return result


class BlenderObject(BaseModel):
    """Reference to a 3D object: semantic name and .blend model file."""

    object: str  # e.g. "dog"
    model: str  # e.g. "dog.blend"

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate .blend filename exists."""
        if not v.endswith(".blend"):
            raise ValueError("Value must be a .blend filename.")
        blend_path = OBJAVERSE_SHAPES_DIR_PATH / v
        if not blend_path.exists():
            raise ValueError(f"Missing blend file: {blend_path}")
        return v

    def get_dimensions(self) -> BlenderObjectDimensions:
        """Get the dimensions of the object (cached per object/model for this process)."""
        return _get_blender_object_dimensions(self.object, self.model)

    def as_readable_string(self) -> str:
        """Return a human-readable representation of the object."""
        dims = self.get_dimensions()
        w_str = f"width(x)={dims.x}"
        h_str = f"height(y)={dims.y}"
        d_str = f"depth(z)={dims.z}"
        return f"{self.object}: {w_str}, {h_str}, {d_str}"


class RelativeWhere(BaseModel):
    """Relative spatial relation to another object."""

    preposition: str
    what: BlenderObject


class ActionScene(BaseModel):
    """
    Structured action scene description.

    Example:
        ```json
        {
            "who": {"object": "dog", "model": "dog.blend"},
            "does": "throws",
            "what": {"object": "chair", "model": "chair.blend"},
            "where": {
                "preposition": "over",
                "what": {"object": "fence", "model": "fence.blend"}
            },
            "to_whom": {"object": "puma", "model": "puma.blend"}
        }
        ```
    """

    who: BlenderObject
    does: str
    what: Optional[BlenderObject] = None
    where: Optional[RelativeWhere] = None
    to_whom: Optional[BlenderObject] = None

    def as_readable_string(self) -> str:
        """
        Return a human-readable representation of the action scene.

        Example:
        ```
        who: dog
        does: throws
        what: chair
        where: over fence
        to whom: puma
        ```
        """
        lines = [
            f"who: {self.who.object}",
            f"does: {self.does}",
        ]
        if self.what is not None:
            lines.append(f"what: {self.what.object}")
        if self.where is not None:
            lines.append(f"where: {self.where.preposition} {self.where.what.object}")
        if self.to_whom is not None:
            lines.append(f"to whom: {self.to_whom.object}")
        return "\n".join(lines)


class ActionSceneSpecs(BaseModel):
    position: dict[str, list[str]]
    orientation: dict[str, list[str]]
    size: dict[str, list[str]]
    pose: dict[str, list[str]]


class PromptPair(BaseModel):
    system: str
    user: str
