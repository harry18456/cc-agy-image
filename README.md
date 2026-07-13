English | [繁體中文](README.zh-TW.md)

# agy-image

Lets Claude Code generate and edit images with the **local `agy` CLI** (Antigravity / Gemini "Nano Banana") — fully local, **no API key**.
When you need a transparent background, a local `rembg` pass does semantic background removal, producing a PNG with a **real alpha channel** (agy itself only paints a fake checkerboard / white backdrop).

Once installed, natural-language requests trigger it — no commands to memorize:

- "Draw me a vertical event poster with the title '立即啟用'…"
- "Make an app icon, flat style"
- "Cut out this image's background, save as a transparent PNG"
- "Make a Lunar New Year greeting image styled after this mascot" (reference image)

Highlights:

- **Text posters in one shot**: titles, body copy, and button text are generated right inside the image; Chinese text works (verified with dense text layouts)
- **`--ref` reference images**: the output faithfully reproduces an existing mascot / product / logo design
- **`--transparent` true background removal**: rembg (u2net) semantic segmentation — no clean solid-color backdrop required

> ⚠️ **Windows only**. Driving agy headless requires ConPTY (pywinpty); a plain subprocess pipe simply hangs.

## Requirements

- Windows + Python 3
- `agy` CLI (Google Antigravity) installed and logged in, with `agy` on PATH
- Claude Code

## Installation

```
/plugin marketplace add harry18456/cc
/plugin install agy-image@harry18456
```

Restart Claude Code to take effect.

### Use locally right away (no push, no marketplace)

Junction the skill directory into the skills directory and the next session loads it:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\agy-image" -Target "<path to this repo>\skills\agy-image"
```

## First-use notes

- The first run auto-installs `pip install pywinpty pillow` (into whichever Python runs the script).
- The first **background removal** auto-installs `rembg + onnxruntime` and downloads a ~**176MB** u2net model into `~/.u2net/` — the first transparent image takes noticeably longer.
- Generating one image usually takes 1–3 minutes (agy's own speed) and outputs a PNG in the ~1024px class; resize afterwards if you need exact dimensions.

## How it works

One script does it all — `skills/agy-image/scripts/agy_image.py`:

1. Drives `agy` via ConPTY (pywinpty) — agy's print mode needs a real console.
2. Headless recipe: `--add-dir <output dir> --sandbox`, instructing agy to generate and save in one go — no plans, no waiting for confirmation.
3. agy often saves files into `~/.gemini/antigravity*/brain|scratch` instead of the requested path; the script identifies this run's actual outputs (excluding thumbnails and intermediates) and copies them to `--out`.
4. `--transparent` runs one more local rembg pass, outputting a true-alpha PNG.

Known behavior: agy almost always prints `Error: timed out waiting for response` at the end — **even on success**. Trust only the script's final `OK / FAILED` verdict.

## Security

- Prompts are always passed via temp files, never shell-interpolated (inject-safe).
- agy runs with `--sandbox`.
- Every call still goes through Claude Code's Bash permission prompt; it's recommended **not** to add `agy` or this script to an auto-approve allowlist, so every generation stays a deliberate action.

## Local development / testing

No need to push to GitHub first — load this folder directly:

```
claude --plugin-dir <path to this repo>
```

## License

MIT
