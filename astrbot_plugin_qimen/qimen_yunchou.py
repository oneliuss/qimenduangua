# -*- coding: utf-8 -*-
"""
奇门遁甲运筹模块：择吉方、择吉时、定攻守策略与行动方针。
古法依据：《神奇之门》《开悟之门》《奇门法窍》。
核心逻辑：遍历九宫评分（吉门+吉星+吉神+三奇）定最佳方位 ->
          依时干日干定吉时 -> 依格局定策略 -> 依主客生克定攻守。
"""
try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


_SANQI = ("乙", "丙", "丁")
_JI_MEN = ("开门", "休门", "生门")
_XIONG_MEN = ("死门", "惊门", "伤门")


def _gong_score(info):
    """评估单宫吉凶分数（越高越吉）。"""
    g = info.get("gong")
    if g == 5:
        return -999
    s = 0
    men = info.get("men", "")
    star = info.get("tianpan_star", "")
    shen = info.get("shen", "")
    yi = info.get("dipan", "")
    tp_yi = info.get("tianpan_yi", "")

    if info.get("is_kong"):
        s -= 3
    if men in _JI_MEN:
        s += 3
    elif men in _XIONG_MEN:
        s -= 3
    if Q.STAR_FORTUNE.get(star) == "吉":
        s += 2
    elif Q.STAR_FORTUNE.get(star) == "凶":
        s -= 2
    if Q.SHEN_FORTUNE.get(shen) == "吉":
        s += 2
    elif Q.SHEN_FORTUNE.get(shen) == "凶":
        s -= 2
    if yi in _SANQI:
        s += 2
    if tp_yi in _SANQI:
        s += 1
    if info.get("is_ma"):
        s += 1
    return s


def _best_gong(pp):
    gongs = pp.get("gongs", {})
    if not gongs:
        return None, None
    best_g, best_s = None, -1000
    for g, info in gongs.items():
        sc = _gong_score(info)
        if sc > best_s:
            best_s, best_g = sc, g
    return best_g, best_s


def _worst_gong(pp):
    gongs = pp.get("gongs", {})
    if not gongs:
        return None
    worst_g, worst_s = None, 1000
    for g, info in gongs.items():
        sc = _gong_score(info)
        if sc < worst_s:
            worst_s, worst_g = sc, g
    return worst_g


def _geju_strategy(pp, style="modern"):
    """依格局定总体策略。"""
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    gejus = _detect_geju_names(pp)
    if "伏吟" in gejus:
        return _t("伏吟之局，宜守不宜动，静待时机，不可强为冒进。",
                  "伏吟格局不太适合大动作，先稳住、等时机比较好，别急着冲。")
    if "反吟" in gejus:
        return _t("反吟之局，反复多变，宜变通行事，预留退路，勿钻牛角尖。",
                  "反吟格局变化多、容易反复，做事要灵活点，给自己留条后路，别太死磕。")
    ji = sum(1 for n, _, f in _raw_gejus(pp) if f == "吉")
    xiong = sum(1 for n, _, f in _raw_gejus(pp) if f == "凶")
    if ji >= 2 and ji > xiong:
        return _t("吉格叠见，宜顺势进取，可放手谋为。",
                  "好的格局比较多，可以顺着势头往前走，放心去做。")
    if xiong >= 2 and xiong > ji:
        return _t("凶格较多，宜暂避锋芒，稳固防守，待凶势消退再动。",
                  "不好的格局比较多，建议先避一避、稳住防守，等这阵过去再说。")
    if ji > 0 and xiong > 0:
        return _t("吉凶参半，宜攻守兼备，进退有度，择吉方吉时而动。",
                  "好坏参半，进攻和防守都要兼顾，进退有分寸，挑个好方向好时机再动。")
    return _t("格局平和，宜稳扎稳打，按部就班推进。",
              "格局比较平稳，踏踏实实、一步步来就行。")


def _raw_gejus(pp):
    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG
    return QG.detect_geju(pp)


def _detect_geju_names(pp):
    return [n for n, _, _ in _raw_gejus(pp)]


def _posture(pp, style="modern"):
    """主客攻守判断（依直符宫天盘地盘生克）。"""
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG
    yong = Q.pick_yongshen_qm(pp.get("question", "")) or "直符"
    yong_gong, _, yong_info = QG.find_yong_gong(pp, yong)
    g = yong_gong if yong_gong else pp.get("zhifu_gong")
    if g is None or g == 5:
        return _t("主客未明，宜观望待变", "主客关系不太明确，建议先观望、等变化")
    g_wx = Q.GONG[g][2]
    tp_star = (yong_info or {}).get("tianpan_star", "") or pp.get("tianpan", {}).get(g, "")
    tp_wx = Q.STAR_WUXING.get(tp_star, g_wx)
    if Q.wuxing_sheng(tp_wx, g_wx):
        return _t("天盘生地盘，利客（宜主动出击，先发制人）",
                  "天盘生地盘，利客（目前适合主动出击，抢占先机）")
    if Q.wuxing_sheng(g_wx, tp_wx):
        return _t("地盘生天盘，利主（宜静守待变，后发制人）",
                  "地盘生天盘，利主（目前适合静观其变，后发制人）")
    if Q.wuxing_ke(tp_wx, g_wx):
        return _t("天盘克地盘，客克主，利主动进取",
                  "天盘克地盘，客克主，目前适合主动进取")
    if Q.wuxing_ke(g_wx, tp_wx):
        return _t("地盘克天盘，主克客，宜防守固守",
                  "地盘克天盘，主克客，建议以防守为主")
    return _t("主客比和，势均力敌，攻守皆可",
              "主客势均力敌，进攻防守都行")


def _best_timing(pp, style="modern"):
    """依时干日干定吉时。"""
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    hour_gan = pp.get("hour_gan", "")
    day_gz = pp.get("day_gz", "")
    parts = []
    if hour_gan in _SANQI:
        qi_name = {"乙": "日奇", "丙": "月奇", "丁": "星奇"}.get(hour_gan, "")
        parts.append(_t(
            f"时干{hour_gan}（{qi_name}）临宫，当下为三奇吉时，宜速行。",
            f"时干{hour_gan}（{qi_name}）临宫，现在是个不错的时机（三奇吉时），适合赶紧行动。"
        ))
    if day_gz and day_gz[0] in _SANQI:
        parts.append(_t(
            f"日干{day_gz[0]}为三奇，本日总体吉顺，利谋为。",
            f"日干{day_gz[0]}是三奇，今天整体比较顺，适合办事。"
        ))
    ma = pp.get("ma")
    if ma:
        parts.append(_t(
            f"驿马在{ma}，宜行变动之事，出行迁移尤利。",
            f"驿马在{ma}，适合做一些变动的事，出行、搬家之类的特别有利。"
        ))
    gejus = _detect_geju_names(pp)
    if "伏吟" in gejus:
        parts.append(_t(
            "伏吟主迟，宜择冲开之期（值对宫地支之时日）再动。",
            "伏吟说明事情会比较慢，建议等到冲开的时机（对宫地支对应的日子时辰）再行动。"
        ))
    elif "反吟" in gejus:
        parts.append(_t(
            "反吟主速，事近应，宜趁近期速决。",
            "反吟说明事情来得快，近期就会有结果，适合抓紧时间解决。"
        ))
    if not parts:
        parts.append(_t(
            "无显著奇吉时干，宜择三吉门所临之时辰或驿马值期行事。",
            "没有特别突出的吉时，建议挑三吉门对应的时辰或驿马当值的时候做事。"
        ))
    return "；".join(parts) + "。"


def yunchou(pp, style="modern"):
    """运筹模块主函数。返回结构化结果 dict。"""
    try:
        return _yunchou_impl(pp, style=style)
    except Exception as e:
        return {
            "module": "运筹",
            "title": "运筹策略",
            "best_direction": "未定",
            "best_timing": "未定",
            "strategy": f"运筹推断受阻：{e}",
            "posture": "未定",
            "actions": [],
            "avoid": [],
        }


def _yong_fortune(yong):
    """取用神本身吉凶（门/星/神通用）。"""
    if yong in Q.MEN_FORTUNE:
        return Q.MEN_FORTUNE[yong]
    if yong in Q.STAR_FORTUNE:
        return Q.STAR_FORTUNE[yong]
    if yong in Q.SHEN_FORTUNE:
        return Q.SHEN_FORTUNE[yong]
    return "中"


def _event_desc(question):
    """依问题关键词提取事项简述，使同用神不同事项产出不同方略。"""
    if not question:
        return "所问之事"
    q = question
    if "出行" in q or "远行" in q or "出差" in q or "旅游" in q:
        return "出行远行"
    if "开店" in q or "创业" in q or "开张" in q:
        return "开店创业"
    if "投资" in q or "求财" in q or "理财" in q:
        return "投资求财"
    if "谈判" in q or "合作" in q or "洽谈" in q:
        return "合作谈判"
    if "搬家" in q or "迁居" in q or "搬迁" in q:
        return "搬家迁居"
    if "考试" in q or "升学" in q or "高考" in q:
        return "考试升学"
    if "结婚" in q or "嫁娶" in q or "婚嫁" in q:
        return "婚姻嫁娶"
    if "求职" in q or "谋职" in q or "找工作" in q:
        return "求职谋职"
    return "所问之事"


def _yunchou_impl(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG

    question = pp.get("question", "")
    event_desc = _event_desc(question)
    yong = Q.pick_yongshen_qm(question)
    yong_g, yong_kind, yong_info = (None, None, None)
    if yong:
        yong_g, yong_kind, yong_info = QG.find_yong_gong(pp, yong)

    best_g, best_s = _best_gong(pp)
    worst_g = _worst_gong(pp)

    # 在全局最优宫之外，兼参用神所临之宫：用神宫分高则取其所问之方
    yong_score = None
    if yong_g is not None and yong_g != 5:
        yong_score = _gong_score(pp["gongs"][yong_g])
    recommend_g = best_g
    if yong_score is not None and yong_score >= 1:
        recommend_g = yong_g

    if recommend_g is not None:
        rdir = Q.GONG[recommend_g][1]
        rgua = Q.GONG[recommend_g][0]
        best_direction = f"{rdir}方（{rgua}宫·{Q.GONG[recommend_g][2]}）"
        if yong_g is not None and yong_g != 5:
            if recommend_g == yong_g:
                best_direction += _t(
                    f"，用神【{yong}】临此方且宫气吉顺，最利所问之事",
                    f"，用神【{yong}】正好在这个方向，宫位条件好，最适合这件事"
                )
            elif yong_score is not None and yong_score <= -1:
                best_direction += _t(
                    f"；用神【{yong}】落{Q.GONG[yong_g][0]}宫气受制，故取全局吉方",
                    f"；用神【{yong}】落{Q.GONG[yong_g][0]}宫条件不太好，所以取全局最优的方向"
                )
            else:
                best_direction += _t(
                    f"；用神【{yong}】落{Q.GONG[yong_g][0]}宫气平平，参全局吉方",
                    f"；用神【{yong}】落{Q.GONG[yong_g][0]}宫条件一般，参考全局最优方向"
                )
    else:
        best_direction = _t("无可用吉方", "没有特别好的方向可用")

    strategy = _geju_strategy(pp, style=style)
    if yong:
        meaning = Q.QM_YONG_MEANING.get(yong, "")
        if yong_g is not None and yong_g != 5:
            g_wx = Q.GONG[yong_g][2]
            strategy += _t(
                f" 此问以【{yong}】为用神，落{Q.GONG[yong_g][0]}宫（{g_wx}），",
                f" 这件事以【{yong}】为用神，落在{Q.GONG[yong_g][0]}宫（{g_wx}），"
            )
            if (yong_info or {}).get("is_kong"):
                strategy += _t("逢空亡落空，宜待出空之期再谋。",
                                "赶上空亡了，暂时使不上劲，等出空之后再谋划。")
            elif _yong_fortune(yong) == "吉" and yong_score is not None and yong_score >= 1:
                strategy += _t("用神得地、宫气相扶，宜向此方进取。",
                                "用神位置好、宫位也帮忙，适合往这个方向努力。")
            elif _yong_fortune(yong) == "凶" or (yong_score is not None and yong_score <= -1):
                strategy += _t("用神宫气受制，宜暂避此方、另择吉方谋为。",
                                "用神所在宫位条件不太好，建议先避开这个方向、另找好方向做事。")
            else:
                strategy += _t("用神宫气平平，宜稳中求进。",
                                "用神所在宫位条件一般，适合稳扎稳打、慢慢推进。")
        else:
            strategy += _t(
                f" 此问以【{yong}】为用神，未显于盘，宜参直符直使。",
                f" 这件事以【{yong}】为用神，但没有出现在盘上，建议参考直符直使来判断。"
            )
        if meaning:
            strategy += f"（{meaning}）"

    strategy = _t(f"所问【{event_desc}】，", f"所问的是【{event_desc}】，") + strategy
    posture = _posture(pp, style=style)
    best_timing = _best_timing(pp, style=style)

    actions = []
    actions.append(_t(
        f"所问【{event_desc}】，以【{yong or '直符'}】为用神定方。",
        f"所问【{event_desc}】，以【{yong or '直符'}】为用神来确定方向。"
    ))
    avoid = []

    # 用神专属行动建议，使不同所问之事得出不同方略
    if yong and yong_g is not None and yong_g != 5:
        ydir = Q.GONG[yong_g][1]
        ygua = Q.GONG[yong_g][0]
        ymen = (yong_info or {}).get("men", "")
        ystar = (yong_info or {}).get("tianpan_star", "")
        yshen = (yong_info or {}).get("shen", "")
        meaning = Q.QM_YONG_MEANING.get(yong, "")
        if meaning:
            actions.append(_t(
                f"所问以【{yong}】为用神：{meaning}",
                f"这件事以【{yong}】为用神：{meaning}"
            ))
        if yong_score is not None and yong_score >= 1:
            actions.append(_t(
                f"用神临{ygua}宫（{ydir}方），临{ymen}、{ystar}、{yshen}，宫气吉顺，宜取{ydir}方行所问之事。",
                f"用神落在{ygua}宫（{ydir}方），那边有{ymen}、{ystar}、{yshen}，条件不错，建议往{ydir}方做这件事。"
            ))
        elif yong_score is not None and yong_score <= -1:
            actions.append(_t(
                f"用神临{ygua}宫（{ydir}方），宫气受制，不宜专向此方，宜避之另择吉方。",
                f"用神落在{ygua}宫（{ydir}方），那边条件不太好，不建议专门往这个方向，最好避开另找好方向。"
            ))
        else:
            actions.append(_t(
                f"用神临{ygua}宫（{ydir}方），宫气平平，可参全局吉方行事。",
                f"用神落在{ygua}宫（{ydir}方），那边条件一般，可以参考全局最优方向做事。"
            ))
        if (yong_info or {}).get("is_kong"):
            actions.append(_t(
                f"用神落{ygua}宫逢空亡，眼下难成，宜待出空之期再图。",
                f"用神落{ygua}宫赶上空亡，暂时做不成，等几天（出空之后）再说。"
            ))

    if recommend_g is not None:
        binfo = pp["gongs"][recommend_g]
        bmen = binfo.get("men", "")
        bstar = binfo.get("tianpan_star", "")
        bshen = binfo.get("shen", "")
        byi = binfo.get("dipan", "")
        actions.append(_t(
            f"宜取{Q.GONG[recommend_g][1]}方行事，该宫临{bmen}、{bstar}、{bshen}"
            + (f"、三奇{byi}" if byi in _SANQI else "") + "，诸吉汇聚。",
            f"建议往{Q.GONG[recommend_g][1]}方做事，那边有{bmen}、{bstar}、{bshen}"
            + (f"、三奇{byi}" if byi in _SANQI else "") + "，各方面条件都不错。"
        ))
        if bmen == "开门":
            actions.append(_t(
                "开门方位利求职、升迁、开店创业、出行远行。",
                "开门方位适合找工作、升职、开店创业、出行远行。"
            ))
        elif bmen == "生门":
            actions.append(_t(
                "生门方位利求财、投资、经营买卖、农事产业。",
                "生门方位适合求财、投资、做买卖、搞农事产业。"
            ))
        elif bmen == "休门":
            actions.append(_t(
                "休门方位利和谈、求请、养息、安养调息。",
                "休门方位适合谈判、求人办事、休养、调养身体。"
            ))
        if "利客" in posture or "主动" in posture:
            actions.append(_t(
                "主客利客，宜主动出击、先发制人，把握先机。",
                "目前适合主动出击，抢占先机，把握住机会。"
            ))
        elif "利主" in posture or "静守" in posture:
            actions.append(_t(
                "主客利主，宜以静制动、后发制人，蓄势待发。",
                "目前适合以静制动，后发制人，先蓄势再行动。"
            ))
    else:
        actions.append(_t(
            "盘面无明显吉方，宜从直符直使所临方位参看。",
            "盘面上没有明显的好方向，建议看直符直使所在的方位作参考。"
        ))

    if "伏吟" in _detect_geju_names(pp):
        avoid.append(_t(
            "伏吟之局忌大动冒进，宜守正待时。",
            "伏吟格局不太适合大动作，先稳住比较好。"
        ))
    if "反吟" in _detect_geju_names(pp):
        avoid.append(_t(
            "反吟之局忌一意孤行，防半途而废、反复折腾。",
            "反吟格局别一条道走到黑，小心半途而废、反复折腾。"
        ))
    if (yong and yong_g is not None and yong_g != 5 and yong_score is not None
            and yong_score <= -1 and yong_g != recommend_g):
        avoid.append(_t(
            f"忌取{Q.GONG[yong_g][1]}方（用神{yong}受制之宫），所问之事此方多败。",
            f"避开{Q.GONG[yong_g][1]}方（用神{yong}所在宫位条件不好），这个方向容易失败。"
        ))
    if worst_g is not None and worst_g != recommend_g:
        winfo = pp["gongs"][worst_g]
        wmen = winfo.get("men", "")
        wdir = Q.GONG[worst_g][1]
        if wmen in _XIONG_MEN:
            avoid.append(_t(
                f"忌取{wdir}方（{wmen}所在），凶门临之，行事多败。",
                f"避开{wdir}方（那边是{wmen}），凶门在那里，做事容易失败。"
            ))
        if winfo.get("is_kong"):
            avoid.append(_t(
                f"{Q.GONG[worst_g][0]}宫逢空亡，不宜在此方谋事，防落空。",
                f"{Q.GONG[worst_g][0]}宫赶上空亡，不建议在这个方向做事，容易落空。"
            ))
    for g in pp.get("kong_gongs", []):
        if g != recommend_g:
            avoid.append(_t(
                f"{Q.GONG[g][0]}宫空亡，相关方位事项易落空，须待出空。",
                f"{Q.GONG[g][0]}宫空亡，这个方向的事容易落空，要等出空之后再说。"
            ))

    if not avoid:
        avoid.append(_t(
            "无显著凶险方位，仍宜避开空亡与凶门所临之方。",
            "没有特别凶的方位，但还是建议避开空亡和凶门所在的方向。"
        ))

    return {
        "module": "运筹",
        "title": "运筹策略",
        "best_direction": best_direction,
        "best_timing": best_timing,
        "strategy": strategy,
        "posture": posture,
        "actions": actions,
        "avoid": avoid,
        "best_gong": recommend_g,
        "worst_gong": worst_g,
    }
