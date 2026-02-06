# MAVIS

Multi-view Action-to-Visual Image Synthesis

## Dev Notes:

- Launch scenes with `"/Applications/Blender.app/Contents/MacOS/Blender" test_output.blend`

### TODO

Next:
- Find best local inpainting/image editing model
- Inpaint plausible, but random-ish background
- Inpaint each object pose using action scene specs (pose only? maybe orientation too?)
- Generate batches of 4 POVs across a few interesting symmetrical composition configs and make canva/pdf of outputs to show people

Maybe:
- "Walk" the percentiles of the POV sampling distribution if POV diversity is important
- Soft "blacklist" regions in POV sampling distribution when object overlap is computed if efficiency is important