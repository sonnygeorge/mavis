import pytest

from mavis.schema import (
    BlenderObject,
    RelativeWhere,
    ActionScene,
    PromptPair,
    ActionSceneSpecs,
)
from mavis.prompts import (
    render_generate_scene_specs_prompt,
    render_generate_scene_setup_code_prompt,
)


@pytest.fixture
def action_scene():
    who = BlenderObject(object="dog", model="dog.blend")
    does = "throws"
    what = BlenderObject(object="chair", model="chair.blend")
    where = RelativeWhere(
        preposition="over",
        what=BlenderObject(object="bookshelf", model="bookshelf.blend"),
    )
    to_whom = BlenderObject(object="puma", model="puma.blend")
    yield ActionScene(who=who, does=does, what=what, where=where, to_whom=to_whom)


@pytest.fixture
def action_scene_specs():
    position = {
        "dog": ["at a conceivably throwable distance to puma"],
        "chair": ["in the airspace between the dog and puma"],
        "bookshelf": ["in between the dog and puma"],
    }
    orientation = {
        "dog": ["facing puma"],
        "chair": ["randomly skewed"],
        "bookshelf": ["naturally separating the dog and puma"],
    }
    size = {
        "dog": ["large enough to throw chair"],
        "chair": ["small enough to be thrown by dog"],
    }
    pose = {
        "dog": ["in end position of a throwing motion oriented toward the puma"],
        "chair": ["hurtling through air toward puma"],
        "bookshelf": ["naturally separating the dog and puma"],
    }
    yield ActionSceneSpecs(
        position=position, orientation=orientation, size=size, pose=pose
    )


@pytest.fixture
def scene_characteristics():
    return """First, I will ponder what a static scene might look like in which a dog is unambiguously throwing a chair over a bookshelf to a puma (without any of these things being touching).

- Instead of being in the dog's hand (entities must not touch), the chair should probably be flying through the air on a trajectory from the dog, over the bookshelf, to the puma.
- The chair shouldn't be so large that it would be unrealistic for the dog to have thrown it.
- Hurtling through the air, the chair's orientation could be in any direction. However, it might look surreally strange if it was perfectly rightside-up, so it probably ought to have some rotational skew.
- The dog should be in a pose that evidences he was the thrower of the chair and the puma should be anticipating its arrival.

Given this, here are the specifications:
"""


def test_render_generate_scene_specs_prompt(action_scene):
    prompts = render_generate_scene_specs_prompt(action_scene)
    assert isinstance(prompts, PromptPair)


def test_render_generate_scene_setup_code_prompt(
    action_scene, scene_characteristics, action_scene_specs
):
    prompts = render_generate_scene_setup_code_prompt(
        action_scene, scene_characteristics, action_scene_specs
    )
    assert isinstance(prompts, PromptPair)
