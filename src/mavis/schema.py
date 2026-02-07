import json
import os
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator
from mavis.globals import BlenderObject, BLENDER_OBJECTS


def _resolve_blender_object(
    v: str | BlenderObject | None,
) -> BlenderObject | None:
    """Convert string to BlenderObject via registry, or pass through if already one."""
    if v is None:
        return None
    if isinstance(v, str):
        if v not in BLENDER_OBJECTS:
            raise ValueError(
                f"Unknown object '{v}'. Available: {list(BLENDER_OBJECTS.keys())}"
            )
        return BLENDER_OBJECTS[v]
    return v


class RelativeWhere(BaseModel):
    """Relative spatial relation to another object."""

    preposition: str
    what: BlenderObject

    @field_validator("what", mode="before")
    @classmethod
    def resolve_what(cls, v: str | BlenderObject) -> BlenderObject:
        result = _resolve_blender_object(v)
        assert result is not None  # what is required
        return result


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

    @field_validator("who", mode="before")
    @classmethod
    def resolve_who(cls, v: str | BlenderObject) -> BlenderObject:
        return _resolve_blender_object(v)  # type: ignore[return-value]

    @field_validator("what", "to_whom", mode="before")
    @classmethod
    def resolve_what_to_whom(cls, v: str | BlenderObject | None) -> BlenderObject | None:
        return _resolve_blender_object(v)

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
            f"who: {self.who.name}",
            f"does: {self.does}",
        ]
        if self.what is not None:
            lines.append(f"what: {self.what.name}")
        if self.where is not None:
            lines.append(f"where: {self.where.preposition} {self.where.what.name}")
        if self.to_whom is not None:
            lines.append(f"to whom: {self.to_whom.name}")
        return "\n".join(lines)

    @property
    def shorthand_str(self) -> str:
        """Upper-camel shorthand string, e.g. 'ViJuOvBoLa'."""
        parts = [
            self.who.name[:2],
            self.does[:2],
            self.what.name[:2] if self.what else "",
            self.where.preposition[:2] if self.where else "",
            self.where.what.name[:2] if self.where else "",
            self.to_whom.name[:2] if self.to_whom else "",
        ]
        return "".join(p.capitalize() for p in parts)

    @property
    def object_strs(self) -> list[str]:
        return [
            x
            for x in [
                self.who.name,
                self.what.name if self.what else None,
                self.where.what.name if self.where else None,
                self.to_whom.name if self.to_whom else None,
            ]
            if x is not None
        ]


class ActionSceneSpecs(BaseModel):
    position: dict[str, list[str]]
    orientation: dict[str, list[str]]
    size: dict[str, list[str]]
    pose: dict[str, list[str]]

    def as_readable_string(self) -> str:
        return json.dumps(self.model_dump(), indent=2)


class YesNo(StrEnum):
    yes = "Yes"
    no = "No"


class BinaryResponse(BaseModel):
    answer: YesNo


class VLMPrompt(BaseModel):
    system: str | None = None
    user: str
    image_paths: list[os.PathLike] = []
