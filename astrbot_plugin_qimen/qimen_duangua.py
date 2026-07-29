# -*- coding: utf-8 -*-
"""
奇门遁甲断卦：基于起局排盘，依古法判吉凶、给建议。
古法依据：《御定奇门宝鉴》《奇门法窍》。
现代依据：张志春《神奇之门》《开悟之门》、《奇门启悟》、《奇门遁甲现代实例精解》、《奇门真髓》、《奇门精粹》。

核心断卦流程：
  取用神 -> 查用神落宫旺相休囚 -> 看门宫生克(门迫/门义/门和/门制) ->
  十干克应(天盘干加地盘干) -> 击刑入墓 -> 格局(吉格凶格) ->
  直符直使生克 -> 空亡转宫 -> 主客关系 -> 综合断吉凶应期建议。
"""
try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


def _wx_of(yong):
    if yong in Q.MEN_WUXING:
        return Q.MEN_WUXING[yong]
    if yong in Q.STAR_WUXING:
        return Q.STAR_WUXING[yong]
    if yong in Q.SHEN_WUXING:
        return Q.SHEN_WUXING[yong]
    if yong in Q.YI_WUXING:
        return Q.YI_WUXING[yong]
    return "土"


def _fortune_of(yong):
    if yong in Q.MEN_FORTUNE:
        return Q.MEN_FORTUNE[yong]
    if yong in Q.STAR_FORTUNE:
        return Q.STAR_FORTUNE[yong]
    if yong in Q.SHEN_FORTUNE:
        return Q.SHEN_FORTUNE[yong]
    return "中"


def find_yong_gong(pp, yong):
    for g, info in pp["gongs"].items():
        if info["men"] == yong:
            return g, "门", info
        if info["tianpan_star"] == yong:
            return g, "星", info
        if info["shen"] == yong:
            return g, "神", info
        if info["dipan"] == yong:
            return g, "仪", info
    return None, None, None


# ===================== 门宫生克 =====================
def men_gong_relation(men, gong_wx):
    men_wx = Q.MEN_WUXING.get(men, "土")
    if men_wx == gong_wx:
        return "门旺", 0
    if Q.wuxing_sheng(men_wx, gong_wx):
        return "门义", 1
    if Q.wuxing_ke(men_wx, gong_wx):
        return "门迫", -2
    if Q.wuxing_sheng(gong_wx, men_wx):
        return "门和", 1
    if Q.wuxing_ke(gong_wx, men_wx):
        return "门制", -1
    return "比和", 0


# ===================== 十干克应（天盘干加地盘干）=====================
def detect_shi_gan_ke_ying(pp):
    """依《神奇之门》：天盘干加地盘干的组合断吉凶。返回 [(格名, 吉凶, 断语), ...]。"""
    results = []
    gongs = pp["gongs"]
    for g, info in gongs.items():
        dipan_yi = info["dipan"]
        tp_yi = info.get("tianpan_yi", "")
        if not tp_yi or g == 5:
            continue
        key = (tp_yi, dipan_yi)
        if key in Q.SHI_GAN_KE_YING:
            name, ft, desc = Q.SHI_GAN_KE_YING[key]
            results.append((name, ft, f"{tp_yi}加{dipan_yi}于{Q.GONG[g][0]}宫：{desc}"))
    return results


# ===================== 六仪击刑 =====================
def detect_ji_xing(pp):
    """依《御定奇门宝鉴》：检测六仪击刑。返回 [(仪, 宫, 描述), ...]。"""
    results = []
    for g, info in pp["gongs"].items():
        yi = info["dipan"]
        if (yi, g) in Q.YI_JI_XING:
            results.append((yi, g, Q.YI_JI_XING[(yi, g)]))
    return results


# ===================== 三奇入墓 =====================
def detect_qi_mu(pp):
    """依《奇门法窍》：检测三奇入墓。返回 [(奇, 宫, 描述), ...]。"""
    results = []
    for g, info in pp["gongs"].items():
        yi = info["dipan"]
        if (yi, g) in Q.QI_MU:
            results.append((yi, g, Q.QI_MU[(yi, g)]))
    return results


# ===================== 空亡转宫 =====================
def get_kong_zhuan(pp):
    """依《神奇之门》：空亡转宫，空亡对冲之宫为转宫，断事以转宫论。"""
    kong_gongs = pp.get("kong_gongs", [])
    zhuan = []
    for g in kong_gongs:
        dg = Q.DUI_GONG.get(g)
        if dg:
            zhuan.append((g, dg))
    return zhuan


# ===================== 八门旺衰（依月令）=====================
def get_men_wangshuai(men, month_zhi):
    """依月令查八门旺相休囚。返回旺衰状态字符串。"""
    season = Q.MONTH_SEASON.get(month_zhi, "")
    wang_table = Q.MEN_WANG_SEASON.get(men, {})
    for status, seasons in wang_table.items():
        if season in seasons:
            return status
    return "平"


# ===================== 格局识别 =====================
def detect_geju(pp):
    """识别常见吉格凶格。返回 [(格名, 描述, 吉凶), ...]。"""
    gejus = []
    gongs = pp["gongs"]
    zhifu_gong = pp["zhifu_gong"]
    zhifu_star = pp["zhifu_star"]
    zhishi_men = pp["zhishi_men"]
    dipan = pp["dipan"]
    tianpan = pp["tianpan"]

    # 伏吟
    if tianpan.get(zhifu_gong) == zhifu_star:
        gejus.append(("伏吟", "直符星伏于本宫，停滞不前，宜守不宜动", "凶"))

    # 反吟
    tp_star_gong = None
    for g, s in tianpan.items():
        if s == zhifu_star:
            tp_star_gong = g
            break
    if tp_star_gong and Q.DUI_GONG.get(zhifu_gong) == tp_star_gong and tp_star_gong != zhifu_gong:
        gejus.append(("反吟", "直符星临对宫，反复多变，半途而废", "凶"))

    sanqi = ["乙", "丙", "丁"]
    sanjimen = ["开门", "休门", "生门"]

    # 三诈格：三奇临吉门
    for g, info in gongs.items():
        if info["dipan"] in sanqi and info["men"] in sanjimen and not info["is_kong"]:
            star = info["tianpan_star"]
            star_ft = Q.STAR_FORTUNE.get(star, "")
            if star_ft == "吉":
                gejus.append(("重诈格", f"{info['dipan']}奇临{info['men']}+{star}于{Q.GONG[g][0]}宫，宜暗谋密事", "吉"))
            else:
                gejus.append(("三诈格", f"{info['dipan']}奇临{info['men']}于{Q.GONG[g][0]}宫，谋事可成", "吉"))

    # 玉女守门
    for g, info in gongs.items():
        if info["dipan"] == "丁" and info["men"] == zhishi_men:
            gejus.append(("玉女守门", "丁奇临直使之宫，宜阴私和合、密谋", "吉"))

    # 青龙返首
    for g, yi in dipan.items():
        if yi == "戊" and tianpan.get(g) == zhifu_star:
            gejus.append(("青龙返首", "直符加临甲子戊，大吉，百事皆遂", "吉"))

    # 飞鸟跌穴：乙加戊
    for g, info in gongs.items():
        if info["dipan"] == "戊":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "乙":
                gejus.append(("飞鸟跌穴", "乙奇加地盘戊，吉，宜进纳求职", "吉"))

    # 青龙逃走：乙加辛
    for g, info in gongs.items():
        if info["dipan"] == "辛":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "乙":
                gejus.append(("青龙逃走", "乙奇加辛，凶，破财伤灾", "凶"))

    # 白虎猖狂：庚加戊
    for g, info in gongs.items():
        if info["dipan"] == "戊":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "庚":
                gejus.append(("白虎猖狂", "庚加戊，凶，官非破财", "凶"))

    # 腾蛇妖娇：辛加乙
    for g, info in gongs.items():
        if info["dipan"] == "乙":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "辛":
                gejus.append(("腾蛇妖娇", "辛加乙，凶，虚惊口舌", "凶"))

    # 太白入荧：庚加丙
    for g, info in gongs.items():
        if info["dipan"] == "丙":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "庚":
                gejus.append(("太白入荧", "庚加丙，凶，主贼来犯", "凶"))

    # 荧入太白：丙加庚
    for g, info in gongs.items():
        if info["dipan"] == "庚":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "丙":
                gejus.append(("荧入太白", "丙加庚，凶，贼去亦耗", "凶"))

    # 大格：庚加癸
    for g, info in gongs.items():
        if info["dipan"] == "癸":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "庚":
                gejus.append(("大格", "庚加癸，凶，行人不至", "凶"))

    # 小格：庚加壬
    for g, info in gongs.items():
        if info["dipan"] == "壬":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "庚":
                gejus.append(("小格", "庚加壬，凶，官非词讼", "凶"))

    # 刑格：庚加己
    for g, info in gongs.items():
        if info["dipan"] == "己":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "庚":
                gejus.append(("刑格", "庚加己，凶，遭刑伤", "凶"))

    # 悖格：丙加癸
    for g, info in gongs.items():
        if info["dipan"] == "癸":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "丙":
                gejus.append(("悖格", "丙加癸，凶，谋为悖乱", "凶"))

    # 朱雀入江：丁加癸
    for g, info in gongs.items():
        if info["dipan"] == "癸":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "丁":
                gejus.append(("朱雀入江", "丁加癸，凶，文书口舌", "凶"))

    # 天网四张：癸加癸
    for g, info in gongs.items():
        if info["dipan"] == "癸":
            tp_yi = info.get("tianpan_yi", "")
            if tp_yi == "癸":
                gejus.append(("天网四张", "癸加癸，凶，闭塞不通", "凶"))

    # 人遁吉格：丁奇合太阴临休门
    for g, info in gongs.items():
        if info["dipan"] == "丁" and info["men"] == "休门" and info["shen"] == "太阴":
            gejus.append(("人遁吉格", "丁奇合太阴临休门，大吉，宜密谋潜行", "吉"))

    # 神遁吉格：丙奇合九天临生门
    for g, info in gongs.items():
        if info["dipan"] == "丙" and info["men"] == "生门" and info["shen"] == "九天":
            gejus.append(("神遁吉格", "丙奇合九天临生门，吉，宜行兵施恩", "吉"))

    return gejus


# ===================== 主客关系 =====================
def analyze_zhuke(pp, yong_gong, yong_info):
    """依《神奇之门》：主客关系判断。
    天盘为客（动方），地盘为主（静方）。
    天盘生地盘利客，地盘生天盘利主。
    """
    if yong_gong is None or yong_gong == 5:
        return None
    g_wx = Q.GONG[yong_gong][2]
    tp_star = yong_info.get("tianpan_star", "")
    tp_wx = Q.STAR_WUXING.get(tp_star, g_wx)
    if Q.wuxing_sheng(tp_wx, g_wx):
        return "天盘生地盘，利客（宜主动出击）"
    if Q.wuxing_sheng(g_wx, tp_wx):
        return "地盘生天盘，利主（宜静守待变）"
    if Q.wuxing_ke(tp_wx, g_wx):
        return "天盘克地盘，客克主，利客不利主"
    if Q.wuxing_ke(g_wx, tp_wx):
        return "地盘克天盘，主克客，利主不利客"
    return "主客比和，势均力敌"


# ===================== 综合断卦 =====================
def judge(pp, style="modern"):
    """奇门断卦主函数。返回结构化结果 dict。
    style: 'modern'=白话通俗易懂，'classic'=古法直断偏文言。
    """
    question = pp["question"]
    gongs = pp["gongs"]
    analysis = []
    score = 0
    modern = (style != "classic")

    def _t(classic_text, modern_text):
        """根据风格返回对应文本。"""
        return modern_text if modern else classic_text

    # 1. 取用神
    yong = Q.pick_yongshen_qm(question)
    use_zhifu = False
    if not yong:
        yong = "直符"
        use_zhifu = True

    yong_gong, yong_kind, yong_info = find_yong_gong(pp, yong)

    # 2. 用神落宫与状态
    if yong_gong is None:
        analysis.append(_t(
            f"用神【{yong}】未显于盘，须参看直符直使与日时干。",
            f"代表这件事的【{yong}】没有出现在盘面上，要看整体大局（直符直使）来判断。"
        ))
    else:
        g_wx = Q.GONG[yong_gong][2]
        analysis.append(_t(
            f"用神【{yong}】({Q.GONG[yong_gong][0]}宫·{g_wx})，临{yong_kind}盘。",
            f"代表这件事的【{yong}】落在{Q.GONG[yong_gong][0]}宫（方位：{Q.GONG[yong_gong][1]}，五行属{g_wx}）。"
        ))
        # 用神本身吉凶
        ft = _fortune_of(yong)
        if ft == "吉":
            analysis.append(_t(f"{yong}为吉{yong_kind}，主顺遂。", f"{yong}本身是吉利的，说明事情有好的基础。"))
            score += 2
        elif ft == "凶":
            analysis.append(_t(f"{yong}为凶{yong_kind}，主阻滞。", f"{yong}本身偏凶，说明事情会有阻碍。"))
            score -= 2
        elif ft == "平" or ft == "平吉":
            analysis.append(_t(f"{yong}为平{yong_kind}，吉凶参半。", f"{yong}属于中性，好坏参半，看具体情况。"))
        # 门宫生克（若用神是门）
        if yong_kind == "门":
            rel, delta = men_gong_relation(yong, g_wx)
            analysis.append(_t(
                f"{yong}临{Q.GONG[yong_gong][0]}宫，{rel}。",
                f"{yong}落在这个宫位，两者关系是「{rel}」。"
            ))
            if rel == "门迫":
                analysis.append(_t("门迫克宫，大凶，事多难成。", "门克宫位（门迫），很不理想，事情很难成。"))
            elif rel == "门和":
                analysis.append(_t("宫生门，门和，谋为有助。", "宫位生扶门（门和），有人帮忙，做事顺利。"))
            elif rel == "门义":
                analysis.append(_t("门生宫，门义，事顺。", "门生扶宫位（门义），事情会比较顺。"))
            elif rel == "门制":
                analysis.append(_t("宫克门，门制，事多受制。", "宫位克制门（门制），做事会处处受限。"))
            score += delta
            # 八门旺衰（依月令）
            month_zhi = pp.get("month_gz", "")[1] if len(pp.get("month_gz", "")) >= 2 else ""
            if month_zhi:
                ws = get_men_wangshuai(yong, month_zhi)
                analysis.append(_t(
                    f"月令{month_zhi}({Q.MONTH_SEASON.get(month_zhi,'')}季)，{yong}{ws}。",
                    f"当前是{month_zhi}月（{Q.MONTH_SEASON.get(month_zhi,'')}季），{yong}处于「{ws}」的状态。"
                ))
                if ws == "旺":
                    score += 1
                elif ws == "相":
                    score += 1
                elif ws == "死":
                    score -= 1
        # 用神宫空亡
        if yong_info["is_kong"]:
            analysis.append(_t(
                "用神落宫逢空亡，谋事落空，待出空(填实/冲空)方有转机。",
                "代表这件事的宫位正好赶上「空亡」，意思是现在落空了、使不上劲，要等过几天（出空之后）才有转机。"
            ))
            score -= 3
            # 空亡转宫
            zhuan_gong = Q.DUI_GONG.get(yong_gong)
            if zhuan_gong:
                zhuan_info = gongs.get(zhuan_gong, {})
                analysis.append(_t(
                    f"空亡转宫至{Q.GONG[zhuan_gong][0]}宫，参看转宫："
                    f"{zhuan_info.get('tianpan_star','')}/{zhuan_info.get('men','')}。",
                    f"空亡的话要看对面的宫位（{Q.GONG[zhuan_gong][0]}宫，{Q.GONG[zhuan_gong][1]}方），"
                    f"那里是{zhuan_info.get('tianpan_star','')}/{zhuan_info.get('men','')}，可以作为参考。"
                ))
        # 用神宫临马星
        if yong_info["is_ma"]:
            analysis.append(_t(
                "用神宫临驿马，主变动、速行，事有走动之象。",
                "这个宫位带「驿马」，说明事情会有变动、走得快，可能有出差、搬迁之类的事。"
            ))
            score += 1
        # 三奇入墓
        qi_mu_results = detect_qi_mu(pp)
        for qi, g, desc in qi_mu_results:
            if g == yong_gong:
                analysis.append(_t(f"{desc}，无力，须待冲墓之期。", f"{desc}，力量发挥不出来，要等冲开的时候才行。"))
                score -= 1
        # 六仪击刑
        jixing_results = detect_ji_xing(pp)
        for yi, g, desc in jixing_results:
            if g == yong_gong:
                analysis.append(_t(f"用神宫{desc}，主灾咎破败。", f"用神所在宫位{desc}，容易出问题、有损失。"))
                score -= 2

    # 3. 直符直使
    zf_g = pp["zhifu_gong"]
    zf_star = pp["zhifu_star"]
    zs_men = pp["zhishi_men"]
    analysis.append(_t(
        f"直符：{zf_star}（{Q.GONG[zf_g][0]}宫）；直使：{zs_men}。",
        f"全局核心（直符）：{zf_star}在{Q.GONG[zf_g][0]}宫；执行方（直使）：{zs_men}。"
    ))
    zs_g, zs_kind, zs_info = find_yong_gong(pp, zs_men)
    if zs_g:
        zs_rel, zs_delta = men_gong_relation(zs_men, Q.GONG[zs_g][2])
        analysis.append(_t(
            f"直使{zs_men}落{Q.GONG[zs_g][0]}宫，{zs_rel}。",
            f"执行方{zs_men}落在{Q.GONG[zs_g][0]}宫，关系是「{zs_rel}」。"
        ))
        score += zs_delta
        if zs_info["is_kong"]:
            analysis.append(_t("直使落空亡，主事难成或拖延。", "执行方赶上空亡，事情容易做不成或者被拖延。"))
            score -= 2

    # 4. 格局
    gejus = detect_geju(pp)
    seen = set()
    for name, desc, ft in gejus:
        if name in seen:
            continue
        seen.add(name)
        if ft == "吉":
            analysis.append(_t(f"格局【{name}】：{desc}，吉。", f"好消息：盘中出现「{name}」格局--{desc}，是吉利的。"))
            score += 3
        elif ft == "凶":
            analysis.append(_t(f"格局【{name}】：{desc}，凶。", f"注意：盘中出现「{name}」格局--{desc}，不太吉利。"))
            score -= 3
        else:
            analysis.append(_t(f"格局【{name}】：{desc}，平。", f"盘中出现「{name}」格局--{desc}，影响一般。"))

    # 5. 十干克应（天盘干加地盘干）
    sgky = detect_shi_gan_ke_ying(pp)
    for name, ft, desc in sgky[:3]:  # 取前3条
        if ft == "吉":
            analysis.append(_t(f"十干克应【{name}】：{desc}，吉。", f"干支组合「{name}」：{desc}，偏吉。"))
            score += 1
        elif ft == "凶":
            analysis.append(_t(f"十干克应【{name}】：{desc}，凶。", f"干支组合「{name}」：{desc}，偏凶。"))
            score -= 1
        else:
            analysis.append(_t(f"十干克应【{name}】：{desc}，平。", f"干支组合「{name}」：{desc}，一般。"))

    # 6. 空亡宫
    if pp["kong_gongs"]:
        kg = "、".join(Q.GONG[g][0] for g in pp["kong_gongs"])
        analysis.append(_t(f"旬空在{kg}宫（{pp['kong']}）。", f"目前「空亡」落在{kg}宫（对应地支{pp['kong']}），这个方位暂时使不上劲。"))
        # 空亡转宫
        zhuan = get_kong_zhuan(pp)
        for og, ng in zhuan:
            analysis.append(_t(f"{Q.GONG[og][0]}宫空亡转至{Q.GONG[ng][0]}宫。", f"{Q.GONG[og][0]}宫空亡，可以看对面的{Q.GONG[ng][0]}宫（{Q.GONG[ng][1]}方）作为替代。"))

    # 7. 主客关系
    zhuke = analyze_zhuke(pp, yong_gong, yong_info)
    if zhuke:
        analysis.append(_t(f"主客：{zhuke}", f"主客关系：{zhuke}（简单说就是你是该主动出击还是该静观其变）"))

    # 8. 吉凶等级
    if score >= 5:
        level, emoji = "大吉", "🟢🟢🟢"
    elif score >= 2:
        level, emoji = "吉", "🟢🟢"
    elif score >= 0:
        level, emoji = "小吉/中平", "🟢"
    elif score >= -2:
        level, emoji = "小凶", "🟠"
    elif score >= -4:
        level, emoji = "凶", "🔴"
    else:
        level, emoji = "大凶", "🔴🔴"

    # 9. 应期
    yingqi = infer_yingqi(pp, yong, yong_gong, yong_info, style=style)

    # 10. 建议
    advice = build_advice(question, yong, level, score, yong_gong, yong_info, style=style)

    return {
        "yong": yong,
        "yong_gong": yong_gong,
        "yong_kind": yong_kind,
        "yong_info": yong_info,
        "score": score,
        "level": level,
        "emoji": emoji,
        "analysis": analysis,
        "yingqi": yingqi,
        "advice": advice,
        "gejus": gejus,
        "use_zhifu": use_zhifu,
        "zhuke": zhuke,
        "shi_gan_ke_ying": sgky,
    }


def infer_yingqi(pp, yong, yong_gong, yong_info, style="modern"):
    """应期推断（依《神奇之门》《奇门真髓》）：
    用神空待填实，伏待冲，旺待墓，衰待生。
    空亡看转宫，临马看值马之期。
    """
    modern = (style != "classic")
    if yong_gong is None:
        return ("这件事的关键信息没出现在盘上，什么时候能有结果不好说，可以看整体趋势来推测。"
                if modern else "用神未显，应期难定，可参直符直使旺相之期。")
    parts = []
    if yong_info and yong_info["is_kong"]:
        kong = pp["kong"]
        if modern:
            parts.append(f"目前赶上「空亡」（{kong}），事情暂时没着落，等到跟{kong[0]}或{kong[1]}相关的日子（大概十天内）才有动静")
        else:
            parts.append(f"用神逢空亡({kong})，待填实(值{kong[0]}或{kong[1]})或冲空之期应")
        zhuan_gong = Q.DUI_GONG.get(yong_gong)
        if zhuan_gong:
            if modern:
                parts.append(f"也可以看对面{Q.GONG[zhuan_gong][0]}宫（{Q.GONG[zhuan_gong][1]}方）对应的时间")
            else:
                parts.append(f"空亡转{Q.GONG[zhuan_gong][0]}宫，亦可期值{Q.GONG[zhuan_gong][0]}宫之期")
    else:
        if modern:
            parts.append(f"事情大概在跟{Q.GONG[yong_gong][0]}宫（{Q.GONG[yong_gong][1]}方）对应的时间有结果，或者对面宫的时间也行")
        else:
            parts.append(f"用神临{Q.GONG[yong_gong][0]}宫，可期值{Q.GONG[yong_gong][0]}宫之期或冲宫之期应")
    if pp.get("ma"):
        if modern:
            parts.append(f"驿马在{pp['ma']}，说明这件事跟走动、变动有关，可能在{pp['ma']}对应的时间有变化")
        else:
            parts.append(f"驿马在{pp['ma']}，变动之事可期值马之期")
    # 伏吟反吟应期
    gejus = detect_geju(pp)
    for name, desc, ft in gejus:
        if name == "伏吟":
            parts.append("伏吟说明事情卡住了、进展慢，要等冲开的时候才能动" if modern else "伏吟主迟，待冲开之期方动")
        elif name == "反吟":
            parts.append("反吟说明事情变化快但容易反复，应期比较近" if modern else "反吟主速，事多反复，应期近")
    return "；".join(parts) + "。"


def build_advice(question, yong, level, score, yong_gong, yong_info, style="modern"):
    """根据吉凶与用神，给出实操建议（依《神奇之门》《奇门精粹》）。"""
    modern = (style != "classic")
    if score >= 5:
        tone = ("各方面条件都很好，放心大胆去做，趁热打铁别犹豫。" if modern
                else "诸事皆宜，可放手为之，速行勿疑。")
    elif score >= 2:
        tone = ("总体来说可以做，顺势推进就行。" if modern
                else "总体可行，顺势而为，宜进取。")
    elif score >= 0:
        tone = ("可以做但别太急，稳扎稳打，挑个好时机再行动。" if modern
                else "可谋而不可急，宜稳中求进，择时而动。")
    elif score >= -2:
        tone = ("建议先缓一缓，别急着行动，小心有变数，暂时避避风头。" if modern
                else "宜缓不宜急，需谨慎防变，暂避锋芒。")
    elif score >= -4:
        tone = ("情况不太妙，最好先放一放或者换个时机，别硬来。" if modern
                else "多有不顺，宜暂缓或另寻良机，不可强为。")
    else:
        tone = ("各项指标都不好，现在千万别动手，先稳住、等等看，以后再说。" if modern
                else "凶险之兆，当下不宜行动，宜止宜守，待机再图。")

    tip = Q.QM_YONG_MEANING.get(yong, "")

    extra = ""
    if yong_info and yong_info.get("is_kong"):
        extra = ("现在正好赶上「空亡」，意思是事情暂时落空、没有着落，建议等过几天（出空之后）再推进，千万别着急。"
                 if modern else "用神落空亡，眼下无着落，宜待出空(约旬内)之期再图，切勿急进。")
    if yong_info and yong_info.get("is_ma"):
        extra += ("另外，这个位置带「驿马」，说明事情会变化比较快，适合趁势行动。" if modern
                  else "用神临驿马，事主速动，宜趁势而行。")

    return f"{tone}\n{tip}\n{extra}".strip()
