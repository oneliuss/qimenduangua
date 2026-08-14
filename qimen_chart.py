# -*- coding: utf-8 -*-
"""
奇门遁甲九宫排盘图绘制器（Pillow 自绘，玄黑金风格）。
对外接口：render_paipan_chart(pp, out_path)。
"""
import os

from PIL import Image, ImageDraw, ImageFont

# ---------- 玄黑金配色 ----------
BG = (16, 18, 26)           # 深墨底
CELL_BG = (26, 30, 42)      # 宫格底
CENTER_BG = (32, 30, 26)    # 中宫底（略暖）
GOLD = (212, 175, 55)       # 主金
GOLD_DIM = (140, 118, 62)   # 暗金（内线）
TEXT = (232, 228, 218)      # 主文字
TEXT_DIM = (168, 164, 152)  # 次文字
RED = (198, 62, 56)         # 朱红（空/马章）

# ---------- 画布常量 ----------
WIDTH = 960
MARGIN = 24
HEADER_H = 210              # 标题栏高度
CELL_W, CELL_H = 296, 236   # 宫格尺寸
GRID_X = MARGIN             # 宫格区原点
GRID_Y = MARGIN + HEADER_H
LEGEND_H = 74
HEIGHT = GRID_Y + CELL_H * 3 + 16 + LEGEND_H + MARGIN

# 洛书排布（上南下北）：行=上中下，列=左中右
GRID_LAYOUT = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]

# ---------- 字体探测 ----------
_FONT_CANDIDATES = [
    # Windows
    ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"),
    ("C:/Windows/Fonts/simhei.ttf", None),
    ("C:/Windows/Fonts/simsun.ttc", None),
    # Linux
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
     "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", None),
    ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
     "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"),
    ("/usr/share/fonts/noto/NotoSansCJK-Bold.ttc",
     "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc"),
    ("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", None),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", None),
    ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", None),
    ("/usr/share/fonts/truetype/arphic/uming.ttc", None),
    ("/usr/share/fonts/truetype/arphic/ukai.ttc", None),
    ("/usr/share/fonts/opentype/source-han-sans/SourceHanSansSC-Regular.otf", None),
    # macOS extras
    ("/System/Library/Fonts/STHeiti Light.ttc", None),
    # macOS
    ("/System/Library/Fonts/PingFang.ttc", None),
]

# 扫描兜底：静态候选未命中时遍历常见字体目录（覆盖任意发行版路径）
_SCAN_DIRS = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
]
_SCAN_HINTS = [
    "cjk", "noto", "wqy", "zenhei", "microhei", "droid", "fallback",
    "uming", "ukai", "sourcehan", "simhei", "simsun", "msyh",
    "pingfang", "heiti", "songti", "kaiti", "fangsong",
]
_FONT_CACHE = None  # None=未扫描；[]=已扫描但未找到


def _scan_cjk_fonts():
    """扫描常见字体目录收集 CJK 字体路径（按关键字优先级排序，结果缓存）。"""
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE
    hits = []
    for d in _SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fn in files:
                low = fn.lower()
                if not low.endswith((".ttf", ".ttc", ".otf")):
                    continue
                if any(h in low for h in _SCAN_HINTS):
                    hits.append(os.path.join(root, fn))

    def _prio(p):
        low = os.path.basename(p).lower()
        for i, h in enumerate(_SCAN_HINTS):
            if h in low:
                return i
        return len(_SCAN_HINTS)

    hits.sort(key=lambda p: (_prio(p), p))
    _FONT_CACHE = hits
    return _FONT_CACHE


def find_cjk_font():
    """按平台候选顺序找第一个存在的中文字体（regular）。找不到返回 None。"""
    for _bold, regular in _FONT_CANDIDATES:
        if regular and os.path.exists(regular):
            return regular
    for bold, _regular in _FONT_CANDIDATES:
        if bold and os.path.exists(bold):
            return bold
    scanned = _scan_cjk_fonts()
    return scanned[0] if scanned else None


def load_font(size, bold=False):
    """加载中文字体；找不到任何候选字体抛 RuntimeError（由上层降级纯文字）。"""
    for b, r in _FONT_CANDIDATES:
        path = b if (bold and b) else r
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
        if r and os.path.exists(r):
            return ImageFont.truetype(r, size)
    scanned = _scan_cjk_fonts()
    if scanned:
        return ImageFont.truetype(scanned[0], size)
    raise RuntimeError("no CJK font found")


def _text_w(draw, s, font):
    return draw.textlength(s, font=font)


def _center_text(draw, cx, y, s, font, fill):
    draw.text((cx - _text_w(draw, s, font) / 2, y), s, font=font, fill=fill)


def _draw_header(img, draw, pp):
    """标题栏：插件名 + 问事/时间/四柱/遁局/直符直使空亡驿马。"""
    f_title = load_font(40, bold=True)
    f_line = load_font(22)
    cx = WIDTH / 2
    _center_text(draw, cx, MARGIN + 6, "奇 门 遁 甲 排 盘", f_title, GOLD)
    # 分隔线
    ly = MARGIN + 62
    draw.line([(MARGIN + 40, ly), (WIDTH - MARGIN - 40, ly)], fill=GOLD_DIM, width=2)
    y = ly + 12
    L = [
        f"问事：{pp['question']}",
        f"起局：{pp['datetime']}    四柱：{pp['year_gz']}年 {pp['month_gz']}月 {pp['day_gz']}日 {pp['hour_gz']}时",
        f"节气【{pp['jieqi']}】 {pp['yin_yang']}遁{pp['ju']}局 {pp['yuan']}    旬首【{pp['xun_shou']}/{pp['xun_yi']}】",
        f"直符【{pp['zhifu_star']}】  直使【{pp['zhishi_men']}】  "
        f"旬空【{'、'.join(pp['kong'])}】  驿马【{pp['ma'] or '无'}】",
    ]
    for line in L:
        draw.text((MARGIN + 12, y), line, font=f_line, fill=TEXT)
        y += 30


def _draw_badge(draw, cx, cy, ch):
    """朱红圆章角标（空/马）。"""
    r = 15
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED, outline=GOLD, width=1)
    f = load_font(18, bold=True)
    draw.text((cx - _text_w(draw, ch, f) / 2, cy - 11), ch, font=f, fill=(255, 244, 230))


def _draw_cell(draw, g, info, x0, y0):
    """单宫内容：宫数八卦方位 / 神 / 星 / 门 / 天盘干加地盘干 / 五行 / 标记。"""
    f_sm = load_font(18)
    f_md = load_font(24, bold=True)
    f_lg = load_font(30, bold=True)
    cx = x0 + CELL_W / 2
    if g == 5:
        # 中宫：寄坤二，简化显示
        _center_text(draw, cx, y0 + 70, f"中五宫", f_md, GOLD)
        _center_text(draw, cx, y0 + 116, f"（寄坤二宫）", f_sm, TEXT_DIM)
        _center_text(draw, cx, y0 + 152, f"地盘【{info['dipan'] or '—'}】", f_sm, TEXT)
        return
    # 左上：宫数·八卦·方位
    draw.text((x0 + 10, y0 + 8), f"{g} {info['bagua']}·{info['fang']}", font=f_sm, fill=TEXT_DIM)
    # 右上：五行
    wx = info["wx"]
    draw.text((x0 + CELL_W - 10 - _text_w(draw, wx, f_sm), y0 + 8), wx, font=f_sm, fill=TEXT_DIM)
    # 神盘（顶部居中，暗金）
    shen = info["shen"] or "—"
    _center_text(draw, cx, y0 + 40, shen, f_sm, GOLD_DIM)
    # 天盘星（主显示）
    _center_text(draw, cx, y0 + 72, info["tianpan_star"] or "—", f_lg, TEXT)
    # 人盘门（金色）
    _center_text(draw, cx, y0 + 122, info["men"] or "—", f_md, GOLD)
    # 天盘干加地盘干
    tp = info.get("tianpan_yi", "") or "—"
    dp = info["dipan"] or "—"
    _center_text(draw, cx, y0 + 168, f"{tp} 加 {dp}", f_md, TEXT)
    # 直符宫：金色高亮边框
    if info["is_zhifu_gong"]:
        draw.rectangle([x0 + 3, y0 + 3, x0 + CELL_W - 3, y0 + CELL_H - 3],
                       outline=GOLD, width=4)
        _draw_badge(draw, x0 + CELL_W - 26, y0 + 34, "符")
    # 空亡 / 驿马角标
    bx = x0 + 26
    if info["is_kong"]:
        _draw_badge(draw, bx, y0 + 34, "空")
        bx += 38
    if info["is_ma"]:
        _draw_badge(draw, bx, y0 + 34, "马")


def _draw_legend(draw):
    """底部图例行。"""
    f = load_font(18)
    y = GRID_Y + CELL_H * 3 + 16 + 14
    draw.line([(MARGIN + 40, y - 8), (WIDTH - MARGIN - 40, y - 8)], fill=GOLD_DIM, width=1)
    _center_text(draw, WIDTH / 2, y + 6,
                 "图例：上=南/离9 下=北/坎1 ｜ 宫内自上而下：神盘·天盘星·人盘门·天盘干加地盘干",
                 f, TEXT_DIM)
    _center_text(draw, WIDTH / 2, y + 34,
                 "金框=直符宫   红章 空=旬空  马=驿马   中五宫寄坤二",
                 f, TEXT_DIM)


def render_paipan_chart(pp, out_path):
    """绘制九宫排盘图（标题栏 + 九宫格 + 图例），保存 PNG 到 out_path，返回 out_path。"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    _draw_header(img, draw, pp)
    for r, row in enumerate(GRID_LAYOUT):
        for c, g in enumerate(row):
            x0 = GRID_X + c * (CELL_W + 8)
            y0 = GRID_Y + r * (CELL_H + 8)
            fill = CENTER_BG if g == 5 else CELL_BG
            draw.rectangle([x0, y0, x0 + CELL_W, y0 + CELL_H],
                           fill=fill, outline=GOLD_DIM, width=2)
            _draw_cell(draw, g, pp["gongs"][g], x0, y0)
    _draw_legend(draw)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
