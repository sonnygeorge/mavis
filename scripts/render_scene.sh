#!/bin/bash
# Requires Blender in PATH, or set BLENDER_EXE to your Blender executable.
#
# Uses --background so Blender initializes with a valid scripting context. Output is saved
# to data/objaverse/test_placement_output.blend; open that file in Blender to view.
#
# Example (macOS): BLENDER_EXE="/Applications/Blender.app/Contents/MacOS/Blender" ./scripts/run_placement_test.sh

set -e
cd "$(dirname "$0")/.."
BLENDER="${BLENDER_EXE:-blender}"
"$BLENDER" --background data/objaverse/base_scene.blend --python src/mavis/render_scene.py
