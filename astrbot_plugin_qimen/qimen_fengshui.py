# -*- coding: utf-8 -*-
"""
奇门遁甲风水模块：环境方位分析、空间布局调整建议。
古法依据：《神奇之门》《开悟之门》。
九宫对应方位：坎1=北 坤2=西南 震3=东 巽4=东南 中5=中 乾6=西北 兑7=西 艮8=东北 离9=南。
核心逻辑：遍历九宫辨吉凶（吉门+吉星+三奇为吉方，凶门+凶星为凶方）->
          吉方宜动宜用，凶方宜静宜镇。
"""
try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


_SANQI = ("乙", "丙", "丁")
_JI_MEN = ("开门", "休门", "生门")
_XIONG_MEN = ("死门", "惊门", "伤门")
_XIONG_STAR = ("天蓬", "天芮", "天柱")


def _gong_dir_desc(g):
    bagua, fang, wx = Q.GONG.get(g, ("", "", ""))
    return fang, bagua, wx


def _gong_fengshui_score(info):
    g = info.get("gong")
    if g == 5:
        return 0
    s = 0
    men = info.get("men", "")
    star = info.get("tianpan_star", "")
    shen = info.get("shen", "")
    yi = info.get("dipan", "")
    tp_yi = info.get("tianpan_yi", "")
    if info.get("is_kong"):
        s -= 2
    if men in _JI_MEN:
        s += 2
    elif men in _XIONG_MEN:
        s -= 2
    if Q.STAR_FORTUNE.get(star) == "吉":
        s += 1
    elif star in _XIONG_STAR:
        s -= 1
    if Q.SHEN_FORTUNE.get(shen) == "吉":
        s += 1
    elif Q.SHEN_FORTUNE.get(shen) == "凶":
        s -= 1
    if yi in _SANQI:
        s += 1
    if tp_yi in _SANQI:
        s += 1
    return s


def _men_laytip(men, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    return {
        "开门": _t("利开门纳气，宜设主入口、办公洽谈", "适合开门进气，建议在这个方向开门或设主入口、办公洽谈"),
        "休门": _t("宜安养休息，适设卧室、休憩区", "适合休养休息，可以设卧室、休息区"),
        "生门": _t("财气所在，宜设财位、经营生财之所", "财气在这里，适合设财位、做生意赚钱的地方"),
        "伤门": _t("煞气偏重，不宜久居，宜置静物化解", "煞气比较重，不适合久待，放点静物化解一下"),
        "杜门": _t("宜闭塞隐蔽，适设储藏、技术研习之所", "适合隐蔽，可以设储藏室、技术研习的地方"),
        "景门": _t("文书之位，宜设书房、文书宣传之处", "文书的位置，适合设书房、做宣传策划的地方"),
        "死门": _t("凶位，宜静不宜动，忌设卧房灶台", "凶位，适合安静少动，别在这里设卧室或灶台"),
        "惊门": _t("口舌之位，忌设会客谈判之所", "容易口舌的位置，别在这里设会客或谈判的地方"),
    }.get(men, "")


_YONG_EVENT = {
    "生门": "求财经营", "开门": "出行开创", "休门": "安养和合",
    "伤门": "争竞索债", "杜门": "隐藏钻研", "景门": "文书考学",
    "死门": "田土丧葬", "惊门": "官非口舌",
    "六合": "婚姻合作", "玄武": "失物防盗", "白虎": "刑伤武威",
    "太阴": "暗谋庇护", "腾蛇": "虚惊缠绕", "九天": "远行扬威",
    "九地": "固守潜伏", "直符": "自身运势",
    "天芮": "疾病隐患", "天心": "医药疗愈", "天辅": "文教考试",
    "天冲": "武事进取", "天蓬": "险难盗贼", "天任": "稳积蓄",
    "天英": "文名火光", "天柱": "破败争斗", "天禽": "中正平稳",
}


def _event_desc(question):
    """依问题关键词提取事项简述，使同用神不同事项产出不同方案。"""
    if not question:
        return "所问之事"
    q = question
    if "办公室" in q or "办公位" in q or "办公" in q:
        return "办公环境布局"
    if "卧室" in q or "床位" in q or "睡房" in q:
        return "卧室床位布局"
    if "店铺" in q or "商铺" in q or "店面" in q:
        return "店铺选址布局"
    if "房子" in q or "住宅" in q or "房屋" in q or "买房" in q:
        return "住宅风水堪察"
    if "座位" in q or "朝向" in q:
        return "座位朝向选择"
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
    if "装修" in q or "装饰" in q or "装潢" in q:
        return "装修装饰"
    if "选址" in q or "选位置" in q:
        return "选址定局"
    if "财位" in q:
        return "财位布局"
    if "煞气" in q or "化煞" in q:
        return "化煞调整"
    return "所问之事"


def fengshui(pp, style="modern"):
    """风水模块主函数。返回结构化结果 dict。"""
    try:
        return _fengshui_impl(pp, style=style)
    except Exception as e:
        return {
            "module": "风水",
            "title": "风水环境",
            "auspicious_sectors": [],
            "inauspicious_sectors": [],
            "key_sector": "未定",
            "layout_advice": [],
            "environment": f"风水推断受阻：{e}",
        }


def _fengshui_impl(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG

    gongs = pp.get("gongs", {})
    question = pp.get("question", "")
    event_desc = _event_desc(question)
    yong = Q.pick_yongshen_qm(question)
    yong_g, yong_kind, yong_info = (None, None, None)
    if yong:
        yong_g, yong_kind, yong_info = QG.find_yong_gong(pp, yong)
    yong_score = None
    if yong_g is not None and yong_g != 5:
        yong_score = _gong_fengshui_score(gongs.get(yong_g, {}))

    auspicious = []
    inauspicious = []
    scored = []

    for g, info in gongs.items():
        if g == 5:
            continue
        fang, bagua, wx = _gong_dir_desc(g)
        s = _gong_fengshui_score(info)
        men = info.get("men", "")
        star = info.get("tianpan_star", "")
        shen = info.get("shen", "")
        yi = info.get("dipan", "")
        tp_yi = info.get("tianpan_yi", "")
        parts = []
        if men:
            parts.append(men)
        if star:
            parts.append(star)
        if shen:
            parts.append(shen)
        if yi in _SANQI:
            parts.append(f"三奇{yi}")
        combo = "、".join(parts) if parts else _t("无明显组合", "没有特别的组合")
        scored.append((g, fang, bagua, s, combo, men, star, info))

    for g, fang, bagua, s, combo, men, star, info in scored:
        highlight = _t("（用神所临，本问关键方位）", "（用神在这里，是这件事的关键方位）") if (yong and g == yong_g) else ""
        if s >= 3:
            auspicious.append((fang, _t(
                f"{bagua}宫临{combo}，吉气汇聚，为大吉之方{highlight}",
                f"{bagua}宫有{combo}，吉气很旺，是个大吉的方位{highlight}"
            )))
        elif s >= 1:
            auspicious.append((fang, _t(
                f"{bagua}宫临{combo}，吉气渐生，可用之方{highlight}",
                f"{bagua}宫有{combo}，有点吉气，可以用的方位{highlight}"
            )))
        elif s <= -3:
            inauspicious.append((fang, _t(
                f"{bagua}宫临{combo}，凶煞较重，宜镇宜避{highlight}",
                f"{bagua}宫有{combo}，煞气比较重，最好化解或避开{highlight}"
            )))
        elif s <= -1:
            inauspicious.append((fang, _t(
                f"{bagua}宫临{combo}，气机不畅，宜静不宜动{highlight}",
                f"{bagua}宫有{combo}，气场不太顺，适合安静少动{highlight}"
            )))

    zhifu_g = pp.get("zhifu_gong")
    # 关键方位优先取用神所临之宫，无用神则退回全局最高分之宫
    if yong and yong_g is not None and yong_g != 5:
        key_g = yong_g
    else:
        key_g = zhifu_g
        best_s = -1000
        for g, fang, bagua, s, combo, men, star, info in scored:
            if s > best_s:
                best_s, key_g = s, g
    if key_g is not None and key_g != 5:
        kfang, kbagua, kwx = _gong_dir_desc(key_g)
        kinfo = gongs.get(key_g, {})
        kcombo_parts = [x for x in [kinfo.get("men", ""), kinfo.get("tianpan_star", ""),
                                    kinfo.get("shen", "")] if x]
        if yong and key_g == yong_g:
            key_sector = _t(
                f"就【{event_desc}】而言，{kfang}方（{kbagua}宫，临{'、'.join(kcombo_parts)}），为用神【{yong}】所临，乃本问之关键方位",
                f"就【{event_desc}】来说，{kfang}方（{kbagua}宫，有{'、'.join(kcombo_parts)}），是用神【{yong}】所在的位置，是这件事的关键方位"
            )
        else:
            key_sector = _t(
                f"{kfang}方（{kbagua}宫，临{'、'.join(kcombo_parts)}），为全局气运枢纽",
                f"{kfang}方（{kbagua}宫，有{'、'.join(kcombo_parts)}），是整体气运的核心方位"
            )
    else:
        key_sector = _t("中宫为枢，八方待察", "中宫是核心，八方还需要看")

    layout_advice = []
    # 用神所临方位的专属布局建议，使不同所问得出不同方案
    if yong and yong_g is not None and yong_g != 5:
        yfang, ybagua, ywx = _gong_dir_desc(yong_g)
        ykinfo = gongs.get(yong_g, {})
        ymen = ykinfo.get("men", "")
        meaning = Q.QM_YONG_MEANING.get(yong, "")
        tip = _men_laytip(ymen, style=style)
        yong_advice = _t(
            f"所问【{event_desc}】，以【{yong}】为用神，落{yfang}方（{ybagua}宫）。",
            f"所问【{event_desc}】，以【{yong}】为用神，落在{yfang}方（{ybagua}宫）。"
        )
        if meaning:
            yong_advice += f"（{meaning}）"
        if ykinfo.get("is_kong"):
            yong_advice += _t(
                "此方逢空亡，气散不聚，所问之事宜待出空，暂不宜在此方强为。",
                "这个方向赶上空亡，气散了聚不住，这件事要等出空之后再说，暂时别在这个方向硬来。"
            )
        elif yong_score is not None and yong_score >= 1:
            yong_advice += (_t("此方宫气吉顺，宜重点启用、设为相关功能区。", "这个方向宫气不错，适合重点使用、设成相关的功能区。") + tip) if tip else _t("此方宫气吉顺，宜重点启用、设为相关功能区。", "这个方向宫气不错，适合重点使用、设成相关的功能区。")
        elif yong_score is not None and yong_score <= -1:
            yong_advice += (_t("此方宫气欠佳，宜静宜镇，不宜在此方强谋所问之事。", "这个方向宫气不太好，适合安静少动，别在这个方向硬做这件事。") + tip) if tip else _t("此方宫气欠佳，宜静宜镇，不宜在此方强谋所问之事。", "这个方向宫气不太好，适合安静少动，别在这个方向硬做这件事。")
        else:
            yong_advice += _t("此方宫气平平，宜适中启用、勿过动过静。", "这个方向宫气一般，适当使用就行，别太折腾也别太闲着。")
        layout_advice.append(yong_advice)
    for g, fang, bagua, s, combo, men, star, info in scored:
        if s >= 1:
            tip = _men_laytip(men, style=style)
            layout_advice.append(_t(
                f"{fang}方（{bagua}宫）吉方宜动宜用，{tip}。",
                f"{fang}方（{bagua}宫）吉利的方位适合多用多动，{tip}。"
            ) if tip else _t(
                f"{fang}方（{bagua}宫）吉方宜动宜用，可作主要功能区。",
                f"{fang}方（{bagua}宫）吉利的方位适合多用多动，可以作为主要功能区。"
            ))
        elif s <= -1:
            tip = _men_laytip(men, style=style)
            layout_advice.append(_t(
                f"{fang}方（{bagua}宫）凶方宜静宜镇，{tip}。",
                f"{fang}方（{bagua}宫）不吉利的方位适合安静少动，{tip}。"
            ) if tip else _t(
                f"{fang}方（{bagua}宫）凶方宜静不宜动，宜置静物化解。",
                f"{fang}方（{bagua}宫）不吉利的方位适合安静少动，放点静物化解一下。"
            ))
    for g in pp.get("kong_gongs", []):
        if g == 5:
            continue
        dg = Q.DUI_GONG.get(g)
        layout_advice.append(_t(
            f"{Q.GONG[g][1]}方（{Q.GONG[g][0]}宫）逢空亡，气散不聚，"
            f"宜待出空或以对冲{Q.GONG[dg][1]}方补气（{'' if dg is None else Q.GONG[dg][0]}宫）。",
            f"{Q.GONG[g][1]}方（{Q.GONG[g][0]}宫）赶上空亡，气散聚不住，"
            f"等出空之后再用，或者用对面的{Q.GONG[dg][1]}方来补气（{'' if dg is None else Q.GONG[dg][0]}宫）。"
        ))
    if not layout_advice:
        layout_advice.append(_t(
            "各宫吉凶平和，布局以中正均衡为要，吉方略动、凶方略静即可。",
            "各个方位吉凶比较平和，布局以均衡为主，吉利的方位稍微多用用、不吉利的方位安静点就行。"
        ))

    ji_n = sum(1 for _, _, _, s, _, _, _, _ in scored if s >= 1)
    xiong_n = sum(1 for _, _, _, s, _, _, _, _ in scored if s <= -1)
    if ji_n >= 3 and ji_n > xiong_n:
        env_base = _t(
            "整体环境吉气充沛，八方多吉，宜居宜业，气势通达。",
            "整体环境吉气很旺，好方位多，适合居住和做事，气场通畅。"
        )
    elif xiong_n >= 3 and xiong_n > ji_n:
        env_base = _t(
            "整体环境煞气偏重，凶方较多，须重点化解镇煞，慎择方位。",
            "整体环境煞气比较重，不好的方位多，要重点化解，小心选方位。"
        )
    elif ji_n > 0 and xiong_n > 0:
        env_base = _t(
            "环境吉凶参半，须趋吉避凶，善用吉方、镇伏凶方，方可藏风聚气。",
            "环境好坏参半，要用好吉利的方位、化解不吉利的方位，才能聚住气。"
        )
    else:
        env_base = _t(
            "环境气机平和，无大吉大凶，以均衡布局、顺应自然为佳。",
            "环境气场比较平和，没有特别好的也没有特别差的，均衡布局、顺应自然就好。"
        )
    event_type = _YONG_EVENT.get(yong, "") if yong else ""
    if event_type:
        environment = _t(
            f"就所问【{event_desc}】（{event_type}）而言，{env_base}",
            f"就所问【{event_desc}】（{event_type}）来说，{env_base}"
        )
    else:
        environment = _t(
            f"就所问【{event_desc}】而言，{env_base}",
            f"就所问【{event_desc}】来说，{env_base}"
        )

    return {
        "module": "风水",
        "title": "风水环境",
        "auspicious_sectors": auspicious,
        "inauspicious_sectors": inauspicious,
        "key_sector": key_sector,
        "layout_advice": layout_advice,
        "environment": environment,
        "zhifu_gong": zhifu_g,
        "key_gong": key_g,
    }
