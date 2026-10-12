# novelai-skills

A [Claude Code](https://claude.com/claude-code) skill and a single-file Python SDK/CLI for **NovelAI image generation** (V5 / V4.5). Claude writes the prompt, generates, looks at the result and fixes it, all within the free Opus quota by default.

[中文说明](#中文说明)

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

**As a Claude Code plugin** (inside Claude Code):

```
/plugin marketplace add Tsukumi233/novelai-skills
/plugin install novelai@novelai-skills
```

**Or copy the skill manually:**

```bash
git clone https://github.com/Tsukumi233/novelai-skills
cp -r novelai-skills/skills/novelai ~/.claude/skills/
```

Then just ask Claude: *"draw Reimu and Marisa having tea on a snowy shrine porch"*.

## CLI usage (without Claude)

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

---

## 中文说明

给 Claude Code 用的 NovelAI 生图 skill，附带单文件 Python SDK/CLI。支持文生图、图生图、局部重绘、多角色分槽（位置 + 互动）、读取 PNG 元数据并复现、风格预设、余额查询、tag 联想。默认只在 Opus 免费额度内生成，花 Anlas 的操作需要显式 `--allow-paid`。

**安装**：在 Claude Code 里执行 `/plugin marketplace add Tsukumi233/novelai-skills` 和 `/plugin install novelai@novelai-skills`，或者把 `skills/novelai` 复制到 `~/.claude/skills/`。

**准备**：安装 [uv](https://docs.astral.sh/uv/)，并把 NovelAI 持久 API Token 设为环境变量 `NOVELAI_API_KEY`。

然后直接对 Claude 说「画灵梦和魔理沙在下雪的神社檐廊喝茶」就行。

许可证：AGPL-3.0。修改后分发或做成网络服务都必须以相同许可证开源。非官方项目，与 Anlatan / NovelAI 无关。
