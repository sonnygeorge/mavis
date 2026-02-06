import json
import math
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path as _Path

import numpy as np
import bpy
from mathutils import Vector

_src = _Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from mavis.globals import (
    N_POVS,
    BLENDER_OBJECTS,
    ObjectPlacementSpec,
    BASE_SCENE_PATH,
    TEMP_JSON_PATH,
    IMG_RESOLUTION_X,
    IMG_RESOLUTION_Y,
    OUTPUT_RENDERS_DIR_PATH,
    OUTPUT_MASKS_DIR_PATH,
)

MAX_CAMERA_ANGLE_SAMPLES = 50
MAX_RENDER_ATTEMPTS = 5
BLENDER_CAMERA_FOV_ANGLE_RADS = math.radians(60)


@dataclass
class BoundingBox:
    center: Vector
    corners: list[Vector]


def compute_combined_bbox(objects: list[bpy.types.Object]) -> BoundingBox:
    """Compute the combined AABB of all objects in world space. Returns center and 8 corners."""
    all_corners: list[Vector] = []
    for obj in objects:
        for corner in obj.bound_box:
            all_corners.append(obj.matrix_world @ Vector(corner))
    if not all_corners:
        return BoundingBox(center=Vector((0, 0, 0)), corners=[])
    min_x = min(v.x for v in all_corners)
    max_x = max(v.x for v in all_corners)
    min_y = min(v.y for v in all_corners)
    max_y = max(v.y for v in all_corners)
    min_z = min(v.z for v in all_corners)
    max_z = max(v.z for v in all_corners)
    center = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2))
    corners = [
        Vector((min_x, min_y, min_z)),
        Vector((min_x, min_y, max_z)),
        Vector((min_x, max_y, min_z)),
        Vector((min_x, max_y, max_z)),
        Vector((max_x, min_y, min_z)),
        Vector((max_x, min_y, max_z)),
        Vector((max_x, max_y, min_z)),
        Vector((max_x, max_y, max_z)),
    ]
    return BoundingBox(center=center, corners=corners)


def convert_pitch_and_tilt_to_unit_vector(pitch: float, tilt: float) -> Vector:
    """Convert pitch and tilt to a normal unit vector."""
    el, az = pitch, tilt
    vec = Vector(
        (
            math.cos(el) * math.cos(az),
            math.cos(el) * math.sin(az),
            -math.sin(el),
        )
    )
    vec.normalize()
    return vec


def place_objects(specs: list[ObjectPlacementSpec]) -> list[bpy.types.Object]:
    """Add objects to the current Blender scene according to placement specifications."""
    placed: list[bpy.types.Object] = []
    for spec in specs:
        object_data = BLENDER_OBJECTS[spec.object_name]

        # Append the object to the scene (directory = path to Object collection, not the object itself)
        object_dir = object_data.object_path.parent
        bpy.ops.wm.append(directory=str(object_dir), filename=object_data.name)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS", center="BOUNDS")

        # Select the object
        selected_obj = bpy.data.objects[object_data.name]
        bpy.ops.object.select_all(action="DESELECT")
        selected_obj.select_set(True)
        bpy.context.view_layer.objects.active = selected_obj

        # Set object position to origin before scaling
        selected_obj.location = (0, 0, 0)

        # Scale the object
        scale = object_data.scale
        bpy.ops.transform.resize(value=(scale, scale, scale))

        # Compute placement: if touching_ground, align bottom to target_location z
        x, y, z = spec.target_location
        bbox = [
            selected_obj.matrix_world @ Vector(corner)
            for corner in selected_obj.bound_box
        ]
        min_z = min(v.z for v in bbox)

        # Translate the object to the target location
        if spec.touching_ground:
            bpy.ops.transform.translate(value=(x, y, z - min_z))
        else:
            bpy.ops.transform.translate(value=(x, y, z))

        # Apply rotation if specified
        selected_obj.rotation_mode = "XYZ"
        if spec.target_facing_direction is not None:
            selected_obj.rotation_euler = list(spec.target_facing_direction)

        # De-select all objects
        bpy.ops.object.select_all(action="DESELECT")
        placed.append(selected_obj)
    return placed


def compute_min_camera_distance_to_capture_bbox(
    bbox: BoundingBox,
    camera_pitch: float,
    camera_tilt: float,
    camera_fov_angle_rads: float,
    camera_aspect_ratio: float,
) -> float:
    """
    Assuming a camera pointing in this direction towards the center of the bounding box,
    returns the minimum camera distance such that the projection of all eight bbox corners
    lies within the normalized image frame. Assume z is up and camera roll is 0.
    """
    if not bbox.corners:
        return 0.0
    center = bbox.center
    corners = bbox.corners
    look_dir = convert_pitch_and_tilt_to_unit_vector(camera_pitch, camera_tilt)
    # Camera frame derived from look_dir with Z-up reference (matches Blender's to_track_quat)
    rot = look_dir.to_track_quat("-Z", "Y").to_matrix()
    right = Vector(rot.col[0])  # camera local +X
    up = Vector(rot.col[1])  # camera local +Y
    # Half-angles: Blender angle is horizontal FOV
    half_h = camera_fov_angle_rads / 2
    half_v = math.atan(math.tan(half_h) / camera_aspect_ratio)
    tan_h = math.tan(half_h)
    tan_v = math.tan(half_v)
    d_candidates: list[float] = []
    for p in corners:
        p_rel = p - center
        depth_offset = p_rel.dot(look_dir)
        x_cam = p_rel.dot(right)
        y_cam = p_rel.dot(up)
        min_depth = max(abs(x_cam) / tan_h, abs(y_cam) / tan_v)
        d_candidates.append(min_depth - depth_offset)
    return max(0.0, max(d_candidates))


def render_object_masks(
    placed_objects: list[bpy.types.Object],
) -> list[np.ndarray]:
    """Render a binary alpha mask for each placed object individually.

    Switches to EEVEE for speed, enables transparent film, and renders each
    object in isolation (all other meshes hidden).  Returns a list of binary
    masks (H x W, values 0.0 or 1.0), one per placed object.
    """
    scene = bpy.context.scene
    render_args = scene.render

    # Save render state to restore later
    orig_engine = render_args.engine
    orig_film_transparent = render_args.film_transparent
    orig_file_format = render_args.image_settings.file_format
    orig_color_mode = render_args.image_settings.color_mode
    orig_filepath = render_args.filepath
    orig_hide_render = {obj.name: obj.hide_render for obj in bpy.data.objects}

    # Configure for fast mask rendering
    render_args.engine = "BLENDER_EEVEE_NEXT"  # Use BLENDER_EEVEE_NEXT on Blender 4.0/4.1
    render_args.film_transparent = True
    render_args.image_settings.file_format = "PNG"
    render_args.image_settings.color_mode = "RGBA"

    masks: list[np.ndarray] = []
    h, w = render_args.resolution_y, render_args.resolution_x

    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx, target_obj in enumerate(placed_objects):
            # Hide every mesh in the scene except the target object
            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    obj.hide_render = obj.name != target_obj.name

            tmp_path = os.path.join(tmp_dir, f"mask_{idx}.png")
            render_args.filepath = tmp_path
            bpy.ops.render.render(write_still=True)

            # Load rendered image and extract alpha channel as a binary mask
            img = bpy.data.images.load(tmp_path)
            pixels = np.array(img.pixels[:]).reshape((h, w, 4))
            mask = (pixels[:, :, 3] > 0.5).astype(np.float32)
            masks.append(mask)
            bpy.data.images.remove(img)

    # Restore all render state
    for obj in bpy.data.objects:
        if obj.name in orig_hide_render:
            obj.hide_render = orig_hide_render[obj.name]
    render_args.engine = orig_engine
    render_args.film_transparent = orig_film_transparent
    render_args.image_settings.file_format = orig_file_format
    render_args.image_settings.color_mode = orig_color_mode
    render_args.filepath = orig_filepath

    return masks


def save_masks(
    masks: list[np.ndarray],
    placed_objects: list[bpy.types.Object],
    pov_index: int,
) -> None:
    """Save individual per-object masks and a combined mask to OUTPUT_MASKS_DIR_PATH.

    Files are named ``{pov_index:04d}_{object_name}.png`` for individual masks
    and ``{pov_index:04d}_all_objects.png`` for the combined (union) mask.
    """
    if not masks:
        return
    h, w = masks[0].shape

    def _write_mask(mask: np.ndarray, filepath: str) -> None:
        img = bpy.data.images.new("_tmp_mask_save", width=w, height=h)
        rgba = np.zeros((h, w, 4), dtype=np.float32)
        rgba[:, :, 0] = mask
        rgba[:, :, 1] = mask
        rgba[:, :, 2] = mask
        rgba[:, :, 3] = 1.0
        img.pixels[:] = rgba.flatten()
        img.filepath_raw = filepath
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)

    # Save individual object masks
    for mask, obj in zip(masks, placed_objects):
        path = str(OUTPUT_MASKS_DIR_PATH / f"{pov_index:04d}_{obj.name}.png")
        _write_mask(mask, path)

    # Save combined (union) mask
    combined = np.clip(np.sum(masks, axis=0), 0.0, 1.0)
    path = str(OUTPUT_MASKS_DIR_PATH / f"{pov_index:04d}_all_objects.png")
    _write_mask(combined, path)


def render_scene(object_placement_specs: list[ObjectPlacementSpec]) -> None:
    bpy.ops.wm.open_mainfile(filepath=str(BASE_SCENE_PATH))
    # Place objects in the scene according to the placement specifications
    placed_objects = place_objects(object_placement_specs)
    # Make sure all objects are visible and will be included in renders
    scene_collection = bpy.context.scene.collection
    for obj in placed_objects:
        obj.hide_render = False
        obj.hide_viewport = False
        if scene_collection.name not in (c.name for c in obj.users_collection):
            scene_collection.objects.link(obj)
    bbox_all_objects = compute_combined_bbox(placed_objects)
    # Setup camera
    camera = bpy.data.objects["Camera"]
    # Set FOV and resolution
    camera.data.angle = BLENDER_CAMERA_FOV_ANGLE_RADS
    render_args = bpy.context.scene.render
    render_args.resolution_x = IMG_RESOLUTION_X
    render_args.resolution_y = IMG_RESOLUTION_Y
    aspect_ratio = IMG_RESOLUTION_X / IMG_RESOLUTION_Y
    render_args.resolution_percentage = 100
    camera.rotation_mode = "XYZ"
    # Render for each POV
    for i in range(N_POVS):
        # Try to find a camera angle with no visual overlap between objects
        masks: list[np.ndarray] = []
        found_useable_angle = False
        for _attempt in range(MAX_CAMERA_ANGLE_SAMPLES):
            # Sample a camera angle to look down at the objects from
            tilt_min, tilt_max = 0.174, math.pi / 2
            tilt_mean = math.radians(45)
            tilt_std = math.radians(15)
            tilt = np.clip(np.random.normal(tilt_mean, tilt_std), tilt_min, tilt_max)
            pan = np.random.uniform(-math.pi, math.pi)
            min_distance = compute_min_camera_distance_to_capture_bbox(
                bbox=bbox_all_objects,
                camera_pitch=tilt,
                camera_tilt=pan,
                camera_fov_angle_rads=BLENDER_CAMERA_FOV_ANGLE_RADS,
                camera_aspect_ratio=aspect_ratio,
            )
            # Add a little bit of distance to the minimum distance
            distance = np.random.uniform(0.03, 0.15) * min_distance + min_distance
            # Camera points at bbox center; place it at center - distance * look_dir (Z-up)
            look_dir = convert_pitch_and_tilt_to_unit_vector(tilt, pan)
            camera.location = bbox_all_objects.center - distance * look_dir
            # Derive rotation from look_dir so camera actually faces the bbox center
            # Camera local -Z should align with look_dir, with world Z as up reference
            camera.rotation_euler = look_dir.to_track_quat("-Z", "Y").to_euler("XYZ")
            # Render per-object masks and check for visual overlap
            masks = render_object_masks(placed_objects)
            pov_has_object_overlap = bool(np.any(np.sum(masks, axis=0) > 1))
            if pov_has_object_overlap:
                continue
            found_useable_angle = True
            break

        if not found_useable_angle:
            raise ValueError(
                "Failed to sample a camera angle in which objects did not overlap "
                f"after {MAX_CAMERA_ANGLE_SAMPLES} attempts."
            )

        # Save per-object and combined masks
        save_masks(masks, placed_objects, i)

        # Render the scene: output path per POV, bounded retry
        output_image = OUTPUT_RENDERS_DIR_PATH / f"render_{i:04d}.png"
        render_args.filepath = str(output_image)
        for attempt in range(MAX_RENDER_ATTEMPTS):
            try:
                bpy.ops.render.render(write_still=True)
                break
            except Exception as e:
                print(f"Render attempt {attempt + 1}/{MAX_RENDER_ATTEMPTS} failed: {e}")
        else:
            print(f"Gave up after {MAX_RENDER_ATTEMPTS} render attempts for POV {i}.")


if __name__ == "__main__":
    with open(TEMP_JSON_PATH, "r") as f:
        obj_placement_specs = json.load(f)
    os.remove(TEMP_JSON_PATH)
    object_placement_specs = [ObjectPlacementSpec(**spec) for spec in obj_placement_specs]
    render_scene(object_placement_specs)
