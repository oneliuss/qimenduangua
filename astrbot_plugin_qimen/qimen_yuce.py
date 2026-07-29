# -*- coding: utf-8 -*-
"""
奇门遁甲预测模块：推断事物发展趋势、成败概率、应期与风险预警。
古法依据：《神奇之门》《开悟之门》《奇门真髓》。
核心逻辑：取用神 -> 查落宫旺相休囚 -> 门宫生克 -> 格局吉凶 -> 空亡应期 -> 综合定趋势。
"""
try:
    from . import qimen_data as Q
    from . import qimen_duangua as QG
except ImportError:
    import qimen_data as Q
    import qimen_duangua as QG


_SEASON_WX = {"春": "木", "夏": "火", "秋": "金", "冬": "水", "四季月": "土"}


def _safe_month_zhi(pp):
    mgz = pp.get("month_gz", "")
    return mgz[1] if len(mgz) >= 2 else ""


def _star_strength(star, month_zhi):
    """九星旺相休囚（依月令季节与星五行生克）。"""
    season = Q.MONTH_SEASON.get(month_zhi, "")
    season_wx = _SEASON_WX.get(season, "")
    star_wx = Q.STAR_WUXING.get(star, "土")
    if not season_wx:
        return "平"
    if star_wx == season_wx:
        return "旺"
    if Q.wuxing_sheng(season_wx, star_wx):
        return "相"
    if Q.wuxing_sheng(star_wx, season_wx):
        return "休"
    if Q.wuxing_ke(star_wx, season_wx):
        return "囚"
    if Q.wuxing_ke(season_wx, star_wx):
        return "死"
    return "平"


def _score_to_rate(score):
    if score >= 5:
        return "高"
    if score >= 2:
        return "中高"
    if score >= 0:
        return "中"
    if score >= -2:
        return "中低"
    return "低"


def yuce(pp, style="modern"):
    """预测模块主函数。返回结构化结果 dict。"""
    try:
        return _yuce_impl(pp, style=style)
    except Exception as e:
        return {
            "module": "预测",
            "title": "趋势预测",
            "trend": f"预测推断受阻：{e}",
            "success_rate": "中",
            "phases": [],
            "timing": "应期难定",
            "risks": [],
            "summary": "盘面信息不足，建议重新起局或参看直符直使综合判断。",
        }


def _yuce_impl(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    gongs = pp.get("gongs", {})
    question = pp.get("question", "")
    month_zhi = _safe_month_zhi(pp)

    yong = Q.pick_yongshen_qm(question)
    if not yong:
        yong = "直符"
    yong_gong, yong_kind, yong_info = QG.find_yong_gong(pp, yong)

    score = 0
    risks = []
    phases = []

    if yong_gong is None:
        score -= 1
        phases.append(_t(
            "起始阶段：用神未显于盘，事态尚未明朗，须待时机成熟方有头绪。",
            "起始阶段：代表这件事的信息没有出现在盘上，情况还不明朗，要等时机成熟才有头绪。"
        ))
    else:
        g_wx = Q.GONG[yong_gong][2]
        bagua = Q.GONG[yong_gong][0]
        ft = QG._fortune_of(yong)
        if ft == "吉":
            score += 2
            phases.append(_t(
                f"起始阶段：用神【{yong}】为吉{yong_kind}，落{bagua}宫，开局有利，事有生机。",
                f"起始阶段：代表这件事的【{yong}】是吉利的，落在{bagua}宫，开局不错，有希望。"
            ))
        elif ft == "凶":
            score -= 2
            phases.append(_t(
                f"起始阶段：用神【{yong}】为凶{yong_kind}，落{bagua}宫，开局不利，需防阻滞。",
                f"起始阶段：代表这件事的【{yong}】偏凶，落在{bagua}宫，开局不太理想，要注意阻碍。"
            ))
            risks.append(_t(
                f"用神{yong}本身为凶，主阻滞不利。",
                f"用神{yong}本身偏凶，说明事情会有阻碍。"
            ))
        else:
            phases.append(_t(
                f"起始阶段：用神【{yong}】为平{yong_kind}，落{bagua}宫，吉凶参半，须看后续生扶。",
                f"起始阶段：代表这件事的【{yong}】属于中性，落在{bagua}宫，好坏参半，要看后续发展。"
            ))

        if yong_kind == "门":
            rel, delta = QG.men_gong_relation(yong, g_wx)
            score += delta
            if rel == "门迫":
                risks.append(_t(
                    f"{yong}临{bagua}宫门迫（门克宫），事多难成，大凶之象。",
                    f"{yong}落在{bagua}宫形成门迫（门克宫），事情很难成，很不理想。"
                ))
                phases.append(_t(
                    f"发展阶段：{yong}迫{bagua}宫，发展受阻，强为则败。",
                    f"发展阶段：{yong}克{bagua}宫，发展受阻，硬来容易失败。"
                ))
            elif rel == "门制":
                risks.append(_t(
                    f"{yong}受{bagua}宫所制，发展受限。",
                    f"{yong}被{bagua}宫克制，发展受限。"
                ))
                phases.append(_t(
                    f"发展阶段：{yong}受宫制，推进吃力，需借外力。",
                    f"发展阶段：{yong}被宫位克制，推进比较吃力，需要借助外力。"
                ))
            elif rel == "门和":
                phases.append(_t(
                    f"发展阶段：宫生{yong}（门和），有助力扶持，发展顺遂。",
                    f"发展阶段：宫位生扶{yong}（门和），有人帮忙，发展顺利。"
                ))
            elif rel == "门义":
                phases.append(_t(
                    f"发展阶段：{yong}生宫（门义），事顺而通达。",
                    f"发展阶段：{yong}生扶宫位（门义），事情顺当通达。"
                ))
            else:
                phases.append(_t(
                    f"发展阶段：{yong}与宫比和，平稳推进。",
                    f"发展阶段：{yong}和宫位比和，平稳推进。"
                ))
            if month_zhi:
                ws = QG.get_men_wangshuai(yong, month_zhi)
                if ws in ("旺", "相"):
                    score += 1
                    phases.append(_t(
                        f"用神{yong}当令{ws}，势头正盛，宜趁势而为。",
                        f"用神{yong}当前处于「{ws}」的状态，势头正旺，适合趁势去做。"
                    ))
                elif ws == "死":
                    score -= 1
                    risks.append(_t(
                        f"用神{yong}月令处死地，气数衰弱。",
                        f"用神{yong}在当前月份处于「死」的状态，气势比较弱。"
                    ))

        tp_star = (yong_info or {}).get("tianpan_star", "")
        if tp_star:
            st = _star_strength(tp_star, month_zhi)
            if st in ("旺", "相"):
                score += 1
                phases.append(_t(
                    f"结果阶段：天盘{tp_star}{st}而有力，结局可期向好。",
                    f"结果阶段：天盘{tp_star}处于「{st}」的状态，有力量，结局应该不错。"
                ))
            elif st in ("死", "囚"):
                score -= 1
                risks.append(_t(
                    f"天盘{tp_star}处{st}地，后劲不足，结局堪忧。",
                    f"天盘{tp_star}处于「{st}」的状态，后劲不够，结局不太乐观。"
                ))
            else:
                phases.append(_t(
                    f"结果阶段：天盘{tp_star}处{st}，平稳收束。",
                    f"结果阶段：天盘{tp_star}处于「{st}」的状态，平稳收尾。"
                ))

        if yong_info and yong_info.get("is_kong"):
            score -= 3
            risks.append(_t(
                f"用神落{bagua}宫逢空亡，眼下事无着落，须待出空方有转机。",
                f"用神落{bagua}宫赶上空亡，眼下事情没有着落，要等出空之后才有转机。"
            ))
        if yong_info and yong_info.get("is_ma"):
            score += 1
            phases.append(_t(
                "用神临驿马，事主速动变化，发展节奏较快。",
                "用神带驿马，说明事情变化快、节奏比较快。"
            ))

        for qi, g, desc in QG.detect_qi_mu(pp):
            if g == yong_gong:
                score -= 1
                risks.append(_t(desc + "，无力，须待冲墓之期。", desc + "，力量发挥不出来，要等冲开的时候才行。"))
        for yi, g, desc in QG.detect_ji_xing(pp):
            if g == yong_gong:
                score -= 2
                risks.append(_t("用神宫" + desc + "。", "用神所在宫位" + desc + "。"))

    gejus = QG.detect_geju(pp)
    ji_count = 0
    xiong_count = 0
    for name, desc, ft in gejus:
        if ft == "吉":
            ji_count += 1
            score += 3
        elif ft == "凶":
            xiong_count += 1
            score -= 3
            risks.append(_t(
                f"格局【{name}】：{desc}，凶。",
                f"格局【{name}】：{desc}，不太吉利。"
            ))

    for name, ft, desc in QG.detect_shi_gan_ke_ying(pp)[:3]:
        if ft == "吉":
            score += 1
        elif ft == "凶":
            score -= 1
            risks.append(_t(
                f"十干克应【{name}】：{desc}，凶。",
                f"干支组合【{name}】：{desc}，偏凶。"
            ))

    if pp.get("kong_gongs"):
        for g in pp["kong_gongs"]:
            risks.append(_t(
                f"{Q.GONG[g][0]}宫逢空亡，相关事项易落空拖延。",
                f"{Q.GONG[g][0]}宫赶上空亡，相关的事容易落空、拖延。"
            ))

    zhuke = QG.analyze_zhuke(pp, yong_gong, yong_info)
    timing = QG.infer_yingqi(pp, yong, yong_gong, yong_info, style=style)

    success_rate = _score_to_rate(score)

    if score >= 5:
        trend = _t("顺势上扬，诸事亨通，宜积极进取。",
                   "整体势头往上走，各方面都顺，适合积极去做。")
    elif score >= 2:
        trend = _t("总体向好，虽有波折但可成，宜稳步推进。",
                   "总体不错，虽然有些波折但能成，适合稳步推进。")
    elif score >= 0:
        trend = _t("吉凶参半，进退胶着，须择时择机而动。",
                   "好坏参半，进退两难，要挑好时机再动。")
    elif score >= -2:
        trend = _t("势头偏弱，多有阻碍，宜缓不宜急。",
                   "势头偏弱，阻碍比较多，建议慢一点、别急。")
    elif score >= -4:
        trend = _t("走势低迷，阻滞重重，宜暂避锋芒。",
                   "整体走势不太好，阻碍比较多，建议先缓一缓。")
    else:
        trend = _t("凶险之兆，事多难成，当下宜止宜守。",
                   "各方面都不太妙，事情很难成，现在最好先别动。")

    if yong_gong is not None:
        summary = _t(
            f"综合而论，用神【{yong}】落{Q.GONG[yong_gong][0]}宫，"
            f"吉格{ji_count}个、凶格{xiong_count}个，"
            f"成败概率【{success_rate}】。{trend}",
            f"综合来看，代表这件事的【{yong}】落在{Q.GONG[yong_gong][0]}宫，"
            f"好的格局{ji_count}个、不好的格局{xiong_count}个，"
            f"成败概率【{success_rate}】。{trend}"
        )
    else:
        summary = _t(
            f"用神未显，吉格{ji_count}个、凶格{xiong_count}个，成败概率【{success_rate}】。{trend}",
            f"用神没有出现在盘上，好的格局{ji_count}个、不好的格局{xiong_count}个，成败概率【{success_rate}】。{trend}"
        )

    return {
        "module": "预测",
        "title": "趋势预测",
        "trend": trend,
        "success_rate": success_rate,
        "phases": phases,
        "timing": timing,
        "risks": risks,
        "summary": summary,
        "score": score,
        "yong": yong,
        "yong_gong": yong_gong,
        "zhuke": zhuke,
        "gejus": gejus,
    }
