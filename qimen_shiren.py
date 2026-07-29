# -*- coding: utf-8 -*-
"""
奇门遁甲识人模块：性格分析、才干识别、人际关系与人才任用。
古法依据：《神奇之门》《开悟之门》《奇门真髓》。
核心逻辑：以直符（统领/自身）为核心 -> 天盘星辨性格 -> 八门辨才干行动 ->
          八神辨潜藏特质 -> 六合太阴看人际 -> 综合定职业取向与建议。
"""
try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


_STAR_PERSONALITY = {
    "天心": "精明干练，善于管理与统筹，心思缜密，处事周全",
    "天芮": "包容内敛，好学善思，但易隐忍积郁，宜修心养性",
    "天辅": "文雅温和，好学重教，有文化修养，辅佐之才",
    "天冲": "性急躁动，进取果敢，雷厉风行，但易冲动冒失",
    "天蓬": "胆大果决，敢于冒险，智谋深沉，但易铤而走险",
    "天任": "稳重踏实，勤勉担当，任劳任怨，但稍显保守",
    "天英": "热情外露，急躁好名，聪慧明理，但易急功近利",
    "天柱": "刚直不阿，能言善辩，有破败之勇，但易刚愎自用",
    "天禽": "中正平和，圆融通达，不偏不倚，有大将之风",
}

_STAR_TALENT = {
    "天心": "管理调度、战略规划、医药疗愈",
    "天芮": "学术钻研、问题诊断、教育培养",
    "天辅": "文化教育、文案策划、辅助参谋",
    "天冲": "突击攻坚、竞技对抗、速决事务",
    "天蓬": "开拓冒险、情报谋略、危机处置",
    "天任": "基础建设、农事经营、稳健运营",
    "天英": "宣传传播、文书名气、公关外交",
    "天柱": "辩论谈判、破局革新、危机公关",
    "天禽": "综合协调、居中斡旋、统筹大局",
}

_STAR_WEAKNESS = {
    "天心": "过于精明算计，易失人情温度",
    "天芮": "隐忍过度，问题积压难发",
    "天辅": "过于文弱，决断力不足",
    "天冲": "急躁冲动，易虎头蛇尾",
    "天蓬": "胆大妄为，易涉险招祸",
    "天任": "过于保守，错失良机",
    "天英": "急躁好名，易浮夸不实",
    "天柱": "刚愎自用，易招口舌是非",
    "天禽": "随和易失主见，随波逐流",
}

_MEN_TALENT = {
    "开门": "开创开拓、通达成事之才",
    "休门": "调和养息、息事宁人之才",
    "生门": "经营生财、产业运营之才",
    "伤门": "争竞进取、索债捕盗之才",
    "杜门": "技术钻研、隐蔽保密之才",
    "景门": "文书策划、考试宣传之才",
    "死门": "田产管理、殡葬肃穆之才",
    "惊门": "口才辩驳、诉讼维权之才",
}

_SHEN_HIDDEN = {
    "直符": "正气凛然，有统御之威，贵人缘厚",
    "腾蛇": "心思多变，虚惊缠绕，想象力丰富但易多疑",
    "太阴": "深谋远虑，暗中布局，有贵人暗助",
    "六合": "善交际应酬，和合圆融，人脉广泛",
    "白虎": "刚烈威猛，有武勇之气，但易招刑伤",
    "玄武": "机智深沉，善谋略，但易生狡诈之嫌",
    "九地": "沉稳低调，固守潜伏，有守成之能",
    "九天": "志存高远，昂扬进取，有远大抱负",
}

_MEN_CAREER = {
    "开门": "宜仕途官职、行政管理、创业开店",
    "休门": "宜后勤保障、人事调和、休养服务",
    "生门": "宜商贸经营、金融投资、产业开发",
    "伤门": "宜军警竞技、催收维权、突击攻坚",
    "杜门": "宜技术研发、保密安防、工艺钻研",
    "景门": "宜文教宣传、考试升学、策划设计",
    "死门": "宜房产田土、殡葬祭祀、农事矿业",
    "惊门": "宜法律诉讼、播音主持、辩论口才",
}


def _find_day_gan_gong(pp):
    day_gz = pp.get("day_gz", "")
    if not day_gz:
        return None
    day_gan = day_gz[0]
    for g, info in pp.get("gongs", {}).items():
        if info.get("dipan") == day_gan:
            return g
    return None


def _find_shen_gong(pp, shen_name):
    for g, info in pp.get("gongs", {}).items():
        if info.get("shen") == shen_name:
            return g, info
    return None, None


def _target_desc(question):
    """依问题关键词辨识所识之人，使同用神不同对象产出不同论断。"""
    if not question:
        return "所识之人"
    q = question
    if "相亲" in q:
        return "相亲对象"
    if "合作" in q or "合伙人" in q:
        return "合作之人"
    if "领导" in q or "上司" in q or "老板" in q:
        return "上级领导"
    if "下属" in q or "部下" in q or "员工" in q:
        return "下属部属"
    if "对象" in q or "恋人" in q or "男友" in q or "女友" in q:
        return "恋爱对象"
    return "所识之人"


def shiren(pp, target="general", style="modern"):
    """识人模块主函数。返回结构化结果 dict。"""
    try:
        return _shiren_impl(pp, target, style=style)
    except Exception as e:
        return {
            "module": "识人",
            "title": "识人用人",
            "personality": f"识人推断受阻：{e}",
            "talents": [],
            "weaknesses": [],
            "relationships": "未定",
            "career_fit": "未定",
            "advice": "盘面信息不足，建议重新起局。",
        }


def _shiren_impl(pp, target, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG

    gongs = pp.get("gongs", {})
    zhifu_g = pp.get("zhifu_gong")
    zhifu_star = pp.get("zhifu_star", "")
    zhishi_men = pp.get("zhishi_men", "")

    # 以所问之事的用神落宫取人，不同所问（合作/领导/下属）取不同宫位与星性
    question = pp.get("question", "")
    target_desc = _target_desc(question)
    yong = Q.pick_yongshen_qm(question)
    yong_g, yong_kind, yong_info = (None, None, None)
    if yong:
        yong_g, yong_kind, yong_info = QG.find_yong_gong(pp, yong)
    if yong and yong_g is not None and yong_g != 5:
        self_g = yong_g
        self_info = yong_info or gongs.get(self_g, {})
    else:
        self_g = _find_day_gan_gong(pp) or zhifu_g
        self_info = gongs.get(self_g, {}) if self_g else {}
    self_star = self_info.get("tianpan_star", "") or zhifu_star
    self_men = self_info.get("men", "") or zhishi_men
    self_shen = self_info.get("shen", "")

    personality = _t(
        f"所识为【{target_desc}】，{_STAR_PERSONALITY.get(self_star, '性情平和，待人以诚。')}",
        f"这个【{target_desc}】，{_STAR_PERSONALITY.get(self_star, '性格比较平和，待人真诚。')}"
    )
    if yong and yong_g is not None and yong_g != 5:
        personality += _t(
            f"（本问以【{yong}】为用神，落{Q.GONG[yong_g][0]}宫，取天盘{self_star}辨其性情。）",
            f"（这件事以【{yong}】为用神，落在{Q.GONG[yong_g][0]}宫，用天盘{self_star}来看性格。）"
        )
    elif self_g and self_g != 5:
        bagua = Q.GONG[self_g][0]
        wx = Q.GONG[self_g][2]
        personality += _t(
            f"（落{bagua}宫·{wx}，性格受此方位气机影响。）",
            f"（落在{bagua}宫·{wx}，性格受这个方位气场的影响。）"
        )

    talents = []
    if self_star in _STAR_TALENT:
        talents.append(_t(
            f"星{self_star}主：{_STAR_TALENT[self_star]}。",
            f"天盘{self_star}代表：{_STAR_TALENT[self_star]}。"
        ))
    if self_men in _MEN_TALENT:
        talents.append(_t(
            f"门{self_men}主：{_MEN_TALENT[self_men]}。",
            f"八门{self_men}代表：{_MEN_TALENT[self_men]}。"
        ))
    if self_shen in _SHEN_HIDDEN:
        talents.append(_t(
            f"神{self_shen}主：{_SHEN_HIDDEN[self_shen]}。",
            f"八神{self_shen}代表：{_SHEN_HIDDEN[self_shen]}。"
        ))
    if not talents:
        talents.append(_t("才干中正，可堪通用之任。", "才干比较中正，一般的事都能胜任。"))

    weaknesses = []
    if self_star in _STAR_WEAKNESS:
        weaknesses.append(_STAR_WEAKNESS[self_star])
    if self_men in ("死门", "惊门", "伤门"):
        weaknesses.append(_t(
            f"临{self_men}，行事易带偏执，须防偏激。",
            f"临{self_men}，做事容易偏执，要注意别太极端。"
        ))
    if self_shen in ("腾蛇", "玄武", "白虎"):
        modern_trait = ('多疑善变' if self_shen == '腾蛇' else '狡黠多变' if self_shen == '玄武' else '刚烈易怒')
        weaknesses.append(_t(
            f"临{self_shen}，潜藏{modern_trait}之性。",
            f"临{self_shen}，骨子里有点{modern_trait}。"
        ))
    if self_info.get("is_kong"):
        weaknesses.append(_t(
            "自身落空亡，志向易落空，须防虚浮不实。",
            "自身赶上空亡，志向容易落空，要注意别太浮夸。"
        ))
    if not weaknesses:
        weaknesses.append(_t("无明显短板，仍宜修身自省。", "没有明显的短板，但还是要注意修身自省。"))

    liuhe_g, liuhe_info = _find_shen_gong(pp, "六合")
    taiyin_g, taiyin_info = _find_shen_gong(pp, "太阴")
    rel_parts = []
    if liuhe_g:
        rel_parts.append(_t(
            f"六合在{Q.GONG[liuhe_g][0]}宫，主婚姻和合、人脉交际，善结善缘",
            f"六合在{Q.GONG[liuhe_g][0]}宫，代表婚姻和合、人脉交际，善于结善缘"
        ))
    if taiyin_g:
        rel_parts.append(_t(
            f"太阴在{Q.GONG[taiyin_g][0]}宫，有贵人暗中扶持，宜低调行事",
            f"太阴在{Q.GONG[taiyin_g][0]}宫，有贵人暗中帮忙，适合低调做事"
        ))
    zhuke = _zhuke_brief(pp, self_g, self_info, style=style)
    if zhuke:
        rel_parts.append(zhuke)
    relationships = "；".join(rel_parts) + "。" if rel_parts else _t(
        "人际关系平稳，以诚相待自得人和。",
        "人际关系比较平稳，真诚待人自然能得人和。"
    )

    career_parts = []
    if self_men in _MEN_CAREER:
        career_parts.append(_MEN_CAREER[self_men])
    if self_star == "天心":
        career_parts.append(_t("亦宜医药健康、管理咨询", "也适合医药健康、管理咨询"))
    elif self_star == "天辅":
        career_parts.append(_t("亦宜教育文化、培训辅导", "也适合教育文化、培训辅导"))
    elif self_star == "天蓬":
        career_parts.append(_t("亦宜风险投资、危机管理", "也适合风险投资、危机管理"))
    career_fit = "；".join(career_parts) + "。" if career_parts else _t(
        "职业取向中正，可因才适任。",
        "职业取向比较中正，可以根据才能来安排。"
    )

    advice_bits = []
    if self_star in ("天冲", "天英"):
        advice_bits.append(_t(
            "性急宜缓，三思后行，戒急用忍。",
            "性子急要注意慢下来，三思后行，别太冲动。"
        ))
    if self_star == "天蓬":
        advice_bits.append(_t(
            "胆大须防妄为，守正方能远行。",
            "胆子大要注意别乱来，守正才能走得远。"
        ))
    if self_star == "天芮":
        advice_bits.append(_t(
            "宜修心养性，疏导积郁，持续学习精进。",
            "适合修心养性，疏导心里的郁闷，持续学习提升。"
        ))
    if self_men in ("死门", "惊门"):
        advice_bits.append(_t(
            "临凶门宜慎言慎行，防口舌刑伤。",
            "临凶门要注意言行谨慎，小心口舌是非。"
        ))
    if self_info.get("is_kong"):
        advice_bits.append(_t(
            "自身落空，宜脚踏实地，勿好高骛远。",
            "自身落空亡，要脚踏实地，别好高骛远。"
        ))
    if not advice_bits:
        advice_bits.append(_t(
            "扬长避短，发挥天赋，修身立德，自然亨通。",
            "扬长避短，发挥自己的天赋，修身养德，自然顺利。"
        ))
    advice = _t(f"对【{target_desc}】：", f"对【{target_desc}】的建议：") + "".join(advice_bits)

    return {
        "module": "识人",
        "title": "识人用人",
        "personality": personality,
        "talents": talents,
        "weaknesses": weaknesses,
        "relationships": relationships,
        "career_fit": career_fit,
        "advice": advice,
        "self_gong": self_g,
        "self_star": self_star,
        "self_men": self_men,
        "self_shen": self_shen,
        "target": target,
    }


def _zhuke_brief(pp, yong_gong, yong_info, style="modern"):
    modern = (style != "classic")

    def _t(c, m):
        return m if modern else c

    try:
        from . import qimen_duangua as QG
    except ImportError:
        import qimen_duangua as QG
    r = QG.analyze_zhuke(pp, yong_gong, yong_info)
    if not r:
        return ""
    if "利客" in r or "主动" in r:
        return _t("为人主动进取，宜率先垂范", "为人比较主动积极，适合带头做事")
    if "利主" in r or "静守" in r:
        return _t("为人沉稳内敛，宜以静制动", "为人比较沉稳内敛，适合以静制动")
    return _t("为人攻守均衡，进退有度", "为人攻守比较均衡，进退有分寸")
