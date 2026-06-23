import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from io import BytesIO
from pathlib import Path
from statistics import median
from xml.sax.saxutils import escape

import pdfplumber
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "source_codex_maxxing26.pdf"
TMP_DIR = ROOT / "tmp" / "pdfs" / "codex_cn"
PREVIEW_DIR = TMP_DIR / "rendered_pages"
BLOCKS_JSON = TMP_DIR / "blocks.json"
TRANSLATIONS_JSON = TMP_DIR / "translations.json"
POLISH_OVERRIDES_JSON = ROOT / "scripts" / "cn_polish_overrides.json"
OVERLAY_PDF = TMP_DIR / "overlay.pdf"
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PDF = OUTPUT_DIR / "OAI_WhitePaper_Codex-maxxing26_中文润色增强版.pdf"
PDFTOPPM = Path(
    r"C:\Users\kaodanzi\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
)

CJK_FONT = "DengXian"
pdfmetrics.registerFont(TTFont(CJK_FONT, r"C:\Windows\Fonts\Deng.ttf"))

TERM_VARIANTS = {
    "repository": ("repository", "repositories", "repo", "repos", "代码库", "代码仓", "存储库"),
    "open loops": ("open loops", "open loop", "未完成事项", "未关闭事项", "开放循环", "开环"),
    "remote control": ("remote control", "远程操控", "远程操纵", "遥控"),
    "vault": ("vault", "拱顶", "保管库"),
    "steering": ("steering", "转向", "操舵"),
    "durable thread": ("durable thread", "持久对话", "耐用线程"),
    "durable threads": ("durable threads", "耐用的线程", "耐用线程"),
    "thread automations": ("thread automations", "线程自动化功能", "对话自动化"),
    "computer and browser use": ("computer and browser use", "计算机和浏览器使用", "电脑和浏览器使用"),
    "side panel": ("side panel", "侧边面板"),
    "goals": ("goals", "目标项"),
    "memory": ("memory", "记忆功能"),
}


def ensure_dirs():
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def mostly_non_letters(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return True
    letters = re.findall(r"[A-Za-z]", stripped)
    return len(letters) / max(len(stripped), 1) < 0.18


def normalize_block_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    joined = "\n".join(lines)
    joined = joined.replace(" ]", "]").replace("[ ", "[")
    return joined.strip()


def extract_blocks():
    if BLOCKS_JSON.exists():
        return json.loads(BLOCKS_JSON.read_text(encoding="utf-8"))

    pages_out = []
    with pdfplumber.open(str(SOURCE_PDF)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(
                extra_attrs=["fontname", "size"],
                use_text_flow=True,
                keep_blank_chars=False,
            )

            lines = []
            for word in words:
                cy = round((word["top"] + word["bottom"]) / 2, 1)
                for line in lines:
                    if (
                        abs(line["cy"] - cy) <= max(2.5, word["size"] * 0.18)
                        and abs(line["size"] - word["size"]) <= 1.5
                    ):
                        line["words"].append(word)
                        line["cy"] = (line["cy"] * (len(line["words"]) - 1) + cy) / len(line["words"])
                        break
                else:
                    lines.append({"cy": cy, "size": word["size"], "words": [word]})

            segmented_lines = []
            for line in lines:
                words_sorted = sorted(line["words"], key=lambda item: item["x0"])
                segments = []
                current = [words_sorted[0]]
                for prev, word in zip(words_sorted, words_sorted[1:]):
                    gap = word["x0"] - prev["x1"]
                    if gap > max(26, line["size"] * 1.75):
                        segments.append(current)
                        current = [word]
                    else:
                        current.append(word)
                segments.append(current)

                for segment in segments:
                    segmented_lines.append(
                        {
                            "size": line["size"],
                            "text": " ".join(word["text"] for word in segment).strip(),
                            "x0": min(word["x0"] for word in segment),
                            "x1": max(word["x1"] for word in segment),
                            "top": min(word["top"] for word in segment),
                            "bottom": max(word["bottom"] for word in segment),
                            "fontname": segment[0]["fontname"],
                        }
                    )

            lines = sorted(segmented_lines, key=lambda item: (item["top"], item["x0"]))
            blocks = []
            for line in lines:
                if not line["text"]:
                    continue
                if blocks:
                    prev = blocks[-1]
                    same_col = abs(prev["x0"] - line["x0"]) < 28 or (
                        line["x0"] >= prev["x0"] and line["x0"] <= prev["x1"] + 20
                    )
                    gap = line["top"] - prev["bottom"]
                    size_close = abs(prev["size"] - line["size"]) <= 2
                    if same_col and gap <= max(22, line["size"] * 1.6) and size_close:
                        prev["lines"].append(line)
                        prev["x0"] = min(prev["x0"], line["x0"])
                        prev["x1"] = max(prev["x1"], line["x1"])
                        prev["top"] = min(prev["top"], line["top"])
                        prev["bottom"] = max(prev["bottom"], line["bottom"])
                        prev["size"] = max(prev["size"], line["size"])
                        continue
                blocks.append(
                    {
                        "x0": line["x0"],
                        "x1": line["x1"],
                        "top": line["top"],
                        "bottom": line["bottom"],
                        "size": line["size"],
                        "fontname": line["fontname"],
                        "lines": [line],
                    }
                )

            page_blocks = []
            for block_index, block in enumerate(blocks, start=1):
                text = normalize_block_text("\n".join(line["text"] for line in block["lines"]))
                if len(text) <= 1:
                    continue
                page_blocks.append(
                    {
                        "block_id": f"p{page_index}_b{block_index}",
                        "bbox": [
                            round(block["x0"], 2),
                            round(block["top"], 2),
                            round(block["x1"], 2),
                            round(block["bottom"], 2),
                        ],
                        "fontname": block["fontname"],
                        "size": round(block["size"], 2),
                        "text": text,
                    }
                )

            pages_out.append({"page": page_index, "width": page.width, "height": page.height, "blocks": page_blocks})

    BLOCKS_JSON.write_text(json.dumps(pages_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return pages_out


def google_translate(text: str) -> str:
    params = urllib.parse.urlencode(
        {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": text}
    )
    url = "https://translate.googleapis.com/translate_a/single?" + params
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    parts = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
    result = "".join(parts).strip()
    return result or text


def load_translation_cache():
    if TRANSLATIONS_JSON.exists():
        return json.loads(TRANSLATIONS_JSON.read_text(encoding="utf-8"))
    return {}


def save_translation_cache(cache):
    TRANSLATIONS_JSON.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def load_polish_overrides():
    if not POLISH_OVERRIDES_JSON.exists():
        return {"term_map": {}, "direct_map": {}}
    return json.loads(POLISH_OVERRIDES_JSON.read_text(encoding="utf-8"))


def source_mentions_term(source_text: str, source_term: str) -> bool:
    variants = set(TERM_VARIANTS.get(source_term.lower(), ()))
    variants.add(source_term)
    english_variants = {
        variant
        for variant in variants
        if re.fullmatch(r"[A-Za-z][A-Za-z\s-]*", variant)
    }
    return any(re.search(re.escape(variant), source_text, flags=re.IGNORECASE) for variant in english_variants)


def replace_terms(source_text: str, translated_text: str, term_map: dict[str, str]) -> str:
    result = translated_text
    placeholders = {}
    for index, (source_term, target_term) in enumerate(
        sorted(term_map.items(), key=lambda item: len(item[0]), reverse=True)
    ):
        if not source_mentions_term(source_text, source_term):
            continue
        placeholder = f"__TERM_{index}__"
        placeholders[placeholder] = target_term
        variants = set(TERM_VARIANTS.get(source_term.lower(), ()))
        variants.add(source_term)
        for variant in sorted(variants, key=len, reverse=True):
            result = re.sub(re.escape(variant), placeholder, result, flags=re.IGNORECASE)
    for placeholder, target_term in placeholders.items():
        result = result.replace(placeholder, target_term)
    return result


def apply_polish(source_text: str, translated_text: str, overrides: dict) -> str:
    direct_map = overrides.get("direct_map", {})
    term_map = overrides.get("term_map", {})
    normalized_source = source_text.strip()

    if normalized_source in direct_map:
        return direct_map[normalized_source].strip()

    polished = replace_terms(normalized_source, translated_text.strip(), term_map)
    for wrong_term, corrected_term in {
        "法典": "Codex",
        "螺纹": "线程",
    }.items():
        polished = polished.replace(wrong_term, corrected_term)

    return re.sub(r"\s+", " ", polished).strip()


def build_translations(block_pages):
    cache = load_translation_cache()
    overrides = load_polish_overrides()
    updated = False
    for page in block_pages:
        for block in page["blocks"]:
            text = block["text"]
            if text not in cache:
                if mostly_non_letters(text):
                    cache[text] = text
                else:
                    cache[text] = google_translate(text)
                    time.sleep(0.12)
                updated = True

            polished = apply_polish(text, cache[text], overrides)
            if polished != cache[text]:
                cache[text] = polished
                updated = True
    if updated:
        save_translation_cache(cache)
    return cache


def render_reference_pages():
    expected = PREVIEW_DIR / "page-01.png"
    if expected.exists():
        return
    import subprocess

    subprocess.run(
        [
            str(PDFTOPPM),
            "-png",
            str(SOURCE_PDF),
            str(PREVIEW_DIR / "page"),
        ],
        check=True,
    )


def rgb_tuple(image: Image.Image, bbox, page_width, page_height):
    width, height = image.size
    scale_x = width / page_width
    scale_y = height / page_height
    x0, top, x1, bottom = bbox
    left = max(0, int((x0 - 2) * scale_x))
    right = min(width, int((x1 + 2) * scale_x))
    upper = max(0, int((top - 2) * scale_y))
    lower = min(height, int((bottom + 2) * scale_y))
    crop = image.crop((left, upper, right, lower)).convert("RGB")
    pixels = list(crop.getdata())
    if not pixels:
        return (255, 255, 255)
    sampled = pixels[:: max(1, len(pixels) // 4000)]
    med = tuple(int(median(channel)) for channel in zip(*sampled))
    return med


def choose_text_color(bg_rgb):
    luminance = (0.299 * bg_rgb[0]) + (0.587 * bg_rgb[1]) + (0.114 * bg_rgb[2])
    if luminance < 140:
        return (255, 255, 255)
    return (34, 31, 35)


def make_style(font_size, color_rgb):
    return ParagraphStyle(
        name=f"Zh-{font_size:.2f}",
        fontName=CJK_FONT,
        fontSize=font_size,
        leading=font_size * 1.18,
        textColor=Color(*(c / 255 for c in color_rgb)),
        alignment=TA_LEFT,
        wordWrap="CJK",
        allowWidows=1,
        allowOrphans=1,
        spaceBefore=0,
        spaceAfter=0,
    )


def fit_paragraph(text, width, height, preferred_size, color_rgb):
    text = escape(text).replace("\n", "<br/>")
    min_size = max(5.0, preferred_size * 0.42)
    best = None
    size = preferred_size
    while size >= min_size:
        style = make_style(size, color_rgb)
        para = Paragraph(text, style)
        req_width, req_height = para.wrap(width, height)
        if req_height <= height and req_width <= width + 1:
            best = (para, style, req_height)
            break
        size -= max(0.5, preferred_size * 0.05)
    if best is None:
        style = make_style(min_size, color_rgb)
        para = Paragraph(text, style)
        _, req_height = para.wrap(width, max(height, preferred_size * 8))
        best = (para, style, min(req_height, max(height, preferred_size * 8)))
    return best


def draw_overlay(block_pages, translations):
    images = {}
    packet = BytesIO()
    c = canvas.Canvas(packet)

    for page in block_pages:
        page_width = float(page["width"])
        page_height = float(page["height"])
        c.setPageSize((page_width, page_height))

        image_path = PREVIEW_DIR / f"page-{page['page']:02d}.png"
        if image_path not in images:
            images[image_path] = Image.open(image_path)
        ref_img = images[image_path]

        for block in page["blocks"]:
            x0, top, x1, bottom = block["bbox"]
            width = max(8, x1 - x0)
            height = max(8, bottom - top)
            translated = translations.get(block["text"], block["text"]).strip()
            if not translated:
                continue

            bg_rgb = rgb_tuple(ref_img, block["bbox"], page_width, page_height)
            text_rgb = choose_text_color(bg_rgb)

            pad_x = max(2, min(8, block["size"] * 0.18))
            pad_y = max(1.5, min(6, block["size"] * 0.12))
            rect_x = x0 - pad_x
            rect_y = page_height - bottom - pad_y
            rect_w = width + pad_x * 2
            rect_h = height + pad_y * 2

            c.setFillColor(Color(*(value / 255 for value in bg_rgb)))
            c.setStrokeColor(Color(*(value / 255 for value in bg_rgb)))
            c.rect(rect_x, rect_y, rect_w, rect_h, fill=1, stroke=1)

            para, style, req_height = fit_paragraph(
                translated,
                max(6, width + pad_x * 1.2),
                max(6, height + pad_y * 1.1),
                preferred_size=max(6.5, float(block["size"]) * 0.94),
                color_rgb=text_rgb,
            )

            draw_x = x0
            draw_y = page_height - top - req_height + (pad_y * 0.2)
            para.drawOn(c, draw_x, draw_y)

        c.showPage()

    c.save()
    OVERLAY_PDF.write_bytes(packet.getvalue())


def merge_overlay():
    original = PdfReader(str(SOURCE_PDF))
    overlay = PdfReader(str(OVERLAY_PDF))
    writer = PdfWriter()
    for base_page, overlay_page in zip(original.pages, overlay.pages):
        base_page.merge_page(overlay_page)
        writer.add_page(base_page)
    with OUTPUT_PDF.open("wb") as f:
        writer.write(f)


def main():
    ensure_dirs()
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(f"Source PDF not found: {SOURCE_PDF}")
    block_pages = extract_blocks()
    render_reference_pages()
    translations = build_translations(block_pages)
    draw_overlay(block_pages, translations)
    merge_overlay()
    print(str(OUTPUT_PDF))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
