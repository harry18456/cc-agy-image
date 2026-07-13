#!/usr/bin/env python
"""agy_image.py - one-shot headless image generation via `agy` (Antigravity / Nano Banana).

Everything needed to make agy produce an image from a non-interactive environment
(Claude Code, CI), folded into one entry point:

  1. Runs agy inside a ConPTY (pywinpty). Plain subprocess pipes HANG — agy's print
     mode needs a real console (verified). The ConPTY makes agy actually run.
  2. Uses the headless recipe: `--add-dir <workspace> --sandbox` + a prompt that tells
     agy to generate & save directly, with no plan / no confirmation gate (otherwise
     agy waits for a "Proceed" click that never comes and hangs).
  3. agy still tends to save into ~/.gemini/antigravity-cli/brain|scratch rather than
     your path, so we locate the freshest image it produced and copy it to --out.
  4. Optional --transparent runs rembg for a real alpha cut-out (neither agy nor codex
     make genuine alpha natively).

Deps (auto-installed if missing): pywinpty, pillow (+ rembg for --transparent).

Usage:
  python agy_image.py --out D:/proj/hero.png --prompt "a red apple on a white background"
  python agy_image.py --out ./sticker.png --prompt-file p.txt --transparent
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time

ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
AGY_OUT_DIRS = [
    "~/.gemini/antigravity/brain", "~/.gemini/antigravity/scratch",
    "~/.gemini/antigravity-cli/brain", "~/.gemini/antigravity-cli/scratch",
]
EXTS = (".png", ".jpg", ".jpeg", ".webp")
NO_PLAN = (
    # Force a single image-gen render. agy's DEFAULT for text-heavy posters is to
    # generate a base image then write a Pillow script to overlay the text — a
    # multi-step agent workflow that never finishes headless, leaving the text area
    # blank. Telling it to render everything (incl. all text) directly makes it do the
    # whole poster in one image-gen call, which it handles well (dense lists included).
    "請只用你的圖片生成功能、一次直接把完整成品畫出來（所有文字都要直接生成在圖片裡）；"
    "不要撰寫或執行任何 Python／程式腳本，也不要分成「先生底圖再疊字」兩步。"
    "請直接生成並存檔，不要列出計畫、不要詢問確認。"
)


def _strip_ansi(t):
    return ANSI_RE.sub("", t).replace("\r\n", "\n").replace("\r", "\n")


def run_agy_conpty(agy_args, max_wait):
    try:
        from winpty import PtyProcess
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pywinpty"], check=True)
        from winpty import PtyProcess

    proc = PtyProcess.spawn(["agy", *agy_args], dimensions=(50, 1000))
    chunks, start = [], time.time()
    while True:
        if time.time() - start > max_wait:
            try:
                proc.terminate(force=True)
            except Exception:
                pass
            chunks.append(f"\n[agy_image] killed: exceeded max-wait {max_wait}s\n")
            break
        try:
            chunk = proc.read()
        except EOFError:
            break
        if chunk == "":
            if not proc.isalive():
                break
            continue
        chunks.append(chunk)
    try:
        proc.wait()
    except Exception:
        pass
    return _strip_ansi("".join(chunks)), (getattr(proc, "exitstatus", 0) or 0)


THUMB_BYTES = 30000  # agy drops tiny thumbnails (~10 KB) in .tempmediaStorage
FILE_URL_RE = re.compile(r"file:///([A-Za-z]:[^\s)\]\"'<>]+|/[^\s)\]\"'<>]+)")


def _is_temp(path):
    return ".tempmediaStorage" in path.replace("\\", "/")


def newest_image(dirs, since, exclude_temp=True, min_bytes=0):
    # os.walk includes hidden dirs, but by default we SKIP `.tempmediaStorage/` — that
    # holds agy's intermediate/cache renders (the recurring no-text frame + thumbnails);
    # the real product is the NAMED file in the session root. Taking global max(mtime)
    # without this grabs the intermediate and reports OK on the wrong image.
    found = []
    for d in dirs:
        base = os.path.expanduser(d)
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            if exclude_temp and _is_temp(root):
                continue
            for f in files:
                if f.lower().endswith(EXTS):
                    p = os.path.join(root, f)
                    try:
                        if os.path.getmtime(p) >= since and os.path.getsize(p) >= min_bytes:
                            found.append(p)
                    except OSError:
                        pass
    return max(found, key=os.path.getmtime) if found else None


def _newest_in_dir(d, since):
    # session root only (non-recursive) → naturally skips the .tempmediaStorage subdir
    if not os.path.isdir(d):
        return None
    cands = []
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if f.lower().endswith(EXTS) and os.path.isfile(p):
            try:
                if os.path.getmtime(p) >= since and os.path.getsize(p) >= THUMB_BYTES:
                    cands.append(p)
            except OSError:
                pass
    return max(cands, key=os.path.getmtime) if cands else None


def locate_image(out, text, since, search_dirs):
    """Find agy's FINAL product, preferring the path agy itself reported and the named
    session-root file over a .tempmediaStorage intermediate or a tiny thumbnail."""
    # 1) the target path (agy honoured --add-dir + the save instruction this run)
    if os.path.exists(out) and os.path.getmtime(out) >= since:
        return out
    # 2) paths agy reported in its output (most reliable). It links the image directly,
    #    or a sibling `.md` viewer — in that case the real image sits in the same dir.
    for p in FILE_URL_RE.findall(text or ""):
        p = os.path.normpath(p.replace("%20", " "))
        if (p.lower().endswith(EXTS) and os.path.isfile(p) and not _is_temp(p)
                and os.path.getmtime(p) >= since and os.path.getsize(p) >= THUMB_BYTES):
            return p
        if p.lower().endswith(".md"):
            cand = _newest_in_dir(os.path.dirname(p), since)
            if cand:
                return cand
    # 3) dir scan for the named product (skip .tempmediaStorage intermediates + thumbnails)
    cand = newest_image(search_dirs, since, exclude_temp=True, min_bytes=THUMB_BYTES)
    if cand:
        return cand
    # 4) last resort: anything since `since` (don't false-FAIL if behaviour differs)
    return newest_image(search_dirs, since, exclude_temp=False, min_bytes=0)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt", help="image description")
    g.add_argument("--prompt-file", help="file containing the image description")
    ap.add_argument("--out", required=True, help="absolute output path, e.g. D:/proj/hero.png")
    ap.add_argument("--transparent", action="store_true", help="rembg cut-out -> real alpha PNG")
    ap.add_argument("--print-timeout", default="2m", help="agy --print-timeout (default 2m)")
    ap.add_argument("--max-wait", type=int, default=200, help="hard wall-clock cap per attempt (seconds)")
    ap.add_argument("--retries", type=int, default=1, help="extra attempts if agy yields no image (default 1)")
    ap.add_argument("--ref", help="reference image: agy is given read access to it and reproduces its subject faithfully")
    a = ap.parse_args()

    desc = a.prompt if a.prompt else open(a.prompt_file, encoding="utf-8").read()
    out = os.path.abspath(a.out)
    workspace = os.path.dirname(out) or "."
    os.makedirs(workspace, exist_ok=True)
    base = os.path.basename(out)

    # Reference image: agy reads files inside its workspace dirs, so grant read access to
    # the ref's OWN directory with an extra --add-dir (it's repeatable) and point agy at the
    # original path. No copy — copying into the output dir duplicated the ref (especially
    # when it already lived there) and risked being mis-collected as the result.
    ref_note, ref_dirs = "", []
    if a.ref:
        if not os.path.isfile(a.ref):
            print(f"FAILED: --ref not found: {a.ref}", file=sys.stderr)
            sys.exit(2)
        ref_abs = os.path.abspath(a.ref)
        ref_dir = os.path.dirname(ref_abs)
        if ref_dir != os.path.abspath(workspace):
            ref_dirs = ["--add-dir", ref_dir]
        ref_note = (
            f"請先讀取這張參考圖：{ref_abs} —— 圖中主體的造型/外觀，請在成品中忠實重現，不要改成別的東西。\n\n"
        )

    prompt = f"{ref_note}{desc.strip()}\n請在工作目錄存成 PNG：{base}。{NO_PLAN}"
    # Search agy's output dirs AND the workspace (agy may drop a .tempmediaStorage/ there).
    search_dirs = AGY_OUT_DIRS + [workspace]

    src = None
    for attempt in range(a.retries + 1):
        start = time.time()
        text, code = run_agy_conpty(
            ["--add-dir", workspace, *ref_dirs, "-p", prompt, "--sandbox", "--print-timeout", a.print_timeout],
            a.max_wait,
        )
        sys.stderr.write(
            f"[agy exit={code}, {round(time.time() - start)}s, attempt {attempt + 1}/{a.retries + 1}] "
            f"tail:\n{text[-400:]}\n"
        )
        # agy almost ALWAYS prints "Error: timed out waiting for response" even on
        # success — NOT a failure signal. Judge by the actual final product only.
        src = locate_image(out, text, start, search_dirs)
        if src:
            break
        sys.stderr.write(f"[attempt {attempt + 1}: no product image found — retrying]\n")

    if not src:
        print("FAILED: agy produced no image after all attempts. This is a genuine hang, "
              "NOT a scan miss — we checked the target, ~/.gemini/antigravity*/brain|scratch "
              "(incl. hidden .tempmediaStorage), and the workspace. Fall back to codex or run "
              "agy in a real terminal.", file=sys.stderr)
        sys.exit(1)
    if os.path.abspath(src) != os.path.abspath(out):
        shutil.copy(src, out)

    if a.transparent:
        try:
            from rembg import remove
            from PIL import Image
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "rembg", "onnxruntime", "pillow"], check=True)
            from rembg import remove
            from PIL import Image
        remove(Image.open(out).convert("RGBA")).save(out)

    from PIL import Image
    im = Image.open(out)
    print(f"OK {out}  {im.size}  {im.mode}  {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
