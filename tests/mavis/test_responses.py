from mavis.responses import (
    parse_generate_scene_specs_response,
    parse_generate_scene_params_response,
)
from mavis.schema import ActionSceneSpecs


def test_parse_generate_scene_specs_response():
    scene_characteristics_str = """To depict a scene where a dog is unambiguously throwing a chair over a bookshelf to a puma, let's first consider the crucial characteristics of such a scene:

1. The dog needs to be positioned on one side of the bookshelf, indicating it is throwing the chair.
2. The chair must be depicted in mid-air, over the bookshelf, towards the puma.
3. The bookshelf must be present as a clear barrier between the dog and the puma.
4. The dog should exhibit a throwing pose, indicating motion.
5. The puma should be positioned on the opposite side of the bookshelf, looking up at the chair to exhibit anticipation.
6. The chair needs to be of a size that a dog can realistically throw, and its orientation while in air should not be perfectly upright to add dynamism to the scene.

Based on these characteristics, here are the specifications in JSON format:"""

    action_scene_specs_str = """```json
{
    "position": {
        "dog": ["on the ground near the base of the bookshelf, facing the puma"],
        "chair": ["in the air above the bookshelf, directed towards the puma"],
        "bookshelf": [
            "standing vertically between the dog and the puma",
            "acting as a barrier"
        ],
        "puma": ["on the ground, just beyond the bookshelf, looking toward the chair"]
    },
    "orientation": {
        "dog": ["facing the puma, in a throwing stance"],
        "puma": ["facing the airspace where the chair is coming down"],
        "bookshelf": ["standing upright, parallel to the ground"],
        "chair": ["randomly skewed in orientation to suggest a dynamic throw"]
    },
    "size": {
        "dog": ["large enough to throw the chair, approximately the size of a medium dog"],
        "chair": ["small enough to be thrown, like a lightweight children's chair"],
        "bookshelf": ["tall enough to create a barrier, comparable to the height of the dog"]
    },
    "pose": {
        "dog": ["in a crouched position, with one paw raised as if throwing"],
        "puma": ["standing alert, eyes focused on the chair in the air"],
        "chair": ["mid-flight, positioned upward in a dynamic angle"]
    }
}
```"""

    expected_action_scene_specs = ActionSceneSpecs(
        position={
            "dog": ["on the ground near the base of the bookshelf, facing the puma"],
            "chair": ["in the air above the bookshelf, directed towards the puma"],
            "bookshelf": [
                "standing vertically between the dog and the puma",
                "acting as a barrier",
            ],
            "puma": [
                "on the ground, just beyond the bookshelf, looking toward the chair"
            ],
        },
        orientation={
            "dog": ["facing the puma, in a throwing stance"],
            "puma": ["facing the airspace where the chair is coming down"],
            "bookshelf": ["standing upright, parallel to the ground"],
            "chair": ["randomly skewed in orientation to suggest a dynamic throw"],
        },
        size={
            "dog": [
                "large enough to throw the chair, approximately the size of a medium dog"
            ],
            "chair": ["small enough to be thrown, like a lightweight children's chair"],
            "bookshelf": [
                "tall enough to create a barrier, comparable to the height of the dog"
            ],
        },
        pose={
            "dog": ["in a crouched position, with one paw raised as if throwing"],
            "puma": ["standing alert, eyes focused on the chair in the air"],
            "chair": ["mid-flight, positioned upward in a dynamic angle"],
        },
    )

    response = scene_characteristics_str + "\n\n" + action_scene_specs_str
    scene_characteristics, parsed_action_scene_specs = (
        parse_generate_scene_specs_response(response)
    )
    assert scene_characteristics == scene_characteristics_str
    assert all(
        [
            expected_action_scene_specs.pose == parsed_action_scene_specs.pose,
            expected_action_scene_specs.orientation
            == parsed_action_scene_specs.orientation,
            expected_action_scene_specs.size == parsed_action_scene_specs.size,
            expected_action_scene_specs.position == parsed_action_scene_specs.position,
        ]
    )


def test_parse_generate_scene_setup_code_response():
    script = """import bpy
import math

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to load and position objects
def load_and_position_object(file_path, location, rotation=(0, 0, 0)):
    bpy.ops.import_scene.obj(filepath=file_path)
    obj = bpy.context.selected_objects[0]
    obj.location = location
    obj.rotation_euler = rotation
    return obj

# Paths to the .blend files (replace '<path>' with the actual paths to your files)
dog_path = '<path_to_dog_blend>'
chair_path = '<path_to_chair_blend>'
bookshelf_path = '<path_to_bookshelf_blend>'
puma_path = '<path_to_puma_blend>'

# Load bookshelf
bookshelf = load_and_position_object(bookshelf_path, location=(0, 0, 2.5))  # Positioned vertically

# Load dog
dog = load_and_position_object(dog_path, location=(-2, 0, 0), rotation=(0, 0, math.radians(45)))  # Crouched and facing the puma

# Load puma
puma = load_and_position_object(puma_path, location=(2, 0, 0), rotation=(0, 0, 0))  # Positioned beyond the bookshelf

# Load chair
chair = load_and_position_object(chair_path, location=(0, 0, 3), rotation=(0, 0, math.radians(45)))  # Positioned in air and skewed

# Set chair in mid-air (to depict throwing)
chair.location.z += 1.2  # Adjust this to make it appear thrown above the shelf

# Optionally: Set the camera for a better view of the action
camera = bpy.data.objects['Camera']
camera.location = (0, -5, 2)  # Position of camera
camera.rotation_euler = (math.radians(60), 0, 0)  # Pointing slightly downwards

# Option to add lighting
if "Light" not in bpy.data.objects:
    bpy.ops.object.light_add(type='POINT', radius=1, location=(0, -5, 5))  # Add a light

# Optionally clear camera and light settings or adjust as needed

# Finished
print("Scene configured successfully")""".strip()
    script_str = f"```python\n{script.strip()}\n```"
    response = f"""To set up the Blender scene based on your specifications, we will create a Python script that performs the following tasks:

1. Import the required objects (dog, chair, bookshelf, puma).
2. Position the objects according to the action depicted.
3. Set the orientation of the objects to suggest the intended dynamics and actions.
4. Use basic transformations to fit the positions and orientations specified.

Here is the Blender Python script:

{script_str}

### Key Parts of the Script:

1. **Clear Existing Objects**: This starts by removing any existing mesh objects to provide a clean slate for the new scene.
   
2. **Load and Position Objects**: A function `load_and_position_object` is defined to load each object, position it, and set its rotation. This function is called for the dog, chair, bookshelf, and puma.

3. **Object Placement**: The dog is placed to the left of the bookshelf, in a throwing stance. The chair is positioned above the bookshelf simulating mid-air and skewed. The puma is placed on the ground on the other side of the bookshelf.

4. **Camera Setup**: The camera is set to get a clear view of the action.

5. **Lighting**: A point light can be added to illuminate the scene.

Make sure to replace the placeholder paths with the actual file paths where your .blend objects are stored. This script allows you to visualize the described action realistically in Blender."""

    blender_setup_code = parse_generate_scene_params_response(response)
    assert blender_setup_code == script
