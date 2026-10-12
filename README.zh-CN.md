# novelai-skills

[English](README.md) | 简体中文

一个 **NovelAI 生图**（V5 / V4.5）的 [Agent Skill](https://agentskills.io)，适用于 Claude Code、OpenCode、oh-my-pi (omp) 以及其他支持 SKILL.md 的 agent，附带单文件 Python SDK/CLI。agent 会自己写 prompt、生成、查看结果并修正，默认全程只用 Opus 免费额度。

## 功能

- 文生图、图生图、局部重绘（蒙版自动对齐 latent 网格；V5 Curated 没有重绘模型时自动改用 V5 Full 重绘）
- 多角色场景：每个角色单独的 prompt、位置，以及 `source#/target#/mutual#` 互动
- 读取 NovelAI PNG 元数据（文本块 + 隐写 alpha），并按元数据**复现**图片
- 风格预设（`painterly`、`graphic`），可在 `styles/*.json` 里添加自己的
- 查询 Anlas / Opus 额度、tag 联想、模型能力、放大和 Director 工具
- 免费额度保护：任何会消耗 Anlas 的请求都会被拒绝，除非显式传 `--allow-paid`
- 在 V5 上实测过的 prompt 写法指南（`references/`）

## 准备

- NovelAI 订阅（免费生成需要 Opus）和一个**持久 API Token**（NovelAI → Account Settings → Get Persistent API Token）
- [uv](https://docs.astral.sh/uv/)（脚本自带依赖声明，只依赖 Pillow）
- Python ≥ 3.10

把 Token 设为环境变量：

```bash
# macOS / Linux
export NOVELAI_API_KEY="pst-..."
```

```powershell
# Windows（永久）
setx NOVELAI_API_KEY "pst-..."
```

## 安装

skill 就是 `skills/novelai` 这个文件夹（标准 `SKILL.md` 格式），放到你的 agent 读取 skill 的目录即可。

**通用位置（推荐）**：OpenCode 和 omp 都会读取；Claude Code 的路径见下表。

```bash
git clone https://github.com/Tsukumi233/novelai-skills
mkdir -p ~/.agents/skills
cp -r novelai-skills/skills/novelai ~/.agents/skills/
```

想用 `git pull` 更新的话，把 `cp` 换成 `ln -s`（Windows 用目录联接 junction）。

| Agent | 全局 skill 目录 |
|---|---|
| Claude Code | `~/.claude/skills/novelai`（或用下面的插件方式） |
| OpenCode | `~/.agents/skills/`、`~/.claude/skills/` 或 `~/.config/opencode/skills/` |
| oh-my-pi (omp) | `~/.omp/agent/skills/`（也会读 `~/.agents/skills/`；读不到时检查 `enabledProviders` 设置） |
| 其他 | 它们读取 `<name>/SKILL.md` 的目录 |

**用 [`skills`](https://github.com/vercel-labs/skills) 安装器**（自动为各 agent 选择目录）：

```bash
npx skills add Tsukumi233/novelai-skills
```

**作为 Claude Code 插件**（在 Claude Code 里执行）：

```
/plugin marketplace add Tsukumi233/novelai-skills
/plugin install novelai@novelai-skills
```

然后直接对 agent 说「画灵梦和魔理沙在下雪的神社檐廊喝茶」就行。agent 需要能执行 shell 命令，最好还能查看图片（用来检查结果）。

## 命令行用法（不通过 agent）

```bash
NAI="uv run --script skills/novelai/scripts/nai.py"
$NAI gen -p "1girl, hakurei reimu, shrine, snow" -o out --name reimu
$NAI gen spec.json                  # JSON spec，格式见 SKILL.md
$NAI gen --style painterly -p "..."
$NAI meta image.png --spec > spec.json && $NAI gen spec.json   # 复现
$NAI balance
$NAI tags "remilia"
```

作为库调用：

```python
import sys; sys.path.insert(0, "skills/novelai/scripts")
import nai
nai.generate({"prompt": "1girl, ...", "chars": [{"prompt": "...", "pos": [0.3, 0.5]}], "out": "."})
```

## 注意

- NovelAI 每个账号同时只能进行一个生成；脚本会排队，遇到 429 自动重试。
- 生成应由用户发起（NovelAI 服务条款），不要无人值守地循环生成。
- 本项目为非官方项目，与 Anlatan / NovelAI 无关。

## 许可证

[AGPL-3.0](LICENSE)。修改后分发，或做成网络服务（网站、bot、API）提供给他人使用，都必须以相同许可证公开源码。
