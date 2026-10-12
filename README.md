# novelai-skills

An [Agent Skill](https://agentskills.io) for Claude Code, OpenCode, oh-my-pi (omp) and other SKILL.md-compatible agents, plus a single-file Python SDK/CLI for **NovelAI image generation** (V5 / V4.5). The agent writes the prompt, generates, looks at the result and fixes it, all within the free Opus quota by default.

English | [简体中文](README.zh-CN.md)

## Features

- txt2img, img2img, inpainting (masks snapped to the latent grid; V5 Curated falls back to V5 Full inpainting)
- Multi-character scenes: per-character prompts, positions, `source#/target#/mutual#` interactions
- Read NovelAI PNG metadata (text chunks + stealth alpha) and **reproduce** an image from it
- Style presets (`painterly`, `graphic`); add your own in `styles/*.json`
- Anlas / Opus meter balance, tag suggestions, model capabilities, upscale and director tools
- A free-quota guard: refuses anything that costs Anlas unless you pass `--allow-paid`
- Prompting guides tested on V5 (`references/`)

## Requirements

- A NovelAI subscription (Opus for free generations) and a **persistent API token** (NovelAI → Account Settings → Get Persistent API Token)
- [uv](https://docs.astral.sh/uv/) (the script declares its own dependencies; only Pillow)
- Python ≥ 3.10

Set the token as an environment variable:

```bash
# macOS / Linux
export NOVELAI_API_KEY="pst-..."
```

```powershell
# Windows (persistent)
setx NOVELAI_API_KEY "pst-..."
```

## Install

The skill is the folder `skills/novelai` (a standard `SKILL.md` skill). Put it where your agent looks for skills.

**Any agent (shared location, recommended)** — read by OpenCode and omp; Claude Code needs its own path below:

```bash
git clone https://github.com/Tsukumi233/novelai-skills
mkdir -p ~/.agents/skills
cp -r novelai-skills/skills/novelai ~/.agents/skills/
```

Use `ln -s` (or a Windows junction) instead of `cp` if you want `git pull` to update it.

| Agent | Global skill directory |
|---|---|
| Claude Code | `~/.claude/skills/novelai` (or the plugin, below) |
| OpenCode | `~/.agents/skills/`, `~/.claude/skills/` or `~/.config/opencode/skills/` |
| oh-my-pi (omp) | `~/.omp/agent/skills/` (also reads `~/.agents/skills/`; if not, check `enabledProviders`) |
| Others | wherever they load `<name>/SKILL.md` skills from |

**With the [`skills`](https://github.com/vercel-labs/skills) installer** (picks the right folder per agent):

```bash
npx skills add Tsukumi233/novelai-skills
```

**As a Claude Code plugin** (inside Claude Code):

```
/plugin marketplace add Tsukumi233/novelai-skills
/plugin install novelai@novelai-skills
```

Then just ask your agent: *"draw Reimu and Marisa having tea on a snowy shrine porch"*. The agent needs to be able to run shell commands and, ideally, view images (to check results).

## CLI usage (without an agent)

```bash
NAI="uv run --script skills/novelai/scripts/nai.py"
$NAI gen -p "1girl, hakurei reimu, shrine, snow" -o out --name reimu
$NAI gen spec.json                  # JSON spec, see SKILL.md
$NAI gen --style painterly -p "..."
$NAI meta image.png --spec > spec.json && $NAI gen spec.json   # reproduce
$NAI balance
$NAI tags "remilia"
```

As a library:

```python
import sys; sys.path.insert(0, "skills/novelai/scripts")
import nai
nai.generate({"prompt": "1girl, ...", "chars": [{"prompt": "...", "pos": [0.3, 0.5]}], "out": "."})
```

## Notes

- NovelAI allows one concurrent generation per account; the script serializes and retries on 429.
- Generations should be user-initiated (NovelAI ToS). Don't run unattended loops.
- This is an unofficial project, not affiliated with Anlatan / NovelAI.

## License

[AGPL-3.0](LICENSE). If you modify it and distribute it, or offer it as a network service (website, bot, API), you must release your source under the same license.
