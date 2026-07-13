---
name: agy-image
description: >-
  Generate or edit raster images locally by driving the installed `agy` CLI
  (Antigravity / Gemini "Nano Banana") — fully local, no API key — and deliver true
  transparent backgrounds via local `rembg`. Use this whenever the user wants to
  create, generate, draw, design, or make an image, picture, illustration, icon, logo,
  avatar, sticker, cut-out, banner, thumbnail, concept art, or wallpaper, or to edit /
  restyle / cut out / remove the background of an existing image. Triggers on casual
  phrasings too: "幫我畫一張…", "生成一張…的圖", "做張圖", "畫個 icon",
  "去背 / 透明背景 / 做成貼圖", "把這張圖改成…", "make me an image of…",
  "cut out / transparent png". Fire even when the user never names a tool — if the
  deliverable is an image file, this is how.
---

# agy-image — you write the prompt, agy renders the image

Drive the local `agy` CLI (Gemini "Nano Banana") to generate or edit images — fully
local, no API key. **Your only job is to write one complete prompt; agy produces the
finished image**, including any text, headings, and layout (it renders text and full
multi-block posters correctly — verified). The one thing agy can't do is a *real*
transparent background, so `--transparent` adds a local `rembg` cut-out afterwards.

## Preflight
```bash
command -v agy >/dev/null && echo HAVE_AGY || echo NO_AGY
```
agy present → continue. Absent → stop and tell the user: "agy-image needs the `agy` CLI
installed."

## Generate

1. **Write the whole image description to a temp file** (`<tmp>/img-prompt.txt`) with
   your file tool — never inline it into the shell. Describe *everything* you want in
   the picture: subject, the exact words / headings and where each goes, colours,
   layout, orientation. It all goes in this one prompt — agy renders the text and
   layout itself.
2. **Run the bundled script** (it owns the rest: ConPTY, the headless recipe, one
   auto-retry, and locating the file agy saved):
   ```bash
   python "<skill-dir>/scripts/agy_image.py" --out "<absolute.png>" --prompt-file "<tmp>/img-prompt.txt"
   # add --transparent for a true alpha cut-out (runs rembg)
   # add --ref <image> to make the subject match an existing image (a mascot / product / logo)
   ```
   Call it with Bash `timeout: 480000`. `pywinpty` auto-installs on first run.
3. **Trust the verdict, not the noise.** Success → it prints `OK <path> <size> <mode>`.
   agy nearly always prints `Error: timed out waiting for response` in its tail even
   when it succeeded — ignore that; the file on disk is the truth. Real failure →
   `FAILED` (it already retried and scanned every place agy saves). On `FAILED`, retry
   the whole call **at most once**, then have the user run agy in a real terminal.
4. **Verify**: `Read` the file; for text, check the spelling.

## Notes
- Output is ~1024-ish PNG; orientation follows your prompt. No exact pixel size —
  resize the finished file yourself if one is required.
- Edit / reference an existing image: name its absolute path inside the prompt, or pass
  `--ref <image>` (the script copies it into agy's workspace and tells agy to reproduce
  its subject faithfully — verified).
- This skill's job is **prompt → image**, nothing more. If a result doesn't fit the
  need, decide what to do *then*, looking at the actual output — don't bake fallbacks
  (overlays, density rules, etc.) into the skill.
- Security: the prompt goes through a temp file (inject-safe), agy runs `--sandbox`,
  and every call still hits your normal Bash permission prompt — keep `agy` off any
  auto-approve allowlist so each run is deliberate.

## Example — full poster, all in one prompt
> 做一張直式色彩學講座海報

`<tmp>/img-prompt.txt`:
`直式宣傳海報。上方置中一張 24 格標準色卡（ColorChecker：6×4 圓角方格、最下排是白到黑的六階灰階、其餘為紅綠藍黃橘與膚色等色塊、深灰色邊框）。中間用深灰色粗體大字寫「色彩學入門講座」，下方小字「7/26 14:00・線上直播」，最下方一個橘色圓角按鈕寫「立即報名」。米白色簡約背景，現代設計，文字務必拼寫正確、清楚。`
```bash
python "<skill-dir>/scripts/agy_image.py" --out "./color-poster.png" --prompt-file "<tmp>/img-prompt.txt"
```

To match a mascot/product, add `--ref`:
```bash
python "<skill-dir>/scripts/agy_image.py" --out "./color-poster.png" --prompt-file "<tmp>/img-prompt.txt" --ref "D:/assets/mascot.png"
```
