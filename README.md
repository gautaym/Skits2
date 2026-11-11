# Skits2

A Unity 6 project for making short animated video skits, rendered on GitHub Actions.

## Environment check

`.github/workflows/unity-env-check.yml` starts an Ubuntu machine on GitHub, runs Unity
6000.0.85f1 (via the [GameCI](https://game.ci) Docker image) and checks the things a skit needs:

| Check | Why |
|---|---|
| Unity licence activation | Unity won't run without it |
| GPU / OpenGL under a virtual display | Rendering video frames headless |
| Timeline, Cinemachine, Recorder, TextMeshPro | Animating scenes, camera shots, captions |
| Render a 3s, 720x1280 two-character test scene to PNG | Proves frames actually render (not blank) |
| espeak-ng text-to-speech | Placeholder voice lines |
| ffmpeg: frames + voice → `skit_test.mp4` | Final video output |

Results show in the run's **Summary** tab; the MP4, report and logs are in the `skit-env-check` artifact.

### One-time setup: Unity secrets

Add these under **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|---|---|
| `UNITY_EMAIL` | Your Unity account email |
| `UNITY_PASSWORD` | Your Unity account password |
| `UNITY_LICENSE` | Full contents of your `Unity_lic.ulf` file (Personal licence) |
| `UNITY_SERIAL` | *Only for Plus/Pro* — use instead of `UNITY_LICENSE` |

To get `Unity_lic.ulf`: install Unity Hub on your computer, sign in and activate a free Personal
licence, then open the file:

- Windows: `C:\ProgramData\Unity\Unity_lic.ulf`
- macOS: `/Library/Application Support/Unity/Unity_lic.ulf`
- Linux: `~/.local/share/unity3d/Unity/Unity_lic.ulf`

Then run the workflow from **Actions → Unity skit environment check → Run workflow**.
