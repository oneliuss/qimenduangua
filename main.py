# -*- coding: utf-8 -*-
"""
AstrBot 奇门遁甲断卦插件入口。
命令：
  /qimen <问题>       奇门遁甲起局断卦（时家奇门转盘法）
  /奇门 <问题>        同上
  /qm <问题>          同上
  /qm_yuce <问题>     预测：事体发展趋势与成败概率
  /qm_yunchou <问题>  运筹：择吉方位与行动策略
  /qm_fengshui <问题> 风水：环境方位与布局建议
  /qm_shiren <问题>   识人：性格才能与人际关系
  /qm_zhexue <问题>   哲学：易理启示与人生智慧
  /qm_all <问题>      综合分析（以上全部）
  /qm_help            查看使用说明
自然语言：
  含"奇门/遁甲/起局/排局"等意图即触发。
"""
import os
import sys
import re

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import qimen as QP
import qimen_data as QQ
import qimen_duangua as QG
import qimen_yuce as QY
import qimen_yunchou as QYC
import qimen_fengshui as QF
import qimen_shiren as QS
import qimen_zhexue as QZ
import qimen_zeri as QZE

import time

import qimen_chart as QC
import qimen_image as QI

_TEMP_DIR = os.path.join(_here, "temp")

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("astrbot_plugin_qimen")

from astrbot.api.star import Star, register
from astrbot.api.event import filter, AstrMessageEvent
import astrbot.api.message_components as Comp


def _safe_call(func, *args, **kwargs):
    """安全调用：若函数不接受 style 参数则自动退回。
    防止旧版模块文件未同步更新导致 TypeError 崩溃。
    """
    try:
        return func(*args, **kwargs)
    except TypeError:
        if "style" in kwargs:
            kwargs.pop("style")
            return func(*args, **kwargs)
        raise


# ===================== 自然语言触发 =====================
QIMEN_PATTERN = (
    r"奇门遁甲|奇门|遁甲|起局|排局|起个局|排个局|奇门局"
    r"|算局|测局|占局|卜局|问局"
)
_QIMEN_RE = re.compile(QIMEN_PATTERN)

# 各专项模块的自然语言触发关键词
YUCE_PATTERN = r"预测|前景|趋势|走势|成败|能不能成|能不能过|能不能行|前景如何|发展如何|未来如何|结果如何|能成吗|会成吗"
YUNCHOU_PATTERN = r"运筹|择吉|哪个方向|什么方向|往哪|去哪方向|选什么方向|出行方向|策略|行动方案|该怎么做|宜动|宜守|方位吉|哪个方位"
FENGSHUI_PATTERN = r"风水|布局|办公室|办公位|座位|朝向|环境|摆设|装修|选址|店铺位置|房子|宅|阴宅|阳宅|煞气|财位"
SHIREN_PATTERN = r"识人|看人|性格|人品|才能|合作伙伴|这个人怎样|对方|识人术|用人|下属|领导怎样|对象人品|合伙人"
ZHEXUE_PATTERN = r"哲学|易理|启示|感悟|道理|智慧|人生|修行|心法|开悟|启迪|哲理|天人合一|大道|天道|道法|悟道|修道|问道|论道|得道|道学|传道|求道|道可道|无为"

_YUCE_RE = re.compile(YUCE_PATTERN)
_YUNCHOU_RE = re.compile(YUNCHOU_PATTERN)
_FENGSHUI_RE = re.compile(FENGSHUI_PATTERN)
_SHIREN_RE = re.compile(SHIREN_PATTERN)
_ZHEXUE_RE = re.compile(ZHEXUE_PATTERN)

# 择日触发：择吉 + 时间段/节日/月份 + 事项 + "日子/哪天/几号"
ZERI_PATTERN = r"择吉|择日|选日子|选吉日|挑日子|适合.{0,8}的日子|哪天.{0,6}适合|几号.{0,6}适合|黄道吉日"
_ZERI_RE = re.compile(ZERI_PATTERN)

# 模块 -> (正则, 触发词列表) 映射，用于自然语言路由
_MODULE_PATTERNS = [
    ("zeri", _ZERI_RE),
    ("fengshui", _FENGSHUI_RE),
    ("shiren", _SHIREN_RE),
    ("yunchou", _YUNCHOU_RE),
    ("zhexue", _ZHEXUE_RE),
    ("yuce", _YUCE_RE),
]

# 命令名列表（用于在正则处理器中跳过命令消息，避免重复响应）
_COMMAND_NAMES = {"qimen", "qm", "奇门", "qm_help", "qm_yuce", "qm_yunchou", "qm_fengshui", "qm_shiren", "qm_zhexue", "qm_all", "qm_zeri"}

# 模块名 -> (配置项键, 模块中文名) 映射，用于开关控制
_MODULE_SWITCH = {
    "duangua": ("enable_duangua", "断卦"),
    "yuce": ("enable_yuce", "预测"),
    "yunchou": ("enable_yunchou", "运筹"),
    "fengshui": ("enable_fengshui", "风水"),
    "shiren": ("enable_shiren", "识人"),
    "zhexue": ("enable_zhexue", "哲学"),
    "zeri": ("enable_zeri", "择日"),
}

# 命令前缀字符（不同平台/配置可能使用不同前缀）
_CMD_PREFIXES = ("/", "／", "!", ".", "。", "#")


def _is_command_msg(msg):
    """判断消息是否为命令调用（而非自然语言），避免命令处理器与正则处理器重复响应。
    判据：
      1. 消息以命令前缀字符开头（/ ／ ! . 等）
      2. 或消息以命令名开头且紧跟空格/换行/结尾（如 "qimen xxx"），但不含前缀
         注意：需区分 "奇门 xxx"（命令）与 "奇门遁甲 xxx"（自然语言）
    """
    stripped = msg.lstrip()
    if not stripped:
        return False
    # 判据1：前缀字符开头
    if stripped[0] in _CMD_PREFIXES:
        return True
    # 判据2：命令名 + 空格/结尾（无前缀的情况）
    for cmd in _COMMAND_NAMES:
        if stripped.lower().startswith(cmd):
            after = stripped[len(cmd):len(cmd) + 1]
            if after in (" ", "　", "\t", "\n", "\r", ""):
                return True
    return False


_FILLER_PREFIX = re.compile(
    r"^(?:帮我|麻烦|麻烦你|请|能不能|可以|能不能帮我|能帮我|给我|来|我想|我要|帮我来|想|要|麻烦帮我|请你)+"
)
_AFTER_PREFIX = re.compile(
    r"^(?:一下|看一看|看看|看下|问一问|问问|问下|测一测|测测|算一算|算算|"
    r"呗|吧|啊|呀|啦|了|[:：，,、\s])+"
)
_SEPS = " :：,，、。.!！?？\t\n\r"


def _extract_question(msg):
    m = _QIMEN_RE.search(msg)
    if not m:
        return msg.strip(_SEPS)
    before = msg[:m.start()]
    after = msg[m.end():]
    before = _FILLER_PREFIX.sub("", before).strip(_SEPS)
    after = _AFTER_PREFIX.sub("", after).strip(_SEPS)
    if after:
        return after
    if before:
        return before
    return ""


def _extract_question_generic(msg, pattern_re):
    """通用问题提取：剥离触发短语与语气词，返回真正的问事内容。"""
    m = pattern_re.search(msg)
    if not m:
        return msg.strip(_SEPS)
    before = msg[:m.start()]
    after = msg[m.end():]
    before = _FILLER_PREFIX.sub("", before).strip(_SEPS)
    after = _AFTER_PREFIX.sub("", after).strip(_SEPS)
    if after:
        return after
    if before:
        return before
    return ""


def _route_module(msg):
    """根据自然语言内容判断应走哪个专项模块。
    返回模块名('zeri'/'yuce'/'yunchou'/'fengshui'/'shiren'/'zhexue')或 None。
    优先匹配特征最鲜明的模块。
    """
    # 优先级：择日 > 风水 > 识人 > 运筹 > 哲学 > 预测（预测最泛，放最后）
    priority = ["zeri", "fengshui", "shiren", "yunchou", "zhexue", "yuce"]
    module_re_map = {
        "zeri": _ZERI_RE,
        "yuce": _YUCE_RE,
        "yunchou": _YUNCHOU_RE,
        "fengshui": _FENGSHUI_RE,
        "shiren": _SHIREN_RE,
        "zhexue": _ZHEXUE_RE,
    }
    for mod in priority:
        if module_re_map[mod].search(msg):
            return mod
    return None


# ===================== 奇门遁甲报告 =====================
_QM_GRID = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]


def _qm_cell(info):
    g = info["gong"]
    star = info["tianpan_star"] or "-"
    men = info["men"] or "-"
    shen = info["shen"] or "-"
    yi = info["dipan"] or "-"
    tags = []
    if info["is_zhifu_gong"]:
        tags.append("符")
    if info["is_kong"]:
        tags.append("空")
    if info["is_ma"]:
        tags.append("马")
    tag = "".join(tags)
    tp_yi = info.get("tianpan_yi", "") or ""
    return f"[{g}{info['bagua']}{tag}] {star}/{men}\n      {shen}·{tp_yi}加{yi}{info['wx']}"


def build_qimen_report(pp, jd, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 🐉 奇门遁甲 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 起局时间：{pp['datetime']}")
    L.append(f"📜 四柱：{pp['year_gz']}年 {pp['month_gz']}月 {pp['day_gz']}日 {pp['hour_gz']}时")
    L.append(f"    节气【{pp['jieqi']}】 {pp['yin_yang']}遁{pp['ju']}局 {pp['yuan']}  "
             f"旬首【{pp['xun_shou']}/{pp['xun_yi']}】")
    L.append(f"    直符【{pp['zhifu_star']}】在{QQ.GONG[pp['zhifu_gong']][0]}宫  "
             f"直使【{pp['zhishi_men']}】  旬空【{'、'.join(pp['kong'])}】  "
             f"驿马【{pp['ma'] or '无'}】")
    L.append("")

    L.append("【九宫盘】(按九宫方位：上=南/离9, 下=北/坎1)")
    for row in _QM_GRID:
        cells = []
        for g in row:
            info = pp["gongs"][g]
            cells.append(_qm_cell(info))
        L.append("  ".join(cells))
        L.append("")
    L.append("图例：[宫数·八卦] 天盘星/人盘门 ，神盘·天盘干加地盘干(宫五行)；符=直符宫 空=空亡 马=驿马")
    L.append("")

    L.append("━━━━━━━━━━ 🔮 古法断卦 ━━━━━━━━━━")
    if jd["use_zhifu"]:
        L.append("用神：所问之事未明，取【直符】为用")
    else:
        yong = jd["yong"]
        yg = jd["yong_gong"]
        if yg:
            L.append(f"用神【{yong}】({jd['yong_kind']}盘) -> {QQ.GONG[yg][0]}宫({QQ.GONG[yg][2]})")
        else:
            L.append(f"用神【{yong}】未显于盘")
    L.append(f"吉凶：{jd['emoji']} 【{jd['level']}】(评分 {jd['score']:+d})")
    L.append("")

    L.append("【判语】")
    for a in jd["analysis"]:
        L.append(f"  · {a}")
    L.append("")
    if jd.get("zhuke"):
        L.append(f"【主客】{jd['zhuke']}")
        L.append("")
    L.append(f"【应期】{jd['yingqi']}")
    L.append("")
    L.append("【实操建议】")
    L.append(jd["advice"])
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 易理乃古人经验之归纳，仅供参考，万事仍需以现实为依归，正心正行方为上策。")
    return "\n".join(L)


# ===================== 预测报告 =====================
def build_yuce_report(pp, result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 📊 奇门预测 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 {pp['datetime']}  {pp['yin_yang']}遁{pp['ju']}局{pp['yuan']}")
    L.append("")
    L.append(f"【总体趋势】{result['trend']}")
    L.append(f"【成败概率】{result['success_rate']}")
    L.append("")
    L.append("【发展阶段】")
    for p in result["phases"]:
        L.append(f"  · {p}")
    L.append("")
    L.append(f"【应期判断】{result['timing']}")
    L.append("")
    if result["risks"]:
        L.append("【风险预警】")
        for r in result["risks"]:
            L.append(f"  ⚠ {r}")
        L.append("")
    L.append("【预测总结】")
    L.append(result["summary"])
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 预测仅供参考，未来在于人为，正心正行可改运势。")
    return "\n".join(L)


# ===================== 运筹报告 =====================
def build_yunchou_report(pp, result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 🧭 奇门运筹 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 {pp['datetime']}  {pp['yin_yang']}遁{pp['ju']}局{pp['yuan']}")
    L.append("")
    L.append(f"【最佳方位】{result['best_direction']}")
    L.append(f"【择吉时机】{result['best_timing']}")
    L.append(f"【主客攻守】{result['posture']}")
    L.append("")
    L.append("【运筹策略】")
    L.append(result["strategy"])
    L.append("")
    L.append("【行动建议】")
    for a in result["actions"]:
        L.append(f"  ✓ {a}")
    L.append("")
    if result["avoid"]:
        L.append("【宜避之事】")
        for a in result["avoid"]:
            L.append(f"  ✗ {a}")
        L.append("")
    if show_disclaimer:
        L.append("⚠️ 运筹之妙在乎因地制宜，奇门指路仍需人为，不可拘泥。")
    return "\n".join(L)


# ===================== 风水报告 =====================
def build_fengshui_report(pp, result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 🏠 奇门风水 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 {pp['datetime']}  {pp['yin_yang']}遁{pp['ju']}局{pp['yuan']}")
    L.append("")
    L.append(f"【环境总评】{result['environment']}")
    L.append("")
    L.append(f"【关键方位】{result['key_sector']}")
    L.append("")
    if result["auspicious_sectors"]:
        L.append("【吉方宜用】")
        for direction, reason in result["auspicious_sectors"]:
            L.append(f"  ✓ {direction}：{reason}")
        L.append("")
    if result["inauspicious_sectors"]:
        L.append("【凶方宜避】")
        for direction, reason in result["inauspicious_sectors"]:
            L.append(f"  ✗ {direction}：{reason}")
        L.append("")
    L.append("【布局建议】")
    for a in result["layout_advice"]:
        L.append(f"  · {a}")
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 风水布局须结合实地形势，奇门方位仅供参考。")
    return "\n".join(L)


# ===================== 识人报告 =====================
def build_shiren_report(pp, result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 👤 奇门识人 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 {pp['datetime']}  {pp['yin_yang']}遁{pp['ju']}局{pp['yuan']}")
    L.append("")
    L.append(f"【性格特质】{result['personality']}")
    L.append("")
    if result["talents"]:
        L.append("【才能优势】")
        for t in result["talents"]:
            L.append(f"  ✓ {t}")
        L.append("")
    if result["weaknesses"]:
        L.append("【短板不足】")
        for w in result["weaknesses"]:
            L.append(f"  ✗ {w}")
        L.append("")
    L.append(f"【人际关系】{result['relationships']}")
    L.append(f"【适合领域】{result['career_fit']}")
    L.append("")
    L.append("【用人之道】")
    L.append(result["advice"])
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 识人须观其言行久长，奇门参考而已，勿以一局定人。")
    return "\n".join(L)


# ===================== 哲学报告 =====================
def build_zhexue_report(pp, result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 📜 奇门哲理 ━━━━━━━━━━")
    L.append(f"📡 问事：{pp['question']}")
    L.append(f"🕐 {pp['datetime']}  {pp['yin_yang']}遁{pp['ju']}局{pp['yuan']}")
    L.append("")
    L.append(f"【核心易理】{result['principle']}")
    L.append("")
    L.append("【格局之智】")
    L.append(result["pattern_wisdom"])
    L.append("")
    L.append(f"【阴阳之道】{result['yin_yang']}")
    L.append(f"【时位之机】{result['timing_wisdom']}")
    L.append("")
    L.append("【人生启示】")
    L.append(result["life_lesson"])
    L.append("")
    quote = result.get("quote", "")
    L.append(f"『 {quote} 』")
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 易理无穷，贵在体悟践行，知行合一方为真智慧。")
    return "\n".join(L)


# ===================== 择日报告 =====================
def build_zeri_report(result, show_disclaimer=True):
    L = []
    L.append("━━━━━━━━━━ 📅 奇门择日 ━━━━━━━━━━")
    if not result.get("time_range"):
        L.append(f"📡 事项：{result.get('event', '未明事项')}")
        L.append("")
        L.append(result["summary"])
        if show_disclaimer:
            L.append("")
            L.append("⚠️ 择日须明确时间段与事项，方可逐日推演。")
        return "\n".join(L)
    L.append(f"📡 事项：{result['event']}（用神：{result['yong']}）")
    L.append(f"🕐 时间范围：{result['time_range']}")
    L.append("")
    if result["good_days"]:
        L.append("【推荐吉日】")
        for i, (date, weekday, hour, score, reasons) in enumerate(result["good_days"], 1):
            star = "⭐" if i == 1 else "  "
            L.append(f"  {star} {date}{weekday} {hour}  评分{score:+d}")
            L.append(f"      理由：{reasons}")
        L.append("")
    else:
        L.append("【推荐吉日】未找到吉日")
        L.append("")
    if result["bad_days"]:
        L.append("【宜避之日】")
        for date, reasons in result["bad_days"]:
            L.append(f"  ✗ {date}  {reasons}")
        L.append("")
    L.append("【择日总结】")
    L.append(result["summary"])
    L.append("")
    L.append("【择日建议】")
    L.append(result["advice"])
    if show_disclaimer:
        L.append("")
        L.append("⚠️ 择日为古人经验归纳，实际还须结合个人八字与实情综合判断。")
    return "\n".join(L)


@register(
    "astrbot_plugin_qimen",
    "qimen_dev",
    "奇门遁甲断卦：起局排盘，判吉凶、预测、运筹、风水、识人、哲理、择日",
    "1.1.1",
    "",
)
class QimenPlugin(Star):
    def __init__(self, context, config):
        super().__init__(context)
        self.config = config or {}

    def _opt(self, key, default):
        v = self.config.get(key, default)
        return v if v not in (None, "") else default

    def _module_enabled(self, module):
        """检查某模块是否在配置中启用。
        未登记在 _MODULE_SWITCH 的模块默认始终启用。
        """
        entry = _MODULE_SWITCH.get(module)
        if entry is None:
            return True
        config_key, _name = entry
        return bool(self._opt(config_key, True))

    def _module_disabled_hint(self, module):
        """返回模块被关闭时的提示文案。"""
        entry = _MODULE_SWITCH.get(module)
        name = entry[1] if entry else module
        return f"⚠️【{name}】模块已被管理员关闭，如需使用请在插件配置中开启。"

    async def _send_result(self, event, report_text, pp=None, title="奇门遁甲"):
        """按 output_mode 输出：text 纯文字 / image 一张合并图（无排盘时为报告图） / both 合并图+文。
        图片任何环节失败自动降级，保证用户总能收到结果。
        """
        mode = str(self._opt("output_mode", "text")).lower()
        if mode not in ("text", "image", "both"):
            mode = "text"
        if mode == "text":
            return event.plain_result(report_text)

        # 1) 九宫排盘图（仅在有排盘数据且开关开启时）
        chart_path = None
        if pp is not None and bool(self._opt("enable_chart_image", True)):
            try:
                os.makedirs(_TEMP_DIR, exist_ok=True)
                chart_path = os.path.join(
                    _TEMP_DIR, f"qimen_chart_{int(time.time() * 1000)}.png")
                QC.render_paipan_chart(pp, chart_path)
            except Exception as e:
                logger.warning(f"九宫排盘图生成失败，已跳过：{e}")
                chart_path = None
        # 2) 有排盘图 → 合并图；无排盘图 → 独立报告图（本地 Pillow）
        image_path = None
        if chart_path:
            try:
                os.makedirs(_TEMP_DIR, exist_ok=True)
                merged_path = os.path.join(
                    _TEMP_DIR, f"qimen_merged_{int(time.time() * 1000)}.png")
                QI.render_merged_image(chart_path, report_text, title, merged_path)
                image_path = merged_path
                try:
                    os.remove(chart_path)  # 合并成功后清理中间文件
                except OSError:
                    pass
            except Exception as e:
                logger.warning(f"合并图生成失败，降级为排盘图：{e}")
                image_path = chart_path
        else:
            try:
                os.makedirs(_TEMP_DIR, exist_ok=True)
                report_path = os.path.join(
                    _TEMP_DIR, f"qimen_report_{int(time.time() * 1000)}.png")
                QI.render_text_local(report_text, title, report_path)
                image_path = report_path
            except Exception as e:
                logger.warning(f"报告图生成失败，已跳过：{e}")
        # 3) 最终兜底：无图可发时回退纯文本
        if not image_path:
            return event.plain_result(report_text)
        chain = [Comp.Image.fromFileSystem(image_path)]
        if mode == "both":
            chain.append(Comp.Plain("\n" + report_text))
        return event.chain_result(chain)

    @filter.command("qimen")
    async def cmd_qimen(self, event: AstrMessageEvent):
        """奇门遁甲起局断卦。"""
        if not self._module_enabled("duangua"):
            yield event.plain_result(self._module_disabled_hint("duangua"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result(
                "请输入你的问题，例如：\n"
                "  /qimen 这笔生意能不能做\n"
                "  /qimen 明天出行顺利吗\n"
                "  /qimen 近期财运如何"
            )
            return
        yield await self._do_divine(event, question)

    @filter.regex(ZERI_PATTERN + "|" + YUCE_PATTERN + "|" + YUNCHOU_PATTERN + "|" + FENGSHUI_PATTERN + "|" + SHIREN_PATTERN + "|" + ZHEXUE_PATTERN)
    async def natural_module(self, event: AstrMessageEvent):
        """自然语言：根据内容自动路由到择日/预测/运筹/风水/识人/哲学模块。"""
        msg = event.message_str or ""
        if _is_command_msg(msg):
            return
        module = _route_module(msg)
        if not module:
            return
        # 检查模块开关
        if not self._module_enabled(module):
            yield event.plain_result(self._module_disabled_hint(module))
            return
        # 择日模块特殊处理：直接用原始消息作为问题（需要保留时间段和事项信息）
        if module == "zeri":
            question = msg.strip(_SEPS)
            # 剥离"择吉"等触发词
            question = _ZERI_RE.sub("", question).strip(_SEPS)
            question = _FILLER_PREFIX.sub("", question).strip(_SEPS)
            question = _AFTER_PREFIX.sub("", question).strip(_SEPS)
            if not question:
                question = msg.strip(_SEPS)
            yield await self._do_zeri(event, question)
            return
        # 其他模块用对应的正则提取问题
        module_re_map = {
            "yuce": _YUCE_RE,
            "yunchou": _YUNCHOU_RE,
            "fengshui": _FENGSHUI_RE,
            "shiren": _SHIREN_RE,
            "zhexue": _ZHEXUE_RE,
        }
        question = _extract_question_generic(msg, module_re_map[module])
        if not question:
            hints = {
                "yuce": "帮我预测下 这笔生意的前景如何",
                "yunchou": "明天出行 哪个方向好",
                "fengshui": "新办公室 布局建议",
                "shiren": "帮我识人 我的合作伙伴怎样",
                "zhexue": "这件事给我什么启示",
            }
            yield event.plain_result(
                f"检测到你想用奇门{ {'yuce':'预测','yunchou':'运筹','fengshui':'风水','shiren':'识人','zhexue':'哲学'}[module] }功能，但没看到具体问题~\n"
                f"可以这样问我：\n  {hints[module]}"
            )
            return
        yield await self._do_module(event, question, module)

    @filter.command("奇门")
    async def cmd_qimen_cn(self, event: AstrMessageEvent):
        if not self._module_enabled("duangua"):
            yield event.plain_result(self._module_disabled_hint("duangua"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/奇门 这次面试能成吗")
            return
        yield await self._do_divine(event, question)

    @filter.command("qm")
    async def cmd_qm(self, event: AstrMessageEvent):
        if not self._module_enabled("duangua"):
            yield event.plain_result(self._module_disabled_hint("duangua"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm 近期工作有着落吗")
            return
        yield await self._do_divine(event, question)

    @filter.regex(QIMEN_PATTERN)
    async def natural_qimen(self, event: AstrMessageEvent):
        """自然语言：含奇门/遁甲/起局等意图即触发。"""
        msg = event.message_str or ""
        # 命令消息交给 command handler 处理，避免重复响应
        if _is_command_msg(msg):
            return
        if not self._module_enabled("duangua"):
            yield event.plain_result(self._module_disabled_hint("duangua"))
            return
        question = _extract_question(msg)
        if not question:
            yield event.plain_result(
                "🐉 检测到你想用奇门遁甲，但没看到具体问题~\n"
                "可以这样问我：\n"
                "  奇门遁甲 测下这笔生意能不能做\n"
                "  帮我起个奇门局 明天出行顺利吗\n"
                "  用遁甲看看近期财运"
            )
            return
        yield await self._do_divine(event, question)

    @filter.command("qm_help")
    async def cmd_help(self, event: AstrMessageEvent):
        yield event.plain_result(
            "🐉 奇门遁甲断卦插件 说明\n"
            "==============\n"
            "【断卦】\n"
            "  /qimen <问题>     起局断卦（吉凶判断+建议）\n"
            "  /奇门 <问题>      同上\n"
            "  /qm <问题>        同上\n"
            "【专项分析】\n"
            "  /qm_yuce <问题>   预测：事体发展趋势与成败概率\n"
            "  /qm_yunchou <问题> 运筹：择吉方位与行动策略\n"
            "  /qm_fengshui <问题> 风水：环境方位与布局建议\n"
            "  /qm_shiren <问题> 识人：性格才能与人际关系\n"
            "  /qm_zhexue <问题>  哲学：易理启示与人生智慧\n"
            "  /qm_zeri <问题>   择日：在指定时间段内逐日推演找吉日\n"
            "  /qm_all <问题>    综合：以上全部模块一网打尽\n"
            "==============\n"
            "自然语言（无需斜杠）：\n"
            "  断卦：奇门遁甲 测下这笔生意能不能做\n"
            "  预测：帮我预测下 这笔生意的前景如何\n"
            "  运筹：明天出行 哪个方向好\n"
            "  风水：新办公室 布局建议\n"
            "  识人：帮我识人 我的合作伙伴怎样\n"
            "  哲学：这件事给我什么启示\n"
            "  择日：择吉 国庆节期间适合结婚的日子\n"
            "==============\n"
            "用法举例：\n"
            "  /qimen 这笔投资能做吗\n"
            "  /qm_yuce 这笔生意的前景如何\n"
            "  /qm_yunchou 明天出行哪个方向好\n"
            "  /qm_fengshui 新办公室布局建议\n"
            "  /qm_shiren 我的合作伙伴怎样\n"
            "  /qm_zhexue 这件事给我什么启示\n"
            "  /qm_zeri 八月份适合开业的日子\n"
            "  /qm_all 这笔投资能做吗\n"
            "==============\n"
            "说明：\n"
            "1. 按时辰节气定局（阴阳遁+上中下元），排天地人神四盘。\n"
            "2. 断卦含格局吉凶、十干克应、门宫生克、主客关系、空亡转宫等。\n"
            "3. 五大专项模块各有侧重，可单独使用或综合分析。\n"
            "4. 依古法与现代体系（《御定奇门宝鉴》《神奇之门》等）。\n"
            "⚠️ 易理仅供参考，请理性看待。"
        )

    @filter.command("qm_yuce")
    async def cmd_yuce(self, event: AstrMessageEvent):
        if not self._module_enabled("yuce"):
            yield event.plain_result(self._module_disabled_hint("yuce"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_yuce 这笔生意的前景如何")
            return
        yield await self._do_module(event, question, "yuce")

    @filter.command("qm_yunchou")
    async def cmd_yunchou(self, event: AstrMessageEvent):
        if not self._module_enabled("yunchou"):
            yield event.plain_result(self._module_disabled_hint("yunchou"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_yunchou 明天出行哪个方向好")
            return
        yield await self._do_module(event, question, "yunchou")

    @filter.command("qm_fengshui")
    async def cmd_fengshui(self, event: AstrMessageEvent):
        if not self._module_enabled("fengshui"):
            yield event.plain_result(self._module_disabled_hint("fengshui"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_fengshui 新办公室布局建议")
            return
        yield await self._do_module(event, question, "fengshui")

    @filter.command("qm_shiren")
    async def cmd_shiren(self, event: AstrMessageEvent):
        if not self._module_enabled("shiren"):
            yield event.plain_result(self._module_disabled_hint("shiren"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_shiren 我的合作伙伴怎样")
            return
        yield await self._do_module(event, question, "shiren")

    @filter.command("qm_zhexue")
    async def cmd_zhexue(self, event: AstrMessageEvent):
        if not self._module_enabled("zhexue"):
            yield event.plain_result(self._module_disabled_hint("zhexue"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_zhexue 这件事给我什么启示")
            return
        yield await self._do_module(event, question, "zhexue")

    @filter.command("qm_all")
    async def cmd_all(self, event: AstrMessageEvent):
        question = event.message_str.strip()
        if not question:
            yield event.plain_result("请输入问题，例如：/qm_all 这笔投资能做吗")
            return
        yield await self._do_module(event, question, "all")

    @filter.command("qm_zeri")
    async def cmd_zeri(self, event: AstrMessageEvent):
        """择日：在指定时间段内逐日推演找出吉日。"""
        if not self._module_enabled("zeri"):
            yield event.plain_result(self._module_disabled_hint("zeri"))
            return
        question = event.message_str.strip()
        if not question:
            yield event.plain_result(
                "请输入择日问题，例如：\n"
                "  /qm_zeri 国庆节期间适合结婚的日子\n"
                "  /qm_zeri 八月份适合开业的日子\n"
                "  /qm_zeri 下个月适合搬家的日子"
            )
            return
        yield await self._do_zeri(event, question)

    async def _do_divine(self, event: AstrMessageEvent, question: str):
        """奇门遁甲起局断卦，返回 plain_result 文本。"""
        show_disclaimer = self._opt("show_disclaimer", True)
        advice_style = self._opt("advice_style", "modern")
        try:
            pp = QP.qimen_paipan(question)
            jd = _safe_call(QG.judge, pp, style=advice_style)
            report = build_qimen_report(pp, jd, show_disclaimer=bool(show_disclaimer))
            return await self._send_result(event, report, pp=pp, title="奇门遁甲·断卦")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return event.plain_result(f"奇门起局出错：{e}\n{tb}")

    async def _do_zeri(self, event: AstrMessageEvent, question: str):
        """择日：在指定时间段内逐日推演，返回 plain_result 文本。"""
        show_disclaimer = self._opt("show_disclaimer", True)
        try:
            result = QZE.zeri(question)
            report = build_zeri_report(result, show_disclaimer=bool(show_disclaimer))
            return await self._send_result(event, report, pp=None, title="奇门择日")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return event.plain_result(f"择日出错：{e}\n{tb}")

    async def _do_module(self, event: AstrMessageEvent, question: str, module: str):
        """执行指定分析模块，返回 plain_result 文本。"""
        show_disclaimer = self._opt("show_disclaimer", True)
        advice_style = self._opt("advice_style", "modern")
        try:
            pp = QP.qimen_paipan(question)
            if module == "all":
                # 按开关过滤要执行的模块（保持 断卦->预测->运筹->风水->识人->哲学 顺序）
                all_modules = ["duangua", "yuce", "yunchou", "fengshui", "shiren", "zhexue"]
                enabled_modules = [m for m in all_modules if self._module_enabled(m)]
                if not enabled_modules:
                    return event.plain_result("⚠️ 所有分析模块均已被关闭，无法生成综合分析。")
                parts = []
                for idx, mod in enumerate(enabled_modules):
                    is_last = (idx == len(enabled_modules) - 1)
                    part_disclaimer = bool(show_disclaimer) if is_last else False
                    if mod == "duangua":
                        r = _safe_call(QG.judge, pp, style=advice_style)
                        parts.append(build_qimen_report(pp, r, show_disclaimer=part_disclaimer))
                    elif mod == "yuce":
                        r = _safe_call(QY.yuce, pp, style=advice_style)
                        parts.append(build_yuce_report(pp, r, show_disclaimer=part_disclaimer))
                    elif mod == "yunchou":
                        r = _safe_call(QYC.yunchou, pp, style=advice_style)
                        parts.append(build_yunchou_report(pp, r, show_disclaimer=part_disclaimer))
                    elif mod == "fengshui":
                        r = _safe_call(QF.fengshui, pp, style=advice_style)
                        parts.append(build_fengshui_report(pp, r, show_disclaimer=part_disclaimer))
                    elif mod == "shiren":
                        r = _safe_call(QS.shiren, pp, style=advice_style)
                        parts.append(build_shiren_report(pp, r, show_disclaimer=part_disclaimer))
                    elif mod == "zhexue":
                        r = _safe_call(QZ.zhexue, pp, style=advice_style)
                        parts.append(build_zhexue_report(pp, r, show_disclaimer=part_disclaimer))
                report = "\n\n".join(parts)
                return await self._send_result(event, report, pp=pp, title="奇门遁甲·综合")
            elif module == "yuce":
                result = _safe_call(QY.yuce, pp, style=advice_style)
                report = build_yuce_report(pp, result, show_disclaimer=bool(show_disclaimer))
            elif module == "yunchou":
                result = _safe_call(QYC.yunchou, pp, style=advice_style)
                report = build_yunchou_report(pp, result, show_disclaimer=bool(show_disclaimer))
            elif module == "fengshui":
                result = _safe_call(QF.fengshui, pp, style=advice_style)
                report = build_fengshui_report(pp, result, show_disclaimer=bool(show_disclaimer))
            elif module == "shiren":
                result = _safe_call(QS.shiren, pp, style=advice_style)
                report = build_shiren_report(pp, result, show_disclaimer=bool(show_disclaimer))
            elif module == "zhexue":
                result = _safe_call(QZ.zhexue, pp, style=advice_style)
                report = build_zhexue_report(pp, result, show_disclaimer=bool(show_disclaimer))
            else:
                return event.plain_result(f"未知模块：{module}")
            _titles = {"yuce": "奇门预测", "yunchou": "奇门运筹",
                       "fengshui": "奇门风水", "shiren": "奇门识人", "zhexue": "奇门哲理"}
            return await self._send_result(
                event, report, pp=pp, title=_titles.get(module, "奇门遁甲"))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return event.plain_result(f"分析出错：{e}\n{tb}")
