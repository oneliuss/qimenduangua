# -*- coding: utf-8 -*-
"""
报告文本转图片管线。
优先级：AstrBot html_render（网络 Jinja2 渲染）-> Pillow 本地排版 -> None（由调用方降级纯文本）。
"""
import os

from PIL import Image, ImageDraw, ImageFont

from qimen_chart import BG, GOLD, GOLD_DIM, TEXT, TEXT_DIM, find_cjk_font, load_font

# ---------- 玄黑金 HTML 模板（html_render 用，Jinja2）----------
REPORT_HTML_TMPL = """
<html><body style="margin:0;background:rgb(16,18,26);">
<div style="width:760px;margin:0 auto;padding:28px 32px;
     font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;
     background:rgb(16,18,26);color:rgb(232,228,218);">
  <div style="text-align:center;color:rgb(212,175,55);font-size:30px;
       font-weight:bold;letter-spacing:6px;">{{ title }}</div>
  <hr style="border:none;border-top:2px solid rgb(140,118,62);margin:18px 0;">
  <pre style="white-space:pre-wrap;word-break:break-all;font-size:19px;
       line-height:1.75;font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;
       margin:0;">{{ content }}</pre>
</div></body></html>
"""


# ---------- Pillow 本地排版 ----------
_IMG_W = 840
_PAD = 30
_LINE_GAP = 10


def _wrap_line(draw, line, font, max_w):
    """按像素宽度折行（逐字符，天然支持中文）。"""
    if not line:
        return [""]
    out, cur = [], ""
    for ch in line:
        if draw.textlength(cur + ch, font=font) > max_w:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    out.append(cur)
    return out


# ---------- 彩色 emoji 支持（CJK 字体无表情字形，需 emoji 字体回退）----------
_EMOJI_FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguiemj.ttf",                      # Windows Segoe UI Emoji（COLR 矢量）
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Debian/Ubuntu fonts-noto-color-emoji
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",           # Alpine font-noto-color-emoji
    "/System/Library/Fonts/Apple Color Emoji.ttc",        # macOS（sbix，Pillow 不支持时探测会自动跳过）
]
_EMOJI_SCAN_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")]
_EMOJI_CACHE = None  # (size, font, kind)


def _is_emoji(ch):
    """是否表情/符号字符（用于选择 emoji 字体绘制）。"""
    cp = ord(ch)
    return (
        0x1F000 <= cp <= 0x1FAFF      # 表情主体（🐉📡🕐📜🔮🟢…）
        or 0x2600 <= cp <= 0x27BF     # 杂项符号与装饰符（⚠✅❌✓✗…）
        or 0x2B00 <= cp <= 0x2BFF     # 补充符号（⭐…）
        or cp == 0x200D               # 零宽连接符
        or 0xFE00 <= cp <= 0xFE0F     # 变体选择符
    )


def _is_hard_emoji(ch):
    """CJK 字体必然缺字形的表情字符（无 emoji 字体时剔除，避免豆腐块）。"""
    cp = ord(ch)
    return 0x1F000 <= cp <= 0x1FAFF or 0x2B00 <= cp <= 0x2BFF or cp == 0x200D or 0xFE00 <= cp <= 0xFE0F


def _strip_emoji(s):
    """移除硬表情字符（仅无 emoji 字体时调用）。"""
    return "".join(ch for ch in s if not _is_hard_emoji(ch))


def _load_emoji_font(size):
    """加载彩色 emoji 字体，返回 (font, kind)。
    kind='vector'：可按任意 size 直接绘制（COLR/轮廓矢量字体）；
    kind='bitmap'：CBDT 位图字体（只能按固有尺寸渲染，需缩放后内联贴上）；
    找不到或不支持返回 (None, None)。按 size 缓存结果。
    """
    global _EMOJI_CACHE
    if _EMOJI_CACHE is not None and _EMOJI_CACHE[0] == size:
        return _EMOJI_CACHE[1], _EMOJI_CACHE[2]

    def _probe_ok(font):
        # 实际渲染一个表情，确认字体真能出彩（排除 sbix 等加载成功但渲不出的情况）
        probe = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
        ImageDraw.Draw(probe).text((0, 0), "\U0001F600", font=font, embedded_color=True)
        return probe.getbbox() is not None

    result = (None, None)
    paths = [p for p in _EMOJI_FONT_CANDIDATES if os.path.exists(p)]
    if not paths:  # 静态候选未命中，扫描常见字体目录兜底
        for d in _EMOJI_SCAN_DIRS:
            if not os.path.isdir(d):
                continue
            for root, _dirs, files in os.walk(d):
                for fn in sorted(files):
                    low = fn.lower()
                    if "emoji" in low and low.endswith((".ttf", ".ttc", ".otf")):
                        paths.append(os.path.join(root, fn))
    for path in paths:
        try:  # 优先按目标尺寸加载（COLR/轮廓矢量字体）
            f = ImageFont.truetype(path, size)
            if _probe_ok(f):
                result = (f, "vector")
                break
        except Exception:
            pass
        for strike in (109, 128, 136, 160):  # CBDT 位图字体按固有尺寸逐个尝试
            try:
                f = ImageFont.truetype(path, strike)
                if _probe_ok(f):
                    result = (f, "bitmap")
                    break
            except Exception:
                continue
        if result[0] is not None:
            break
    _EMOJI_CACHE = (size, result[0], result[1])
    return result


def _draw_emoji(img, draw, x, y, ch, font, kind, size):
    """在 (x, y) 绘制单个彩色 emoji，返回前进宽度（像素）。"""
    if kind == "vector":
        try:
            draw.text((x, y), ch, font=font, embedded_color=True)
        except Exception:
            pass
        try:
            return int(draw.textlength(ch, font=font)) or size
        except Exception:
            return size
    # bitmap（CBDT）：按固有尺寸渲染到透明小图 → 裁剪 → 缩放到字号高度 → 内联贴上
    try:
        tile = Image.new("RGBA", (font.size * 2, font.size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((0, 0), ch, font=font, embedded_color=True)
        bbox = tile.getbbox()
        if not bbox:
            return size
        tile = tile.crop(bbox)
        th = size + 4
        tw = max(1, round(tile.width * th / tile.height))
        tile = tile.resize((tw, th), Image.LANCZOS)
        img.paste(tile, (x, y - 2), tile)
        return tw
    except Exception:
        return size


def _draw_text_mixed(img, draw, x, y, line, cjk_font, fill, emoji_font, emoji_kind, size):
    """混合绘制一行文本：普通字符用 CJK 字体，表情字符用彩色 emoji 字体。"""
    cx = x
    run = ""
    for ch in line:
        if emoji_font is not None and _is_emoji(ch):
            if run:
                draw.text((cx, y), run, font=cjk_font, fill=fill)
                cx += draw.textlength(run, font=cjk_font)
                run = ""
            cp = ord(ch)
            if 0xFE00 <= cp <= 0xFE0F or cp == 0x200D:
                continue  # 变体选择符/零宽连接符不单独绘制
            cx += _draw_emoji(img, draw, cx, y, ch, emoji_font, emoji_kind, size)
        else:
            run += ch
    if run:
        draw.text((cx, y), run, font=cjk_font, fill=fill)


def render_text_local(report_text, title, out_path, width=_IMG_W):
    """把报告文本用 Pillow 排成玄黑金长图。返回 out_path。width：画布宽度，默认 840。"""
    if not find_cjk_font():
        raise RuntimeError("no CJK font found")
    f_title = load_font(34, bold=True)
    f_body = load_font(22)
    emoji_font, emoji_kind = _load_emoji_font(f_body.size)
    probe = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(probe)
    max_w = width - _PAD * 2
    lines = []
    for raw in report_text.split("\n"):
        if emoji_font is None:
            raw = _strip_emoji(raw)  # 无 emoji 字体时剔除表情，避免豆腐块
        lines.extend(_wrap_line(d, raw, f_body, max_w))
    line_h = 22 + _LINE_GAP
    h = _PAD + 54 + 16 + line_h * len(lines) + _PAD
    img = Image.new("RGB", (width, h), BG)
    draw = ImageDraw.Draw(img)
    # 标题居中 + 金色分隔线
    tw = draw.textlength(title, font=f_title)
    draw.text(((width - tw) / 2, _PAD), title, font=f_title, fill=GOLD)
    draw.line([(_PAD, _PAD + 48), (width - _PAD, _PAD + 48)], fill=GOLD_DIM, width=2)
    y = _PAD + 64
    for ln in lines:
        _draw_text_mixed(img, draw, _PAD, y, ln, f_body, TEXT, emoji_font, emoji_kind, f_body.size)
        y += line_h
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


async def render_report_image(star, report_text, title, out_path):
    """报告转图片。返回 http URL 或本地路径；全部失败返回 None。
    star：插件实例（提供 html_render 协程）。
    """
    try:
        url = await star.html_render(
            REPORT_HTML_TMPL, {"title": title, "content": report_text}, return_url=True
        )
        if url:
            return url
    except Exception:
        pass
    try:
        return render_text_local(report_text, title, out_path)
    except Exception:
        return None


# ---------- 合并图（排盘图 + 分隔带 + 报告）----------
_MERGE_W = 960        # 合并图宽度（与排盘图一致）
_MERGE_GAP = 40       # 分隔带高度
_MERGE_BOTTOM = 24    # 底部留白


def render_merged_image(chart_path, report_text, title, out_path):
    """把排盘图与报告合并为一幅 960 宽长图：排盘图 + 40px 分隔带 + 报告标题与正文。
    返回 out_path。任何异常向上抛出，由调用方降级。
    """
    if not find_cjk_font():
        raise RuntimeError("no CJK font found")
    chart = Image.open(chart_path).convert("RGB")
    if chart.size[0] != _MERGE_W:
        raise RuntimeError(f"chart width must be {_MERGE_W}, got {chart.size[0]}")
    chart_h = chart.size[1]
    f_title = load_font(34, bold=True)
    f_body = load_font(22)
    emoji_font, emoji_kind = _load_emoji_font(f_body.size)
    probe = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(probe)
    max_w = _MERGE_W - _PAD * 2
    lines = []
    for raw in report_text.split("\n"):
        if emoji_font is None:
            raw = _strip_emoji(raw)  # 无 emoji 字体时剔除表情，避免豆腐块
        lines.extend(_wrap_line(d, raw, f_body, max_w))
    line_h = 22 + _LINE_GAP
    # 报告区块高（与 render_text_local 同构：上留白 + 标题区 + 正文 + 下留白）
    block_h = _PAD + 54 + 16 + line_h * len(lines) + _PAD
    h = chart_h + _MERGE_GAP + block_h + _MERGE_BOTTOM
    img = Image.new("RGB", (_MERGE_W, h), BG)
    img.paste(chart, (0, 0))
    draw = ImageDraw.Draw(img)
    # 分隔带：暗金横线居中
    gy = chart_h + _MERGE_GAP // 2
    draw.line([(_PAD, gy), (_MERGE_W - _PAD, gy)], fill=GOLD_DIM, width=2)
    # 报告标题 + 金色分隔线 + 正文
    y = chart_h + _MERGE_GAP + _PAD
    tw = draw.textlength(title, font=f_title)
    draw.text(((_MERGE_W - tw) / 2, y), title, font=f_title, fill=GOLD)
    y += 48
    draw.line([(_PAD, y), (_MERGE_W - _PAD, y)], fill=GOLD_DIM, width=2)
    y += 16
    for ln in lines:
        _draw_text_mixed(img, draw, _PAD, y, ln, f_body, TEXT, emoji_font, emoji_kind, f_body.size)
        y += line_h
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
