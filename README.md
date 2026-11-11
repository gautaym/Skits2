# Skits2

Short animated video skits made with [Blender](https://www.blender.org) (free, no licence needed),
rendered headless on GitHub Actions.

## Environment check

`.github/workflows/blender-env-check.yml` runs on every push to `main` (or manually from
**Actions → Blender skit environment check → Run workflow**). It installs Blender 4.5 LTS on an
Ubuntu runner and checks everything a skit needs:

| Check | Why |
|---|---|
| Blender runs headless | Render without a screen |
| OpenGL on a virtual display | EEVEE / Workbench (fast engines) |
| Build a scene from Python: meshes, materials, 3D text, keyframes | Script whole skits |
| Render stills with EEVEE, Cycles (CPU) and Workbench | See which engines work and how fast |
| espeak-ng text-to-speech | Placeholder voice lines |
| Render a 3s 720x1280 two-character clip with voice to MP4 | Final Shorts-format output |
| FBX / glTF importers | Bring in ready-made characters (e.g. Mixamo) |

Results show in the run's **Summary** tab; the MP4, stills and report are in the
`skit-env-check` artifact.

### Run locally

```bash
blender -b --factory-startup --python ci/blender_check.py -- --out Output --engines Cycles
# or, with the bpy package (Python 3.11):  pip install bpy==4.5.16
python ci/blender_check.py --out Output --engines Cycles
```
