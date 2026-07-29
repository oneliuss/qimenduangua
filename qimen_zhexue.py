# -*- coding: utf-8 -*-
"""
奇门遁甲哲学模块：从盘象提炼易理哲思、阴阳之道与人生启示。
古法依据：《周易》《道德经》《烟波钓叟歌》《神奇之门》。
核心逻辑：观整体格局定核心哲理 -> 阴遁阳遁辨阴阳消长 -> 应期与驿马论时机 ->
          吉凶格局引申人生课题 -> 配以经典箴言。
"""
try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


_QUOTES = {
    "伏吟": "《易》曰：'君子以顺德，积小以高大。' 守正待时，厚积薄发。",
    "反吟": "《易》曰：'穷则变，变则通，通则久。' 变则通，通则久。",
    "吉多": "《老子》曰：'道法自然。' 顺势而为，无为而无不为。",
    "凶多": "《易》曰：'天行健，君子以自强不息。' 修德进业，转危为安。",
    "平和": "《中庸》曰：'致中和，天地位焉，万物育焉。' 守中致和，万事咸宁。",
    "空亡": "《金刚经》云：'一切有为法，如梦幻泡影。' 空而不空，待时而动。",
    "马星": "《易》曰：'变通者，趣时者也。' 顺时应变，动静得宜。",
}


def _raw_gejus(pp):
    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG
    return QG.detect_geju(pp)


def _geju_names(pp):
    return [n for n, _, _ in _raw_gejus(pp)]


def _principle(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    names = _geju_names(pp)
    gejus = _raw_gejus(pp)
    ji = sum(1 for _, _, f in gejus if f == "吉")
    xiong = sum(1 for _, _, f in gejus if f == "凶")
    if "伏吟" in names:
        return _t("守正待时，静以修身。伏吟之象，气机内敛不动，当以静制动、蓄势待发。",
                  "稳住等时机，静下心来修自身。伏吟的格局，气场内敛不动，应该以静制动、积蓄力量等待时机。")
    if "反吟" in names:
        return _t("变通无常，顺势流转。反吟之象，气机反复冲荡，当以变应变、随圆就方。",
                  "灵活变通，顺势而为。反吟的格局，气场反复冲荡，应该以变应变、灵活调整。")
    if ji >= 2 and ji > xiong:
        return _t("顺势而为，乘势而上。吉格汇聚，天时地利人和，当因势利导、积极进取。",
                  "顺势去做，乘势而上。好的格局聚在一起，天时地利人和都占了，应该因势利导、积极进取。")
    if xiong >= 2 and xiong > ji:
        return _t("修德进业，转否为泰。凶格叠见，气机壅塞，当反求诸己、积德修善以待时转。",
                  "修德积善，把不好的局面扭转过来。凶的格局比较多，整体气场不太通顺，应该从自身找原因、多做好事等时机转变。")
    return _t("致中和，守正道。盘象平和，吉凶相参，当不偏不倚、中正而行。",
              "走中庸之道，守住正道。盘面比较平和，好坏都有，应该不偏不倚、中正行事。")


def _pattern_wisdom(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    gejus = _raw_gejus(pp)
    if not gejus:
        return _t("盘无显著格局，平淡之中见真章，凡事以稳为主、以诚为本。",
                  "盘面上没有特别突出的格局，平淡之中见真功夫，凡事以稳为主、以诚为本。")
    parts = []
    for name, desc, ft in gejus[:4]:
        if ft == "吉":
            parts.append(_t(
                f"【{name}】示吉：{desc}。启示：善用天时，把握机缘，顺势成事。",
                f"【{name}】是吉利的：{desc}。启示：好好利用天时，把握机会，顺势把事做成。"
            ))
        elif ft == "凶":
            parts.append(_t(
                f"【{name}】示凶：{desc}。启示：谨防隐患，未雨绸缪，化凶为吉。",
                f"【{name}】不太好：{desc}。启示：小心隐患，提前防范，把不好的转成好的。"
            ))
        else:
            parts.append(_t(
                f"【{name}】示平：{desc}。启示：进退有度，不急不躁，静观其变。",
                f"【{name}】影响一般：{desc}。启示：进退有分寸，不急不躁，静静观察变化。"
            ))
    return " ".join(parts)


def _yin_yang(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    yin_yang = pp.get("yin_yang", "")
    ju = pp.get("ju", 0)
    if yin_yang == "阳":
        return _t(
            f"本局为阳遁{ju}局，阳气渐盛、生机外发。"
            f"阳主动、主刚、主显，事宜进取外拓、明察果断；"
            f"然阳极生阴，盛极当防亢龙有悔，宜刚柔并济。",
            f"这一局是阳遁{ju}局，阳气越来越旺、生机往外发。"
            f"阳代表动、刚、外放，适合进取拓展、看清形势果断行动；"
            f"不过阳到极点会转阴，太盛了要防止盛极而衰，刚柔要配合着来。"
        )
    if yin_yang == "阴":
        return _t(
            f"本局为阴遁{ju}局，阴气渐长、气机内收。"
            f"阴主静、主柔、主藏，事宜收敛内守、谋定后动；"
            f"然阴极生阳，否极泰来，宜守中蓄势以待阳生。",
            f"这一局是阴遁{ju}局，阴气越来越重、气场往内收。"
            f"阴代表静、柔、收藏，适合收敛内守、想好了再动；"
            f"不过阴到极点会转阳，坏到头了会好转，守住中心积蓄力量等阳气生发。"
        )
    return _t("阴阳未明，当观气机消长，动静相宜。",
              "阴阳不太明确，要看气场的消长变化，动静搭配着来。")


def _timing_wisdom(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    ma = pp.get("ma")
    kong = pp.get("kong", [])
    names = _geju_names(pp)
    parts = []
    if "伏吟" in names:
        parts.append(_t(
            "伏吟主迟，时机未至，宜静养待时，不可揠苗助长。",
            "伏吟说明事情慢，时机还没到，适合静心等待，不能急于求成。"
        ))
    if "反吟" in names:
        parts.append(_t(
            "反吟主速而反复，机来须疾握，亦须防朝令夕改。",
            "反吟说明事情来得快但容易反复，机会来了要赶紧抓住，也要防止变来变去。"
        ))
    if kong:
        parts.append(_t(
            f"旬空在{'、'.join(kong)}，当下事如泡影，待填实冲空之期方有着落。",
            f"空亡在{'、'.join(kong)}，眼下的事情像泡泡一样不实在，要等出空之后有着落。"
        ))
    if ma:
        parts.append(_t(
            f"驿马在{ma}，变动之机已显，宜顺时而动、择机而行。",
            f"驿马在{ma}，变动的时机已经显现，适合顺时而动、挑好时机行动。"
        ))
    if not parts:
        parts.append(_t(
            "时机平顺，无急无滞，宜顺其自然、水到渠成。",
            "时机比较平顺，不急也不卡，顺其自然、水到渠成就好。"
        ))
    parts.append("《易》云：'随时之义大矣哉。' 知时识机，进退不失其正。")
    return "".join(parts)


def _life_lesson(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    gejus = _raw_gejus(pp)
    names = _geju_names(pp)
    ji = sum(1 for _, _, f in gejus if f == "吉")
    xiong = sum(1 for _, _, f in gejus if f == "凶")
    if "伏吟" in names:
        return _t("处伏吟之境，当守正不移、深耕本业，待时而动，不可妄进。",
                  "处在伏吟的局面，应该守住正道不动摇、深耕本职，等时机再动，不能盲目冒进。")
    if "反吟" in names:
        return _t("处反吟之境，当灵活变通、不执一端，预留退路，方能在反复中立足。",
                  "处在反吟的局面，应该灵活变通、别认死理，给自己留条退路，才能在反复中站住脚。")
    if xiong > ji and xiong >= 2:
        return _t("凶格多见，当反求诸己、修德积善，以德化凶、以正胜邪，静待否极泰来。",
                  "不好的格局比较多，应该从自身找原因、多修德行善，用德行化解凶险、用正气战胜邪气，静静等待否极泰来。")
    if ji > xiong and ji >= 2:
        return _t("吉格多见，当乘势而为、善用机缘，然勿忘居安思危，方能长保吉昌。",
                  "好的格局比较多，应该乘势去做、善用机会，但也别忘了居安思危，才能长久保持好运。")
    return _t("吉凶参半，当知进知退、不骄不馁，中正而行，自然逢凶化吉。",
              "好坏参半，应该知进知退、不骄傲也不气馁，中正行事，自然能逢凶化吉。")


def _quote(pp):
    names = _geju_names(pp)
    gejus = _raw_gejus(pp)
    ji = sum(1 for _, _, f in gejus if f == "吉")
    xiong = sum(1 for _, _, f in gejus if f == "凶")
    if "伏吟" in names:
        return _QUOTES["伏吟"]
    if "反吟" in names:
        return _QUOTES["反吟"]
    if pp.get("kong_gongs"):
        return _QUOTES["空亡"]
    if pp.get("ma"):
        return _QUOTES["马星"]
    if ji >= 2 and ji > xiong:
        return _QUOTES["吉多"]
    if xiong >= 2 and xiong > ji:
        return _QUOTES["凶多"]
    return _QUOTES["平和"]


def zhexue(pp, style="modern"):
    """哲学模块主函数。返回结构化结果 dict。"""
    try:
        return _zhexue_impl(pp, style=style)
    except Exception as e:
        return {
            "module": "哲学",
            "title": "易理哲思",
            "principle": f"哲思推断受阻：{e}",
            "pattern_wisdom": "",
            "yin_yang": "",
            "timing_wisdom": "",
            "life_lesson": "",
            "quote": "",
        }


_YONG_MATTER = {
    "生门": "求财之道", "开门": "开创出行之道", "休门": "安养和合之道",
    "伤门": "争竞进取之道", "杜门": "隐守钻研之道", "景门": "文书考学之道",
    "死门": "田土安葬之道", "惊门": "慎言避讼之道",
    "六合": "姻缘和合之理", "玄武": "防盗防欺之理", "白虎": "避凶远刑之理",
    "太阴": "暗谋潜行之理", "腾蛇": "处变镇定之理", "九天": "志存高远之理",
    "九地": "固守潜伏之理", "直符": "立身行事之理",
    "天芮": "养生愈病之理", "天心": "医药疗愈之理", "天辅": "修学进德之理",
    "天冲": "果决进取之理", "天蓬": "避险守正之理", "天任": "踏实积蓄之理",
    "天英": "扬名慎火之理", "天柱": "破局慎言之理", "天禽": "中正圆融之理",
}


def _yong_fortune(yong):
    if yong in Q.MEN_FORTUNE:
        return Q.MEN_FORTUNE[yong]
    if yong in Q.STAR_FORTUNE:
        return Q.STAR_FORTUNE[yong]
    if yong in Q.SHEN_FORTUNE:
        return Q.SHEN_FORTUNE[yong]
    return "中"


def _yong_state_desc(yong, yong_g, yong_info, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    if not yong or yong_g is None or yong_g == 5:
        return _t("未显于盘", "没有出现在盘上")
    info = yong_info or {}
    bagua = Q.GONG[yong_g][0]
    if info.get("is_kong"):
        return _t(f"落{bagua}宫逢空亡，气散无着", f"落在{bagua}宫赶上空亡，气散了没着落")
    if _yong_fortune(yong) == "吉":
        return _t(f"落{bagua}宫，得地得时，气机畅达", f"落在{bagua}宫，位置和时机都不错，气场通畅")
    if _yong_fortune(yong) == "凶":
        return _t(f"落{bagua}宫，气机受制，多生阻滞", f"落在{bagua}宫，气场受制，阻碍比较多")
    return _t(f"落{bagua}宫，气机平和，吉凶参半", f"落在{bagua}宫，气场平和，好坏参半")


def _yong_wisdom(yong, yong_g, yong_info, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    if not yong or yong_g is None or yong_g == 5:
        return ""
    state = _yong_state_desc(yong, yong_g, yong_info, style=style)
    info = yong_info or {}
    if info.get("is_kong"):
        tip = _t("用神逢空，事如泡影。启示：当下宜守不宜强求，待填实冲空之期，机缘自至。",
                 "用神赶上空亡，事情像泡泡一样不实在。启示：眼下适合守着别硬求，等出空之后，机缘自然就来了。")
    elif _yong_fortune(yong) == "吉":
        tip = _t("用神得地。启示：机缘已显，宜顺势而为、善用其时，勿疑勿怠。",
                 "用神位置不错。启示：机会已经显现，适合顺势去做、好好把握，别犹豫也别懈怠。")
    elif _yong_fortune(yong) == "凶":
        tip = _t("用神受制。启示：当反求诸己、修身积德，以正化邪、待时转运。",
                 "用神受制了。启示：应该从自身找原因、修身积德，用正气化解邪气、等时机转运。")
    else:
        tip = _t("用神平和。启示：进退有度、不急不躁，顺其自然方得圆满。",
                 "用神比较平和。启示：进退有分寸、不急不躁，顺其自然才能圆满。")
    return _t(f"就所问【{yong}】而言（{state}）。{tip}",
              f"就所问的【{yong}】来说（{state}）。{tip}")


def _yong_lesson(yong, yong_g, yong_info, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    if not yong or yong_g is None or yong_g == 5:
        return ""
    info = yong_info or {}
    matter = _YONG_MATTER.get(yong, "所问之事")
    if info.get("is_kong"):
        return _t(
            f"于{matter}，用神落空亡，当学耐心守候，不可强求，待时而动方有着落。",
            f"在{matter}方面，用神赶上空亡，要学会耐心等待，不能强求，等时机到了再动才有着落。"
        )
    if _yong_fortune(yong) == "吉":
        return _t(
            f"于{matter}，用神得地，当乘势修德、善用机缘，居安思危方可长保。",
            f"在{matter}方面，用神位置好，应该乘势修德、好好利用机会，居安思危才能长久保持。"
        )
    if _yong_fortune(yong) == "凶":
        return _t(
            f"于{matter}，用神受制，当忍辱负重、积德修善，以德化凶、静待否极泰来。",
            f"在{matter}方面，用神受制了，要忍辱负重、多做好事，用德行化解凶险、静静等待否极泰来。"
        )
    return _t(
        f"于{matter}，用神平和，当知进知退、中正而行，顺其自然自得圆满。",
        f"在{matter}方面，用神比较平和，应该知进知退、中正行事，顺其自然自然圆满。"
    )


def _question_theme(question):
    """依问题关键词提取主题，使用神无关之泛问亦能产出不同哲思。"""
    if not question:
        return "处世之道"
    q = question
    if "投资" in q or "生意" in q or "财" in q:
        return "求财之道"
    if "事业" in q or "工作" in q:
        return "事业之理"
    if "人生" in q:
        return "人生之悟"
    if "婚姻" in q or "感情" in q:
        return "姻缘之道"
    if "考试" in q or "学" in q:
        return "修学之道"
    if "病" in q or "健康" in q:
        return "养生之道"
    if "合作" in q or "人际" in q:
        return "和合之道"
    return "处世之道"


def _zhexue_impl(pp, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG

    question = pp.get("question", "")
    theme = _question_theme(question)
    yong = Q.pick_yongshen_qm(question)
    yong_g, yong_kind, yong_info = (None, None, None)
    if yong:
        yong_g, yong_kind, yong_info = QG.find_yong_gong(pp, yong)

    matter = _YONG_MATTER.get(yong, "") if yong else ""
    state = _yong_state_desc(yong, yong_g, yong_info, style=style)

    principle_base = _principle(pp, style=style)
    if yong and yong_g is not None and yong_g != 5:
        principle = _t(
            f"论{matter}：用神【{yong}】{state}。{principle_base}",
            f"说{matter}：用神【{yong}】{state}。{principle_base}"
        )
    elif matter:
        principle = _t(
            f"论{matter}：{principle_base}",
            f"说{matter}：{principle_base}"
        )
    else:
        principle = principle_base
    principle = _t(f"所问之题在于【{theme}】。", f"所问的主题是【{theme}】。") + principle

    pattern_base = _pattern_wisdom(pp, style=style)
    yong_wisdom = _yong_wisdom(yong, yong_g, yong_info, style=style)
    pattern_wisdom = (yong_wisdom + " " + pattern_base) if yong_wisdom else pattern_base

    lesson_base = _life_lesson(pp, style=style)
    yong_lesson = _yong_lesson(yong, yong_g, yong_info, style=style)
    life_lesson = (yong_lesson + " " + lesson_base) if yong_lesson else lesson_base
    life_lesson = _t(f"于【{theme}】，", f"在【{theme}】方面，") + life_lesson

    return {
        "module": "哲学",
        "title": "易理哲思",
        "principle": principle,
        "pattern_wisdom": pattern_wisdom,
        "yin_yang": _yin_yang(pp, style=style),
        "timing_wisdom": _timing_wisdom(pp, style=style),
        "life_lesson": life_lesson,
        "quote": _quote(pp),
        "yin_yang_label": pp.get("yin_yang", ""),
        "ju": pp.get("ju", 0),
        "gejus": _raw_gejus(pp),
    }
