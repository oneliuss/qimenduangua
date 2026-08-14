# -*- coding: utf-8 -*-
"""
报告文本转图片管线。
优先级：AstrBot html_render（网络 Jinja2 渲染）-> Pillow 本地排版 -> None（由调用方降级纯文本）。
"""
import os

from PIL import Image, ImageDraw

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


def render_text_local(report_text, title, out_path, width=_IMG_W):
    """把报告文本用 Pillow 排成玄黑金长图。返回 out_path。width：画布宽度，默认 840。"""
    if not find_cjk_font():
        raise RuntimeError("no CJK font found")
    f_title = load_font(34, bold=True)
    f_body = load_font(22)
    probe = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(probe)
    max_w = width - _PAD * 2
    lines = []
    for raw in report_text.split("\n"):
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
        draw.text((_PAD, y), ln, font=f_body, fill=TEXT)
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
    probe = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(probe)
    max_w = _MERGE_W - _PAD * 2
    lines = []
    for raw in report_text.split("\n"):
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
        draw.text((_PAD, y), ln, font=f_body, fill=TEXT)
        y += line_h
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
