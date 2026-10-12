# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Tsukumi233
"""NovelAI image SDK and CLI.

Request shapes follow https://image.novelai.net/docs/doc.json; defaults, presets and
per-model capabilities mirror the novelai.net web client (checked 2026-10-11).

CLI (run with `uv run --script nai.py ...`):
    gen      [SPEC.json ...] [flags]   generate (txt2img / img2img / inpaint)
    meta     IMAGE [--spec]            read NovelAI metadata; --spec prints a reproducing spec
    balance                            Anlas, Opus usage meter
    tags     QUERY                     tag suggestions
    caps     [MODEL]                   model capabilities and presets
    styles                             list style presets (styles/*.json; use with gen --style NAME)
    upscale  IMAGE --allow-paid
    augment  TOOL IMAGE --allow-paid   director tools (lineart, sketch, colorize, emotion, declutter, bg-removal)

Library:
    import nai
    results = nai.generate({"prompt": "...", "chars": [...], "out": "."})
    results = nai.generate({"style": "painterly", "prompt": "..."})
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import copy
import gzip
import hashlib
import io
import json
import os
import random
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image

IMAGE_API = "https://image.novelai.net"
USER_AGENT = "nai-skill/1.0"

# ---------------------------------------------------------------------------
# Models, presets, capabilities (from the web client)
# ---------------------------------------------------------------------------

MODEL_ALIASES = {
    "v5": "nai-diffusion-5-full",
    "v5-full": "nai-diffusion-5-full",
    "v5-curated": "nai-diffusion-5-curated",
    "v4.5": "nai-diffusion-4-5-full",
    "v4.5-full": "nai-diffusion-4-5-full",
    "v4.5-curated": "nai-diffusion-4-5-curated",
    "v4": "nai-diffusion-4-full",
    "v4-full": "nai-diffusion-4-full",
    "v4-curated": "nai-diffusion-4-curated-preview",
}

# Model hash in the PNG "Source" field -> API model name (observed).
MODEL_HASHES = {
    "0ADF9AB7": "nai-diffusion-5-full",
    "DB276663": "nai-diffusion-5-curated",
    "657484A5": "nai-diffusion-5-full",  # V5 Full inpainting output; respec as the base model
}

_V5_UC = {
    "heavy": "lowres, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, "
    "very displeasing, chromatic aberration, dithering, halftone, screentone, multiple views, logo, "
    "too many watermarks, negative space, blank page",
    "light": "lowres, bad hands, bad anatomy, artistic error, sepia, white haze, worst quality, very displeasing, "
    "jpeg artifacts, 0::ai-generated::",
    "furryFocus": "{worst quality}, distracting watermark, unfinished, bad quality, {widescreen}, upscale, {sequence}, "
    "{{grandfathered content}}, blurred foreground, chromatic aberration, sketch, everyone, [sketch background], "
    "simple, [flat colors], ych (character), outline, multiple scenes, [[horror (theme)]], comic",
    "humanFocus": "lowres, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, "
    "very displeasing, chromatic aberration, dithering, halftone, screentone, multiple views, logo, "
    "too many watermarks, negative space, blank page, @_@, mismatched pupils, glowing eyes, bad anatomy",
}
_V45F_UC = dict(_V5_UC, light="lowres, artistic error, scan artifacts, worst quality, bad quality, jpeg artifacts, "
                "multiple views, very displeasing, too many watermarks, negative space, blank page")
_V45C_UC = {
    "heavy": "blurry, lowres, upscaled, artistic error, film grain, scan artifacts, worst quality, bad quality, "
    "jpeg artifacts, very displeasing, chromatic aberration, halftone, multiple views, logo, too many watermarks, "
    "negative space, blank page",
    "light": "blurry, lowres, upscaled, artistic error, scan artifacts, jpeg artifacts, logo, too many watermarks, "
    "negative space, blank page",
    "humanFocus": "blurry, lowres, upscaled, artistic error, film grain, scan artifacts, bad anatomy, bad hands, "
    "worst quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, halftone, multiple views, "
    "logo, too many watermarks, @_@, mismatched pupils, glowing eyes, negative space, blank page",
}
_V4F_UC = {
    "heavy": "blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, "
    "very displeasing, chromatic aberration, multiple views, logo, too many watermarks, white blank page, blank page",
    "light": "blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very displeasing, white blank page, "
    "blank page",
}
_V4C_UC = {
    "heavy": "blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, "
    "very displeasing, chromatic aberration, logo, dated, signature, multiple views, gigantic breasts, "
    "white blank page, blank page",
    "light": "blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very displeasing, logo, dated, "
    "signature, white blank page, blank page",
}

# Each model: quality presets (suffix), UC presets (prefix), capabilities.
MODELS: dict[str, dict[str, Any]] = {
    "nai-diffusion-5-full": {
        "quality": {"standard": "very aesthetic, masterpiece, no text", "light": "very aesthetic, amazing quality, no text"},
        "uc": _V5_UC, "max_chars": 32, "freeform_pos": True, "vibe": False, "charref": False,
        "variety_sigma": None, "transparency": True, "web_scale": 7,
    },
    "nai-diffusion-4-5-full": {
        "quality": {"standard": "very aesthetic, masterpiece, no text"},
        "uc": _V45F_UC, "max_chars": 6, "freeform_pos": False, "vibe": True, "charref": True,
        "variety_sigma": 58, "transparency": False, "web_scale": 5,
    },
    "nai-diffusion-4-5-curated": {
        "quality": {"standard": "very aesthetic, masterpiece, no text, -0.8::feet::, rating:general"},
        "uc": _V45C_UC, "max_chars": 6, "freeform_pos": False, "vibe": True, "charref": True,
        "variety_sigma": 58, "transparency": False, "web_scale": 5,
    },
    "nai-diffusion-4-full": {
        "quality": {"standard": "no text, best quality, very aesthetic, absurdres"},
        "uc": _V4F_UC, "max_chars": 6, "freeform_pos": False, "vibe": True, "charref": False,
        "variety_sigma": 19, "transparency": False, "web_scale": 5,
    },
    "nai-diffusion-4-curated-preview": {
        "quality": {"standard": "rating:general, best quality, very aesthetic, absurdres"},
        "uc": _V4C_UC, "max_chars": 6, "freeform_pos": False, "vibe": True, "charref": False,
        "variety_sigma": 19, "transparency": False, "web_scale": 5,
    },
}
MODELS["nai-diffusion-5-curated"] = MODELS["nai-diffusion-5-full"]

UC_ALIASES = {"strong": "heavy", "human": "humanFocus", "human_focus": "humanFocus",
              "furry": "furryFocus", "furry_focus": "furryFocus"}
# Web client id -> integer used by tag_hint_qt / tag_hint_uc_preset.
TAG_HINT = {"none": 0, "standard": 1, "heavy": 2, "light": 3, "humanFocus": 4, "furryFocus": 5}

SIZES = {
    "portrait": (832, 1216), "landscape": (1216, 832), "square": (1024, 1024),
    "portrait_small": (512, 768), "landscape_small": (768, 512), "square_small": (640, 640),
    "wallpaper": (1920, 1088),
}
STYLE_DIR = Path(__file__).resolve().parent.parent / "styles"
FREE_MAX_PIXELS = 1024 * 1024
FREE_MAX_STEPS = 28

DEFAULTS: dict[str, Any] = {
    "model": "nai-diffusion-5-full",
    "size": "portrait",
    "steps": 28,
    "scale": None,  # None -> web default for the model
    "seed": None,
    "n": 1,
    "quality": "standard",
    "uc": "heavy",
    "sampler": "k_euler_ancestral",
    "noise_schedule": "karras",
    "cfg_rescale": 0.0,
    "variety": False,
    "prefer_brownian": True,
    "ancestral_bug": False,
    "neg_use_order": False,
    "transparent": False,
    "negative": "",
    "chars": [],
    "out": ".",
    "name": "nai",
}


class NAIError(Exception):
    pass


def resolve_model(name: str) -> str:
    m = MODEL_ALIASES.get(name.lower(), name)
    if m.endswith("-inpainting"):
        m = m[: -len("-inpainting")]
    return m


def model_info(model: str) -> dict[str, Any]:
    if model not in MODELS:
        raise NAIError(f"Unknown model '{model}'. Known: {', '.join(MODELS)} (aliases: {', '.join(MODEL_ALIASES)})")
    return MODELS[model]


def join(*parts: str) -> str:
    return ", ".join(p.strip().strip(",").strip() for p in parts if p and p.strip().strip(",").strip())


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.environ.get("NOVELAI_API_KEY") or os.environ.get("NAI_API_KEY")
    if not key:
        raise NAIError("Set NOVELAI_API_KEY (a persistent API token from NovelAI account settings).")
    return key.strip()


@contextlib.contextmanager
def _account_lock(timeout: float = 900.0):
    """NovelAI runs one generation per account at a time; serialize across processes."""
    path = Path(tempfile.gettempdir()) / "nai-skill.lock"
    fh = open(path, "a+b")
    start = time.time()
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() - start > timeout:
                    raise NAIError("Timed out waiting for another nai.py generation to finish.")
                time.sleep(0.5)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()


def request(method: str, url: str, body: dict | None = None, query: dict | None = None,
            timeout: float = 180.0, retries: int = 6) -> tuple[bytes, str]:
    """Send a request; retry on 429 (concurrent lock / rate limit) and 5xx. Returns (body, content-type)."""
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {_api_key()}", "User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    delay = 2.0
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            try:
                text = json.loads(text).get("message", text)
            except Exception:
                pass
            if (e.code == 429 or e.code >= 500) and attempt < retries:
                print(f"[nai] HTTP {e.code} ({text}); retry in {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            raise NAIError(f"HTTP {e.code} from {urllib.parse.urlparse(url).path}: {text}") from None
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(delay)
                continue
            raise NAIError(f"Network error: {e.reason}") from None
    raise NAIError("unreachable")


def images_from_response(data: bytes) -> list[bytes]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"RIFF":
        return [data]
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return [z.read(n) for n in sorted(z.namelist()) if n.lower().endswith((".png", ".webp", ".jpg"))]
    except zipfile.BadZipFile:
        raise NAIError(f"Unexpected response: {data[:200]!r}") from None


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _load(path: str | Path) -> Image.Image:
    im = Image.open(path)
    im.load()
    return im


def _b64png(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _fit(im: Image.Image, w: int, h: int, mask: bool = False) -> Image.Image:
    if im.size == (w, h):
        return im
    return im.resize((w, h), Image.Resampling.NEAREST if mask else Image.Resampling.LANCZOS)


def _pad_charref(im: Image.Image, transparent: bool = False) -> Image.Image:
    """Character reference images must be 1024x1536, 1536x1024 or 1472x1472, padded to fit."""
    w, h = im.size
    tw, th = (1536, 1024) if w > h * 1.2 else (1024, 1536) if h > w * 1.2 else (1472, 1472)
    k = min(tw / w, th / h)
    rim = im.convert("RGBA").resize((max(1, round(w * k)), max(1, round(h * k))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0 if transparent else 255))
    canvas.paste(rim, ((tw - rim.width) // 2, (th - rim.height) // 2), rim)
    return canvas if transparent else canvas.convert("RGB")


def _size(spec_size: Any, width: int | None = None, height: int | None = None) -> tuple[int, int]:
    if width and height:
        w, h = int(width), int(height)
    elif isinstance(spec_size, (list, tuple)):
        w, h = int(spec_size[0]), int(spec_size[1])
    elif isinstance(spec_size, str) and "x" in spec_size.lower():
        w, h = (int(v) for v in spec_size.lower().split("x"))
    elif isinstance(spec_size, str) and spec_size in SIZES:
        w, h = SIZES[spec_size]
    else:
        raise NAIError(f"Bad size {spec_size!r}; use {', '.join(SIZES)} or WxH")
    if w % 64 or h % 64:
        raise NAIError(f"Width and height must be multiples of 64, got {w}x{h}")
    return w, h


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def read_meta(path: str | Path) -> dict[str, Any]:
    """Return NovelAI metadata: {'source','software','params'(Comment JSON), ...}.

    Text chunks may sit after IDAT, so the image must be fully loaded before reading info.
    Falls back to the stealth alpha-channel encoding used by some tools.
    """
    im = _load(path)
    info = dict(im.info)
    if "Comment" not in info and im.mode == "RGBA":
        info.update(_read_stealth(im))
    out = {"source": info.get("Source"), "software": info.get("Software"), "description": info.get("Description")}
    if "Comment" in info:
        c = info["Comment"]
        out["params"] = json.loads(c) if isinstance(c, str) else c
    return out


def _read_stealth(im: Image.Image) -> dict[str, Any]:
    """Decode metadata hidden in the alpha LSBs (column-major), signature 'stealth_pngcomp'."""
    px = im.getchannel("A").load()
    w, h = im.size
    sig = b"stealth_pngcomp"
    raw = bytearray()
    acc, n, total = 0, 0, None
    for x in range(w):
        for y in range(h):
            acc = (acc << 1) | (px[x, y] & 1)
            n += 1
            if n % 8:
                continue
            raw.append(acc)
            acc = 0
            if len(raw) == len(sig) and bytes(raw) != sig:
                return {}
            if len(raw) == len(sig) + 4:
                total = len(sig) + 4 + int.from_bytes(raw[len(sig):], "big") // 8
            if total and len(raw) >= total:
                return json.loads(gzip.decompress(bytes(raw[len(sig) + 4:total])))
    return {}


def spec_from_meta(path: str | Path) -> dict[str, Any]:
    """Build a spec that re-sends exactly the captions and sampler flags stored in an image."""
    meta = read_meta(path)
    p = meta.get("params")
    if not p:
        raise NAIError(f"No NovelAI metadata in {path}")
    v4p = p.get("v4_prompt", {}) or {}
    v4n = p.get("v4_negative_prompt", {}) or {}
    cap = v4p.get("caption", {}) or {}
    ncap = v4n.get("caption", {}) or {}
    use_coords = bool(v4p.get("use_coords"))
    chars = []
    negs = ncap.get("char_captions") or []
    for i, cc in enumerate(cap.get("char_captions") or []):
        neg = negs[i].get("char_caption", "") if i < len(negs) else ""
        c = {"prompt": cc.get("char_caption", ""), "negative": neg}
        centers = cc.get("centers") or []
        if use_coords and centers:
            c["pos"] = [centers[0]["x"], centers[0]["y"]]
        chars.append(c)
    source = meta.get("source") or ""
    model_hash = source.split()[-1] if source else ""
    model = MODEL_HASHES.get(model_hash)
    spec = {
        "_source": source,
        "_software": meta.get("software"),
        "model": model or f"UNKNOWN ({source}) - set this",
        "prompt": cap.get("base_caption", p.get("prompt", "")),
        "negative": ncap.get("base_caption", p.get("uc", "")),
        "chars": chars,
        "quality": "none",  # already baked into the stored caption
        "uc": "none",
        "size": [p.get("width"), p.get("height")],
        "steps": p.get("steps"),
        "scale": p.get("scale"),
        "seed": p.get("seed"),
        "sampler": p.get("sampler"),
        "noise_schedule": p.get("noise_schedule", "karras"),
        "cfg_rescale": p.get("cfg_rescale", 0.0),
        "prefer_brownian": p.get("prefer_brownian", True),
        "ancestral_bug": p.get("deliberate_euler_ancestral_bug", False),
        "neg_use_order": bool(v4n.get("use_order", False)),
        # Keep tag hints exactly as sent: a missing hint becomes null, which removes it from the request.
        "extra": {"tag_hint_qt": p.get("tag_hint_qt"), "tag_hint_uc_preset": p.get("tag_hint_uc_preset"),
                  **({"skip_cfg_above_sigma": p["skip_cfg_above_sigma"]} if p.get("skip_cfg_above_sigma") else {})},
    }
    if p.get("reference_strength_multiple") or p.get("director_reference_strengths") or p.get("director_reference_descriptions"):
        spec["_warning"] = "Original used vibe transfer or character reference; images are not stored in metadata."
    return spec


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def list_styles() -> dict[str, str]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")).get("description", "")
            for p in sorted(STYLE_DIR.glob("*.json"))}


def load_style(name: str) -> dict[str, Any]:
    """A style is a spec layer between DEFAULTS and the spec. Its `prefix` / `suffix` wrap the
    prompt and its `negative` is prepended to the spec's negative, so styles add rather than replace."""
    p = Path(name) if name.endswith(".json") else STYLE_DIR / f"{name}.json"
    if not p.is_file():
        raise NAIError(f"Unknown style '{name}'. Available: {', '.join(list_styles()) or 'none'}")
    return json.loads(p.read_text(encoding="utf-8"))


def _merge(spec: dict[str, Any]) -> dict[str, Any]:
    s = copy.deepcopy(DEFAULTS)
    style = load_style(spec["style"]) if spec.get("style") else {}
    layer = {k: v for k, v in style.items() if k not in ("description", "prefix", "suffix", "negative")}
    for src in (layer, spec):
        for k, v in src.items():
            if v is not None or k == "seed":
                s[k] = v
    if style:
        s["prompt"] = join(style.get("prefix", ""), s.get("prompt", ""), style.get("suffix", ""))
        s["negative"] = join(style.get("negative", ""), s["negative"])
    s.pop("style", None)  # applied; keeps the resolved spec re-runnable without doubling
    return s


def paid_reasons(s: dict[str, Any], w: int, h: int) -> list[str]:
    r = []
    if w * h > FREE_MAX_PIXELS:
        r.append(f"{w}x{h} exceeds 1024x1024 pixels")
    if s["steps"] > FREE_MAX_STEPS:
        r.append(f"{s['steps']} steps > 28")
    if int(s.get("n", 1)) > 1:
        r.append(f"n={s['n']} images per request")
    if s.get("vibes"):
        r.append("vibe transfer (encoding new vibes costs Anlas)")
    if s.get("charref"):
        r.append("character reference")
    return r


def build_request(spec: dict[str, Any], allow_paid: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Turn a spec into the /ai/generate-image JSON body. Returns (body, resolved spec)."""
    s = _merge(spec)
    model = resolve_model(s["model"])
    info = model_info(model)
    w, h = _size(s["size"], s.get("width"), s.get("height"))
    if s["scale"] is None:
        s["scale"] = info["web_scale"]
    seed = s["seed"] if isinstance(s["seed"], int) and s["seed"] >= 0 else random.randint(0, 2**32 - 1)
    s["seed"] = seed

    reasons = paid_reasons(s, w, h)
    if reasons and not allow_paid:
        raise NAIError("Request may cost Anlas: " + "; ".join(reasons) + ". Pass allow_paid / --allow-paid to proceed.")

    quality = s["quality"] or "none"
    uc = UC_ALIASES.get(s["uc"], s["uc"]) or "none"
    if quality != "none" and quality not in info["quality"]:
        raise NAIError(f"Quality preset '{quality}' not available for {model}: {', '.join(info['quality'])}, none")
    if uc != "none" and uc not in info["uc"]:
        raise NAIError(f"UC preset '{uc}' not available for {model}: {', '.join(info['uc'])}, none")

    suffix = info["quality"].get(quality, "")
    if s["transparent"]:
        if not info["transparency"]:
            raise NAIError(f"{model} does not support transparent backgrounds")
        suffix = join("transparent background", suffix)
    prompt = join(s["prompt"], suffix)
    negative = join(info["uc"].get(uc, ""), s["negative"])

    chars = s["chars"] or []
    if len(chars) > info["max_chars"]:
        raise NAIError(f"{model} supports at most {info['max_chars']} characters, got {len(chars)}")
    use_coords = any(c.get("pos") for c in chars)
    char_pos, char_neg = [], []
    for c in chars:
        if isinstance(c, str):
            c = {"prompt": c}
        x, y = c.get("pos") or (0.5, 0.5)
        if not (0 <= x <= 1 and 0 <= y <= 1):
            raise NAIError(f"Character position must be within 0-1, got {c.get('pos')}")
        if use_coords and not info["freeform_pos"]:
            # V4/V4.5 snap to a 5x5 grid.
            x, y = (min(range(5), key=lambda i: abs(0.1 + 0.2 * i - v)) * 0.2 + 0.1 for v in (x, y))
        centers = [{"x": round(x, 4), "y": round(y, 4)}]
        char_pos.append({"char_caption": c.get("prompt", ""), "centers": centers})
        char_neg.append({"char_caption": c.get("negative", "") or "", "centers": centers})

    params: dict[str, Any] = {
        "params_version": 4,
        "width": w,
        "height": h,
        "scale": s["scale"],
        "sampler": s["sampler"],
        "steps": s["steps"],
        "n_samples": int(s.get("n", 1)),
        "seed": seed,
        "noise_schedule": s["noise_schedule"],
        "cfg_rescale": s["cfg_rescale"],
        "dynamic_thresholding": False,
        "controlnet_strength": 1,
        "legacy": False,
        "add_original_image": True,
        "legacy_v3_extend": False,
        "skip_cfg_above_sigma": None,
        "use_coords": use_coords,
        "legacy_uc": False,
        "normalize_reference_strength_multiple": True,
        "deliberate_euler_ancestral_bug": bool(s["ancestral_bug"]),
        "prefer_brownian": bool(s["prefer_brownian"]),
        "tag_hint_qt": TAG_HINT[quality],
        "tag_hint_uc_preset": TAG_HINT[uc],
        "v4_prompt": {
            "caption": {"base_caption": prompt, "char_captions": char_pos},
            "use_coords": use_coords,
            "use_order": True,
        },
        "v4_negative_prompt": {
            "caption": {"base_caption": negative, "char_captions": char_neg},
            "legacy_uc": False,
            "use_coords": use_coords,
            "use_order": bool(s["neg_use_order"]),
        },
        "negative_prompt": negative,
        "image_format": "png",
    }
    if s["transparent"]:
        params["tag_hint_transparent_background"] = True
    if s["variety"]:
        if not info["variety_sigma"]:
            raise NAIError(f"{model} does not support Variety Boost")
        params["skip_cfg_above_sigma"] = info["variety_sigma"] * ((w * h) / (832 * 1216)) ** 0.5

    action = "generate"
    i2i = s.get("i2i")
    if i2i:
        src = _fit(_load(i2i["image"]).convert("RGB"), w, h)
        params["image"] = _b64png(src)
        params["extra_noise_seed"] = max(seed - 1, 0)
        params["sm"] = params["sm_dyn"] = False
        if s.get("mask"):
            mask = _fit(_load(s["mask"]).convert("L"), w, h, mask=True).point(lambda v: 255 if v >= 128 else 0)
            # Grow the mask to whole 8x8 latent cells; partial cells leave visible seams at the edge.
            mask = mask.resize((w // 8, h // 8), Image.Resampling.BOX).point(lambda v: 255 if v > 0 else 0)
            mask = mask.resize((w, h), Image.Resampling.NEAREST)
            params["mask"] = _b64png(mask.convert("RGB"))
            strength = float(i2i.get("strength") or 1.0)
            if strength != 1.0:
                params["img2img"] = {"strength": strength, "color_correct": True}
            action = "infill"
            # V5 Curated has no inpainting model (HTTP 400); V5 Full inpainting blends in fine.
            if model == "nai-diffusion-5-curated":
                model = "nai-diffusion-5-full"
            model = model + "-inpainting"
        else:
            params["strength"] = float(i2i.get("strength") or 0.7)
            params["noise"] = float(i2i.get("noise") or 0.0)
            params["color_correct"] = False
            action = "img2img"
    elif s.get("mask"):
        raise NAIError("mask requires i2i.image (the picture to inpaint)")

    if s.get("vibes"):
        if not info["vibe"]:
            raise NAIError(f"{model} does not support vibe transfer (V4/V4.5 only)")
        encs, strengths, infos = [], [], []
        for v in s["vibes"]:
            ie = float(v.get("info", 1.0))
            encs.append(encode_vibe(v["image"], resolve_model(s["model"]), ie))
            strengths.append(float(v.get("strength", 0.6)))
            infos.append(ie)
        total = sum(abs(x) for x in strengths)
        if len(strengths) > 1 and total > 1:
            strengths = [x / total for x in strengths]
        params["reference_image_multiple"] = encs
        params["reference_strength_multiple"] = strengths
        params["reference_information_extracted_multiple"] = infos

    if s.get("charref"):
        if not info["charref"]:
            raise NAIError(f"{model} does not support character reference (V4.5 only)")
        refs = s["charref"] if isinstance(s["charref"], list) else [s["charref"]]
        params["director_reference_images"] = [_b64png(_pad_charref(_load(r["image"]))) for r in refs]
        params["director_reference_descriptions"] = [
            {"caption": {"base_caption": r.get("mode", "character&style"), "char_captions": []}, "legacy_uc": False}
            for r in refs]
        params["director_reference_information_extracted"] = [1.0 for _ in refs]
        params["director_reference_strength_values"] = [float(r.get("strength", 1.0)) for r in refs]
        params["director_reference_secondary_strength_values"] = [1.0 - float(r.get("fidelity", 1.0)) for r in refs]

    # Raw overrides; a null value removes the key (e.g. to mimic clients that omit tag hints).
    for k, v in (s.get("extra") or {}).items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    body = {"input": prompt, "model": model, "action": action, "parameters": params, "use_new_shared_trial": True}
    s.update({"width": w, "height": h, "model": model})
    return body, s


def generate_bytes(spec: dict[str, Any], allow_paid: bool = False) -> tuple[list[bytes], dict[str, Any]]:
    """Generate without saving. Returns (PNG bytes per image, resolved spec incl. seed/model/width/height)."""
    body, s = build_request(spec, allow_paid=allow_paid)
    with _account_lock():
        data, _ = request("POST", f"{IMAGE_API}/ai/generate-image", body)
    s["action"] = body["action"]
    return images_from_response(data), s


def generate(spec: dict[str, Any], allow_paid: bool = False) -> list[dict[str, Any]]:
    """Generate from a spec; saves PNGs (with NovelAI metadata intact). Returns [{'path','seed',...}]."""
    imgs, s = generate_bytes(spec, allow_paid=allow_paid)
    out = Path(s["out"]).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    results = []
    for i, b in enumerate(imgs):
        seed = s["seed"] + i
        path = out / f"{s['name']}_{stamp}_{seed}{'_' + str(i) if len(imgs) > 1 else ''}.png"
        k = 1
        while path.exists():
            path = out / f"{s['name']}_{stamp}_{seed}_{k}.png"
            k += 1
        path.write_bytes(b)
        results.append({"path": str(path.resolve()), "seed": seed, "model": s["model"],
                        "size": f"{s['width']}x{s['height']}", "action": s["action"]})
    return results


def encode_vibe(image: str, model: str, info: float = 1.0) -> str:
    """Encode (and cache) a vibe reference. Cached encodings cost nothing; new ones cost Anlas."""
    raw = Path(image).read_bytes()
    key = hashlib.sha256(raw + f"|{model}|{info:.3f}".encode()).hexdigest()[:32]
    cache = Path.home() / ".cache" / "nai-skill" / "vibes" / f"{key}.b64"
    if cache.exists():
        return cache.read_text()
    body = {"image": base64.b64encode(raw).decode(), "information_extracted": info, "model": model}
    with _account_lock():
        data, _ = request("POST", f"{IMAGE_API}/ai/encode-vibe", body)
    enc = base64.b64encode(data).decode()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(enc)
    return enc


def suggest_tags(query: str, model: str = "nai-diffusion-5-full", lang: str = "en") -> list[dict[str, Any]]:
    data, _ = request("GET", f"{IMAGE_API}/ai/generate-image/suggest-tags",
                      query={"model": resolve_model(model), "prompt": query, "lang": lang})
    j = json.loads(data)
    return j.get("tags", j) if isinstance(j, dict) else j


def balance() -> dict[str, Any]:
    data, _ = request("GET", f"{IMAGE_API}/user/subscription")
    j = json.loads(data)
    steps = j.get("trainingStepsLeft") or {}
    out = {
        "tier": j.get("tier"),
        "active": j.get("active"),
        "anlas_fixed": steps.get("fixedTrainingStepsLeft"),
        "anlas_purchased": steps.get("purchasedTrainingSteps"),
    }
    u = j.get("usage")
    if u:
        # Opus free-generation meter (V5). Same math as the web client.
        left = 0 if u.get("isNegative") else max(0, u.get("percent", 0))
        t = u.get("timeUntilNextPercent") or 0
        out["opus_meter"] = {
            "percent_left": left,
            "approx_images_left": round(17.3 * left),
            "refill_percent_per_day": round(86400 / t, 1) if t > 0 else 0,
            "low": bool(u.get("isNegative") or u.get("percent", 0) < 5),
        }
    return out


def upscale(image: str, out: str = ".", model: str = "nai-diffusion-5-full") -> str:
    raw = Path(image).read_bytes()
    with _account_lock():
        data, _ = request("POST", f"{IMAGE_API}/ai/upscale",
                          {"image": base64.b64encode(raw).decode(), "model": resolve_model(model)})
    b = images_from_response(data)[0]
    p = Path(out) / f"{Path(image).stem}_upscaled.png"
    p.write_bytes(b)
    return str(p.resolve())


AUGMENT_TOOLS = ["bg-removal", "lineart", "sketch", "colorize", "emotion", "declutter"]


def augment(tool: str, image: str, out: str = ".", prompt: str = "", emotion: str = "neutral", defry: int = 0) -> list[str]:
    if tool not in AUGMENT_TOOLS:
        raise NAIError(f"tool must be one of {AUGMENT_TOOLS}")
    im = _load(image)
    body: dict[str, Any] = {"req_type": tool, "image": base64.b64encode(Path(image).read_bytes()).decode(),
                            "width": im.width, "height": im.height}
    if tool == "emotion":
        body.update(prompt=f"{emotion};;{prompt}", defry=defry)
    elif tool == "colorize":
        body.update(prompt=prompt, defry=defry)
    with _account_lock():
        data, _ = request("POST", f"{IMAGE_API}/ai/augment-image", body)
    paths = []
    for i, b in enumerate(images_from_response(data)):
        p = Path(out) / f"{Path(image).stem}_{tool}{'_' + str(i) if i else ''}.png"
        p.write_bytes(b)
        paths.append(str(p.resolve()))
    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_value(v: str) -> Any:
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def _load_specs(paths: list[str]) -> list[dict[str, Any]]:
    """A spec file holds one spec, a list of specs, or {"defaults": {...}, "jobs": [...]}."""
    specs = []
    for p in paths:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        if isinstance(j, dict) and "jobs" in j:
            d = j.get("defaults", {})
            specs += [{**d, **job} for job in j["jobs"]]
        elif isinstance(j, list):
            specs += j
        else:
            specs.append(j)
    return specs


def _cmd_gen(a: argparse.Namespace) -> int:
    specs = _load_specs(a.spec) if a.spec else [{}]
    over: dict[str, Any] = {}
    for k in ("style", "prompt", "negative", "model", "size", "steps", "scale", "seed", "quality", "uc", "sampler",
              "out", "name", "n"):
        v = getattr(a, k, None)
        if v is not None:
            over[k] = v
    if a.prompt_file:
        over["prompt"] = Path(a.prompt_file).read_text(encoding="utf-8").strip()
    if a.char:
        chars = []
        for c in a.char:
            text, _, pos = c.partition("@")
            d: dict[str, Any] = {"prompt": text.strip()}
            if pos:
                d["pos"] = [float(v) for v in pos.split(",")]
            chars.append(d)
        over["chars"] = chars
    if a.i2i:
        over["i2i"] = {"image": a.i2i, "strength": a.strength, "noise": a.noise}
    if a.mask:
        over["mask"] = a.mask
    for flag in ("variety", "transparent"):
        if getattr(a, flag):
            over[flag] = True
    if a.brownian is not None:
        over["prefer_brownian"] = a.brownian
    for kv in a.set or []:
        k, _, v = kv.partition("=")
        if k.startswith("extra."):
            over.setdefault("extra", {})[k[6:]] = _parse_value(v)
        else:
            over[k] = _parse_value(v)
    rc = 0
    for spec in specs:
        spec = {**spec, **over}
        if a.dry_run:
            body, _ = build_request(spec, allow_paid=True)
            p = body["parameters"]
            for k in ("image", "mask", "reference_image_multiple", "director_reference_images"):
                if k in p:
                    p[k] = "<omitted>"
            print(json.dumps(body, ensure_ascii=False, indent=1))
            continue
        try:
            for r in generate(spec, allow_paid=a.allow_paid):
                print(json.dumps(r, ensure_ascii=False))
        except NAIError as e:
            print(json.dumps({"error": str(e), "name": spec.get("name")}, ensure_ascii=False))
            rc = 1
    return rc


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="nai.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="generate images")
    g.add_argument("spec", nargs="*", help="spec JSON file(s)")
    g.add_argument("-s", "--style", help="style preset from styles/ (see `styles`), or a path to a style JSON")
    g.add_argument("-p", "--prompt")
    g.add_argument("--prompt-file")
    g.add_argument("--neg", dest="negative")
    g.add_argument("-c", "--char", action="append", help='character prompt, optional "@x,y" position (0-1)')
    g.add_argument("-m", "--model")
    g.add_argument("--size", help="portrait|landscape|square|WxH")
    g.add_argument("--steps", type=int)
    g.add_argument("--scale", type=float)
    g.add_argument("--seed", type=int)
    g.add_argument("-n", type=int, dest="n")
    g.add_argument("--quality", help="standard|light|none")
    g.add_argument("--uc", help="heavy|light|humanFocus|furryFocus|none")
    g.add_argument("--sampler")
    g.add_argument("--variety", action="store_true", help="Variety Boost (V4/V4.5)")
    g.add_argument("--transparent", action="store_true", help="transparent background (V5)")
    g.add_argument("--brownian", dest="brownian", action="store_true", default=None)
    g.add_argument("--no-brownian", dest="brownian", action="store_false")
    g.add_argument("--i2i", help="source image for img2img / inpaint")
    g.add_argument("--strength", type=float, help="img2img default 0.7, inpaint default 1.0")
    g.add_argument("--noise", type=float)
    g.add_argument("--mask", help="inpaint mask (white = repaint)")
    g.add_argument("-o", "--out")
    g.add_argument("--name", help="filename prefix")
    g.add_argument("--set", action="append", help="override any spec key, e.g. --set chars='[...]' --set extra.x=1")
    g.add_argument("--allow-paid", action="store_true")
    g.add_argument("--dry-run", action="store_true", help="print the request body without sending")

    m = sub.add_parser("meta", help="read NovelAI metadata from an image")
    m.add_argument("image")
    m.add_argument("--spec", action="store_true", help="print a spec that reproduces the image")

    sub.add_parser("balance", help="Anlas and Opus usage")
    sub.add_parser("styles", help="list style presets")
    t = sub.add_parser("tags", help="tag suggestions")
    t.add_argument("query")
    t.add_argument("-m", "--model", default="v5")
    c = sub.add_parser("caps", help="model capabilities")
    c.add_argument("model", nargs="?")
    u = sub.add_parser("upscale")
    u.add_argument("image")
    u.add_argument("-o", "--out", default=".")
    u.add_argument("--allow-paid", action="store_true")
    au = sub.add_parser("augment")
    au.add_argument("tool", choices=AUGMENT_TOOLS)
    au.add_argument("image")
    au.add_argument("-o", "--out", default=".")
    au.add_argument("--prompt", default="")
    au.add_argument("--emotion", default="neutral")
    au.add_argument("--defry", type=int, default=0)
    au.add_argument("--allow-paid", action="store_true")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "gen":
            return _cmd_gen(a)
        if a.cmd == "meta":
            obj = spec_from_meta(a.image) if a.spec else read_meta(a.image)
            print(json.dumps(obj, ensure_ascii=False, indent=1))
        elif a.cmd == "styles":
            for k, v in list_styles().items():
                print(f"{k:12} {v}")
        elif a.cmd == "balance":
            print(json.dumps(balance(), ensure_ascii=False, indent=1))
        elif a.cmd == "tags":
            for tg in suggest_tags(a.query, a.model):
                print(json.dumps(tg, ensure_ascii=False))
        elif a.cmd == "caps":
            names = [resolve_model(a.model)] if a.model else list(MODELS)
            for n in names:
                i = model_info(n)
                print(json.dumps({"model": n, "quality": list(i["quality"]), "uc": list(i["uc"]),
                                  **{k: v for k, v in i.items() if k not in ("quality", "uc")}}, ensure_ascii=False))
        elif a.cmd in ("upscale", "augment"):
            if not a.allow_paid:
                raise NAIError(f"{a.cmd} may cost Anlas; ask the user, then pass --allow-paid")
            if a.cmd == "upscale":
                print(json.dumps({"path": upscale(a.image, a.out)}))
            else:
                print(json.dumps({"paths": augment(a.tool, a.image, a.out, a.prompt, a.emotion, a.defry)}))
        return 0
    except NAIError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
