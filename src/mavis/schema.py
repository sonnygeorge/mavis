from typing import Optional
from pydantic import BaseModel, field_validator

from constants import OBJAVERSE_DIR


def assert_valid_blend_filename(name: str) -> str:
    """Ensure value is a .blend filename that exists."""
    if not name.endswith(".blend"):
        raise ValueError("Value must be a .blend filename.")
    blend_path = OBJAVERSE_DIR / name
    if not blend_path.exists():
        raise ValueError(f"Missing blend file: {blend_path}")
    return name


class BlenderObject(BaseModel):
    """Reference to a 3D object: semantic name and .blend model file."""

    object: str  # e.g. "dog"
    model: str  # e.g. "dog.blend"

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate .blend filename exists."""
        return assert_valid_blend_filename(v)


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
