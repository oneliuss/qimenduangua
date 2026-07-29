# -*- coding: utf-8 -*-
"""
奇门遁甲择日模块：在指定时间范围内逐日起局，找出适合特定事项的吉日。
古法依据：《御定奇门宝鉴》《奇门法窍》《神奇之门》。
核心逻辑：解析时间段 -> 解析事项 -> 遍历每日吉时起局 -> 用事项用神评分 -> 排序输出吉日。
"""
import re
import datetime
import calendar

try:
    from . import qimen as QP
    from . import qimen_data as Q
    from . import qimen_duangua as QG
    from . import qimen_yunchou as QYC
except ImportError:
    import qimen as QP
    import qimen_data as Q
    import qimen_duangua as QG
    import qimen_yunchou as QYC


# ===================== 时间段解析 =====================
# 节日 -> (月, 日, 持续天数)
_FESTIVALS = {
    "元旦": (1, 1, 1), "春节": (1, 1, 7), "清明": (4, 4, 3),
    "劳动节": (5, 1, 5), "五一": (5, 1, 5),
    "端午节": (6, 10, 3), "端午": (6, 10, 3),
    "国庆节": (10, 1, 7), "国庆": (10, 1, 7),
    "中秋": (9, 15, 3), "中秋节": (9, 15, 3),
    "重阳": (10, 11, 1), "冬至": (12, 22, 1),
}

# 月份中文数字映射
_MONTH_CN = {
    "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
    "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12,
    "1月": 1, "2月": 2, "3月": 3, "4月": 4, "5月": 5, "6月": 6,
    "7月": 7, "8月": 8, "9月": 9, "10月": 10, "11月": 11, "12月": 12,
    "正月": 1, "腊月": 12, "冬月": 11,
}


def parse_time_range(question, now=None):
    """从问题中解析时间段，返回 (start_date, end_date, 描述)。
    返回 None 表示未识别到时间段。
    """
    if now is None:
        now = datetime.datetime.now()
    year = now.year

    # 1. 节日
    for name, (m, d, days) in _FESTIVALS.items():
        if name in question:
            start = datetime.date(year, m, d)
            end = start + datetime.timedelta(days=days - 1)
            return start, end, f"{year}年{name}（{m}月{d}日至{end.month}月{end.day}日）"

    # 2. 某月
    for cn, m in _MONTH_CN.items():
        if cn in question:
            last_day = calendar.monthrange(year, m)[1]
            start = datetime.date(year, m, 1)
            end = datetime.date(year, m, last_day)
            return start, end, f"{year}年{m}月"

    # 3. "下个月"
    if "下个月" in question or "下月" in question:
        m = now.month + 1
        y = year
        if m > 12:
            m = 1
            y += 1
        last_day = calendar.monthrange(y, m)[1]
        start = datetime.date(y, m, 1)
        end = datetime.date(y, m, last_day)
        return start, end, f"{y}年{m}月"

    # 4. "本月"/"这个月"
    if "本月" in question or "这个月" in question:
        m = now.month
        last_day = calendar.monthrange(year, m)[1]
        start = datetime.date(year, m, 1)
        end = datetime.date(year, m, last_day)
        return start, end, f"{year}年{m}月"

    # 5. "本周"
    if "本周" in question or "这周" in question:
        monday = now.date() - datetime.timedelta(days=now.weekday())
        sunday = monday + datetime.timedelta(days=6)
        return monday, sunday, f"本周（{monday.month}月{monday.day}日至{sunday.month}月{sunday.day}日）"

    return None


# ===================== 事项解析 =====================
# 事项 -> (用神, 用神类型, 事项描述)
_EVENT_MAP = [
    (["结婚", "嫁娶", "婚嫁", "办婚礼", "领证", "订婚"], "六合", "婚姻嫁娶"),
    (["开业", "开张", "开店", "开市", "新店"], "生门", "开业经商"),
    (["搬家", "入宅", "迁居", "搬房", "入伙", "乔迁"], "生门", "搬家入宅"),
    (["出行", "出差", "远行", "旅游", "赴任"], "开门", "出行远行"),
    (["签约", "签合同", "签协议"], "六合", "签约合作"),
    (["投资", "理财", "入股"], "生门", "投资求财"),
    (["求职", "面试", "找工作"], "开门", "求职谋职"),
    (["考试", "升学", "科举", "答辩"], "景门", "考试升学"),
    (["动土", "开工", "建房", "装修", "施工"], "开门", "动土兴建"),
    (["诉讼", "官司", "起诉", "开庭"], "惊门", "诉讼官非"),
    (["求医", "看病", "手术", "住院"], "天心", "求医问药"),
    (["提亲", "说媒", "相亲"], "六合", "提亲相亲"),
    (["安葬", "下葬", "出殡"], "死门", "安葬之事"),
    (["提车", "买车", "购车"], "生门", "购置物品"),
    (["入职", "报到", "上任"], "开门", "入职上任"),
]


def parse_event(question):
    """从问题中解析事项类型。返回 (用神, 事项描述) 或 None。"""
    for kws, yong, desc in _EVENT_MAP:
        for kw in kws:
            if kw in question:
                return yong, desc
    return None


# ===================== 逐日评分 =====================
# 每天扫描的时辰（子=0, 卯=5, 午=11, 酉=17 等，取3个代表时辰）
_SCAN_HOURS = [5, 11, 17]  # 卯时、午时、酉时


def _scan_day(date, yong, question):
    """对某一天的多个时辰起局，用指定用神评分。返回 (日期, 最高分, 最佳时辰, 最佳局)。"""
    best_score = -999
    best_hour = None
    best_pp = None
    for hour in _SCAN_HOURS:
        dt = datetime.datetime(date.year, date.month, date.day, hour, 0)
        try:
            pp = QP.qimen_paipan(question, dt=dt)
            score = _eval_day(pp, yong)
            if score > best_score:
                best_score = score
                best_hour = hour
                best_pp = pp
        except Exception:
            continue
    return best_score, best_hour, best_pp


def _eval_day(pp, yong):
    """评估某局对该事项的吉凶分数。"""
    score = 0
    gongs = pp.get("gongs", {})
    yong_gong, yong_kind, yong_info = QG.find_yong_gong(pp, yong)
    if yong_gong is None:
        score -= 5
        # 用直符兜底
        yong_gong = pp.get("zhifu_gong")
        if yong_gong:
            yong_info = gongs.get(yong_gong, {})
    if yong_info:
        if yong_info.get("is_kong"):
            score -= 10
        men = yong_info.get("men", "")
        if men in ("开门", "休门", "生门"):
            score += 5
        elif men in ("死门", "惊门", "伤门"):
            score -= 5
        star = yong_info.get("tianpan_star", "")
        if Q.STAR_FORTUNE.get(star) == "吉":
            score += 3
        elif Q.STAR_FORTUNE.get(star) == "凶":
            score -= 3
        shen = yong_info.get("shen", "")
        if yong in ("六合",) and shen == "六合":
            score += 4
        if Q.SHEN_FORTUNE.get(shen) == "吉":
            score += 2
        elif Q.SHEN_FORTUNE.get(shen) == "凶":
            score -= 2
        tp_yi = yong_info.get("tianpan_yi", "")
        dipan = yong_info.get("dipan", "")
        if dipan in ("乙", "丙", "丁"):
            score += 3
        if tp_yi in ("乙", "丙", "丁"):
            score += 2
    # 格局
    try:
        gejus = QG.detect_geju(pp)
        for name, desc, ft in gejus:
            if ft == "吉":
                score += 3
            elif ft == "凶":
                score -= 3
    except Exception:
        pass
    # 直使空亡
    zs_men = pp.get("zhishi_men", "")
    zs_g, _, zs_info = QG.find_yong_gong(pp, zs_men)
    if zs_info and zs_info.get("is_kong"):
        score -= 4
    # 反吟伏吟扣分
    tianpan = pp.get("tianpan", {})
    zhifu_gong = pp.get("zhifu_gong", 0)
    zhifu_star = pp.get("zhifu_star", "")
    tp_star_gong = None
    for g, s in tianpan.items():
        if s == zhifu_star:
            tp_star_gong = g
            break
    if tp_star_gong and tp_star_gong == zhifu_gong:
        score -= 3  # 伏吟
    return score


_HOUR_NAME = {5: "卯时", 11: "午时", 17: "酉时"}


def zeri(question, now=None, max_days=31, top_n=5):
    """择日主函数。
    返回 dict: {
        "time_range": str,
        "event": str,
        "yong": str,
        "good_days": [(日期str, 星期, 时辰, 分数, 理由)],
        "bad_days": [(日期str, 理由)],
        "summary": str,
        "advice": str,
    }
    """
    if now is None:
        now = datetime.datetime.now()

    time_range = parse_time_range(question, now)
    event = parse_event(question)

    if time_range is None:
        return {
            "time_range": None,
            "event": event[1] if event else "未明事项",
            "yong": event[0] if event else "直符",
            "good_days": [],
            "bad_days": [],
            "summary": "未能从问题中识别到时间段。请指定时间范围，如「八月份」「国庆节期间」「下个月」等。",
            "advice": "请重新提问并明确时间段，例如：择吉 八月份适合开业的日子。",
        }

    start, end, range_desc = time_range
    if (end - start).days + 1 > max_days:
        end = start + datetime.timedelta(days=max_days - 1)
        range_desc += f"（仅扫描前{max_days}天）"

    if event is None:
        yong = "生门"
        event_desc = "一般谋为"
    else:
        yong, event_desc = event

    all_days = []
    cur = start
    while cur <= end:
        score, best_hour, best_pp = _scan_day(cur, yong, question)
        if best_pp is not None:
            all_days.append((cur, score, best_hour, best_pp))
        cur += datetime.timedelta(days=1)

    all_days.sort(key=lambda x: x[1], reverse=True)

    good_days = []
    for date, score, hour, pp in all_days[:top_n]:
        reasons = _day_reasons(pp, yong, score)
        date_str = f"{date.month}月{date.day}日"
        weekday = "一二三四五六日"[date.weekday()]
        good_days.append((date_str, f"周{weekday}", _HOUR_NAME.get(hour, ""), score, reasons))

    bad_days = []
    for date, score, hour, pp in all_days[-3:]:
        if score < -5:
            date_str = f"{date.month}月{date.day}日"
            weekday = "一二三四五六日"[date.weekday()]
            reasons = _day_reasons(pp, yong, score)
            bad_days.append((f"{date_str}（周{weekday}）", reasons))

    if good_days:
        best = good_days[0]
        summary = f"在{range_desc}内，适合{event_desc}的最佳日期为{best[0]}{best[1]}，"
        summary += f"宜选{best[2]}行事，综合评分{best[3]:+d}。"
        if len(good_days) > 1:
            others = "、".join(d[0] for d in good_days[1:])
            summary += f"\n其他较佳日期：{others}。"
        if bad_days:
            bad_str = "、".join(d[0] for d in bad_days)
            summary += f"\n宜避开：{bad_str}。"
    else:
        summary = f"在{range_desc}内未找到适合{event_desc}的吉日，建议另择时段。"

    yong_meaning = Q.QM_YONG_MEANING.get(yong, "")
    advice = f"事项【{event_desc}】以【{yong}】为用神。{yong_meaning}\n"
    advice += f"择吉日已综合考虑用神落宫、门宫生克、格局吉凶、空亡等因素。\n"
    advice += "吉日选定后，宜在当日吉时（如三奇得使之辰、三吉门临宫之时）行事，效果更佳。"

    return {
        "time_range": range_desc,
        "event": event_desc,
        "yong": yong,
        "good_days": good_days,
        "bad_days": bad_days,
        "summary": summary,
        "advice": advice,
    }


def _day_reasons(pp, yong, score):
    """生成某日被评为吉/凶的理由。"""
    reasons = []
    yong_gong, yong_kind, yong_info = QG.find_yong_gong(pp, yong)
    if yong_gong is None:
        yong_gong = pp.get("zhifu_gong")
        yong_info = pp.get("gongs", {}).get(yong_gong, {})
    if yong_info:
        men = yong_info.get("men", "")
        star = yong_info.get("tianpan_star", "")
        shen = yong_info.get("shen", "")
        gong_name = Q.GONG.get(yong_gong, ("", "", ""))[0]
        if men in ("开门", "休门", "生门"):
            reasons.append(f"{yong}临{men}于{gong_name}宫，吉门相助")
        elif men in ("死门", "惊门", "伤门"):
            reasons.append(f"{yong}临{men}于{gong_name}宫，凶门不利")
        if yong_info.get("is_kong"):
            reasons.append(f"用神落{gong_name}宫逢空亡")
        if shen == yong:
            reasons.append(f"用神与{shen}同宫")
        dipan = yong_info.get("dipan", "")
        if dipan in ("乙", "丙", "丁"):
            reasons.append(f"三奇{dipan}加临用神宫")
    try:
        gejus = QG.detect_geju(pp)
        for name, desc, ft in gejus[:3]:
            reasons.append(f"{name}({ft})")
    except Exception:
        pass
    if not reasons:
        reasons.append("综合评分" + f"{score:+d}")
    return "；".join(reasons)
