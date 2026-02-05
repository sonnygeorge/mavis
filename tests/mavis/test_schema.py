import pytest

from mavis.schema import BlenderObject, BlenderObjectDimensions


@pytest.fixture
def blender_object():
    yield BlenderObject(object="puma", model="puma.blend")


def test_blender_object_get_dimensions(blender_object):
    dims = blender_object.get_dimensions()
    assert isinstance(dims, BlenderObjectDimensions)
