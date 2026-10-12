---
name: novelai
description: Generate and edit anime images with NovelAI (V5 / V4.5) through a local SDK + CLI — txt2img, multi-character scenes with per-character prompts and positions, img2img, inpainting, reading NovelAI PNG metadata and reproducing an image from it, Anlas / Opus-meter balance, tag suggestions, upscale and director tools. Use whenever the user asks to draw, generate, redraw, fix or reproduce a NovelAI image, asks how an image was made (prompt/params), or wants prompt help for NovelAI.
license: AGPL-3.0-only
compatibility: Needs uv, Python >= 3.10, network access to NovelAI and the NOVELAI_API_KEY environment variable.
---

# NovelAI

All calls go through one script (SDK + CLI). It needs `NOVELAI_API_KEY` (a persistent API token from NovelAI → Account Settings) and [uv](https://docs.astral.sh/uv/). `<SKILL_DIR>` below is the directory containing this SKILL.md (usually `~/.agents/skills/novelai`, `~/.claude/skills/novelai`, `~/.config/opencode/skills/novelai` or `~/.omp/agent/skills/novelai`). If `NOVELAI_API_KEY` is missing, ask the user to set it; never ask them to paste the token into the chat.

```
NAI = uv run --script <SKILL_DIR>/scripts/nai.py
$NAI gen SPEC.json [more.json] [flags]   # generate; prints one JSON line per image: {"path","seed",...}
$NAI gen -p "..." -c "char prompt@x,y" -c "..." --size landscape -o OUTDIR --name NAME
$NAI gen --style painterly -p "..."      # style preset = params + negative bundle (styles/*.json)
$NAI gen ... --dry-run                   # print the request body, send nothing
$NAI styles                              # list style presets
$NAI meta IMAGE [--spec]                 # read metadata; --spec = spec that re-sends the same request
$NAI balance                             # Anlas + Opus free-generation meter
$NAI tags "remilia"                      # tag suggestions (exact Danbooru names)
$NAI caps [model]                        # presets and capabilities per model
$NAI upscale IMAGE --allow-paid          # costs Anlas: ask first
$NAI augment lineart|sketch|colorize|emotion|declutter|bg-removal IMAGE --allow-paid
```

From Python (other skills/scripts): `sys.path.insert(0, "<SKILL_DIR>/scripts"); import nai; nai.generate(spec)`, `nai.read_meta(path)`, `nai.spec_from_meta(path)`.

## Rules

- **Free quota.** The defaults stay within the Opus free tier: ≤ 1024×1024 pixels (832×1216 / 1216×832 / 1024×1024), ≤ 28 steps, one image per request. The script refuses anything else, and also vibe transfer and character reference, unless `--allow-paid` / `allow_paid=True`. Only pass it after the user agrees to spend Anlas in this conversation. `balance` shows the Opus meter (`percent_left`, about 17 images per percent); mention it if it gets low (< 5 %).
- **Never put `nsfw` in negative prompts.**
- **One generation at a time.** NovelAI allows one concurrent generation per account; the script serializes and retries 429s. Generations must be user-initiated (NovelAI ToS): generate what was asked, not open-ended loops.
- **Save where the user works.** Pass `-o` (or `"out"`) = the current project folder (normally the working directory). Files are `NAME_YYYYmmdd_HHMMSS_SEED.png` with NovelAI metadata intact.
- **Look at every result** (open the PNG with your image-viewing / file-reading tool) before reporting. If you cannot view images, say so and ask the user to check. Check each character (identity anchors, count, nobody missing, duplicated or merged with an extra), each requested action and interaction direction, hands and faces, and that the setting looks like the requested place. Report honestly what V5 got right and wrong; link the files; give seeds.

## Spec (JSON)

Write specs to files for anything non-trivial (easier to edit and rerun). A file may hold one spec, a list, or `{"defaults": {...}, "jobs": [{...}, ...]}`. (The `//` comments below are explanations; real JSON can't contain them.)

```json
{
  "prompt": "artist:..., year 2024, 3girls, touhou, scene, lighting, palette, mood",
  "negative": "extra negatives (UC preset is prepended automatically)",
  "chars": [
    {"prompt": "kochiya sanae, green hair, ..., source#pulling by the hand", "negative": "maid", "pos": [0.3, 0.5]},
    {"prompt": "yasaka kanako, ..., target#pulling by the hand", "pos": [0.5, 0.5]}
  ],
  "model": "v5-full",          // v5-full | v5-curated | v4.5-full | v4.5-curated | full API name
  "size": "landscape",         // portrait 832x1216 | landscape 1216x832 | square 1024x1024 | [w, h]
  "steps": 28, "scale": 7, "seed": null,
  "quality": "standard",       // standard | light (V5) | none   -> appended quality tags
  "uc": "heavy",               // heavy | light | humanFocus | furryFocus | none -> prepended negative preset
  "out": ".", "name": "scene"
}
```

`"style": "painterly"` loads `styles/painterly.json` as a layer under the spec: its params become defaults, its `negative` is prepended to yours and its `prefix`/`suffix` wrap your prompt. Presets: `painterly` (V5 Curated, CFG 6, no presets, the reference images' long negative incl. negative artists) and `graphic` (V5 Full, CFG 5.6, standard presets, poster suffix). Add a new style file when a recipe proves itself.

Other keys: `transparent` (V5), `variety` (V4/V4.5 Variety Boost), `cfg_rescale`, `sampler`, `noise_schedule`, `i2i: {"image", "strength", "noise"}`, `mask` (with `i2i` → inpaint), `vibes: [{"image","strength","info"}]` (V4/V4.5), `charref: {"image","mode":"character&style","strength","fidelity"}` (V4.5), `prefer_brownian`, `ancestral_bug`, `neg_use_order`, and `extra: {raw API param: value}` (`null` removes a param). CLI `--set key=json` overrides any key, e.g. `--set seed=123 --set model='"v5-curated"'`.

Defaults follow the web client: V5 Full, 832×1216, 28 steps, CFG 7 (V5 web default; V4.x default 5), quality `standard`, UC `heavy`, k_euler_ancestral / karras.

## Writing prompts

Before writing prompts for a new kind of scene in a session, read:

- `references/prompt-patterns.md`: the prompt design distilled from well-made reference images. It covers transferable principles (account for both hands, placement in words, 3-colour palette, light that lands somewhere, guard phrases, group geometry), fill-in skeletons for each style preset, and phrase banks.
- `references/prompting.md`: tested specifics. It covers artist/year tags, the two multi-character methods (per-character slots vs. long-form `| girl,` captions), V5's known failure modes and their fixes, and Curated vs Full.

Append new findings (what worked, what failed) to the test log or tables in these files.

## Common tasks

- **Multi-character scene**: per-character `chars` with positions, NPCs in their own slot, `source#/target#` interactions (see prompting.md).
- **Fix a small defect** (a hand, an object): paint a white-on-black mask the size of the image over the area (PIL), then `gen` with the same prompt/chars plus the change, `--i2i ORIGINAL --mask MASK`. Strength defaults to 1.0 for inpainting. The mask is grown to the 8-px latent grid automatically (partial cells leave seams). V5 Curated has no inpainting model; the script falls back to V5 Full inpainting, which blends seamlessly into Curated images (tested on a sock trim).
- **Variation of a good image**: same spec with a new seed, or img2img `--i2i IMG --strength 0.4-0.6`.
- **"How was this made?" / reproduce**: `meta IMAGE` shows the stored prompt and params (text chunks may be after the image data; the script handles that and stealth alpha metadata). `meta IMAGE --spec > spec.json` then `gen spec.json` re-sends the identical request. Model hashes: `0ADF9AB7` = V5 Full, `DB276663` = V5 Curated. Images whose Software is a third-party client (e.g. "Plana") may have been post-processed and will not match pixel-for-pixel even with identical params.
- **Exact tag names**: `tags "partial name"`.

## Capabilities (from the web client)

| | V5 Full / Curated | V4.5 Full / Curated |
|---|---|---|
| char slots | 32, free positions | 6, 5×5 grid |
| vibe transfer / character reference | no | yes (paid) |
| Variety Boost | no | yes |
| transparent background | yes | no |
| quality presets | standard, light | standard |

On V5, `prefer_brownian` and `deliberate_euler_ancestral_bug` have no effect (verified: identical pixels).
