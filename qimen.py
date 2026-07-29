# -*- coding: utf-8 -*-
"""
奇门遁甲起局排盘（时家奇门·转盘法）。
古法依据：《烟波钓叟歌》《奇门遁甲秘笈大全》。
排盘四盘：天盘九星、地盘六仪三奇、人盘八门、神盘八神。
"""
import datetime
import random

try:
    from . import qimen_data as Q
except ImportError:
    import qimen_data as Q


# ===================== 月支（节气定月建）=====================
JIEQI_MZ = [
    (2, 4, "寅"), (3, 6, "卯"), (4, 5, "辰"), (5, 6, "巳"),
    (6, 6, "午"), (7, 7, "未"), (8, 8, "申"), (9, 8, "酉"),
    (10, 8, "戌"), (11, 7, "亥"), (12, 7, "子"), (1, 6, "丑"),
]


def get_month_zhi(dt):
    candidates = sorted(JIEQI_MZ, key=lambda x: (x[0], x[1]))
    cur = "子"
    for m, d, z in candidates:
        if (dt.month, dt.day) >= (m, d):
            cur = z
        else:
            break
    if dt.month == 1 and dt.day < 6:
        cur = "子"
    return cur


# ===================== 干支历（复用六爻模块并补时柱）=====================
def _get_year_gz(dt):
    year = dt.year
    if (dt.month, dt.day) < (2, 4):
        year -= 1
    idx = (year - 4) % 60
    return Q.LIU_SHI_JIA_ZI[idx]


def _get_month_gz(dt):
    month_zhi = get_month_zhi(dt)
    yz = _get_year_gz(dt)
    year_gan = yz[0]
    wuhu = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊",
            "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬",
            "戊": "甲", "癸": "甲"}
    yin_gan = wuhu.get(year_gan, "丙")
    zhi_idx = Q.DI_ZHI.index(month_zhi)
    yin_gan_idx = Q.TIAN_GAN.index(yin_gan)
    offset = (zhi_idx - 2) % 12
    gan = Q.TIAN_GAN[(yin_gan_idx + offset) % 10]
    return gan + month_zhi


def _get_day_gz(dt):
    base = datetime.date(1900, 1, 1)
    cur = datetime.date(dt.year, dt.month, dt.day)
    diff = (cur - base).days
    idx = (diff + 10) % 60
    return Q.LIU_SHI_JIA_ZI[idx]


def hour_to_zhi(hour):
    """小时(0-23)转时支。23点归子时（早子时）。"""
    if hour == 23 or hour == 0:
        return "子"
    # 1-2丑,3-4寅,...用 (hour+1)//2 映射
    idx = ((hour + 1) // 2) % 12
    return Q.DI_ZHI[idx]


def _get_hour_gz(dt):
    """时柱干支：五鼠遁起时。"""
    day_gz = _get_day_gz(dt)
    day_gan = day_gz[0]
    wushu = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙",
             "丙": "戊", "辛": "戊", "丁": "庚", "壬": "庚",
             "戊": "壬", "癸": "壬"}
    zi_gan = wushu.get(day_gan, "甲")
    zhi = hour_to_zhi(dt.hour)
    zhi_idx = Q.DI_ZHI.index(zhi)
    zi_gan_idx = Q.TIAN_GAN.index(zi_gan)
    offset = zhi_idx
    gan = Q.TIAN_GAN[(zi_gan_idx + offset) % 10]
    return gan + zhi


# ===================== 节气定局 =====================
def get_jieqi(dt):
    """返回当前所处节气名（近似）。"""
    cur = None
    for m, d, name in Q.JIEQI_DATES:
        if (dt.month, dt.day) >= (m, d):
            cur = name
        else:
            break
    if dt.month == 1 and dt.day < 6:
        cur = "冬至"  # 小寒前属上年冬至
    return cur


def get_ju(dt):
    """定局：返回 (局数1-9, 阴阳遁, 元)。
    古法：每节气分上中下三元，每元5日，以甲己日为元首。
    用日干支定元：找日柱所在甲己旬首，再据节气内已过天数定上中下元。
    """
    jieqi = get_jieqi(dt)
    ju_info = Q.JIEQI_JU.get(jieqi, (1, 7, 4, "阳"))
    up, mid, down, yin_yang = ju_info
    day_gz = _get_day_gz(dt)
    day_idx = Q.LIU_SHI_JIA_ZI.index(day_gz)
    # 定元：每个节气15天分三元，每元5天。
    # 以该节气的基准日为起点计算已过天数。节气近似日见 JIEQI_DATES。
    # 日干支定元法：甲己日为各元之首。上元起甲子/甲午，中元起甲辰/甲寅...
    # 实际古法：看日干支在该节气(15日)内的位置：第1-5天上元，6-10中元，11-15下元。
    # 用节气起始日到当日的天数差定元，精确对应"每5日一元"。
    jieqi_start = _jieqi_start_date(dt)
    if jieqi_start is not None:
        days_passed = (datetime.date(dt.year, dt.month, dt.day) - jieqi_start).days
        yuan_idx = days_passed // 5  # 0上 1中 2下
        if yuan_idx > 2:
            yuan_idx = 2  # 超出节气范围则归下元
    else:
        # 兜底：用甲己日定元（日干甲或己为元首）
        day_gan = day_gz[0]
        gan_idx = Q.TIAN_GAN.index(day_gan)
        # 甲己->0(上), 乙庚->1, 丙辛->2, 丁壬->3, 戊癸->4
        offset_in_yuan = gan_idx // 2
        # 用日支进一步校正：子午卯酉为上元，寅申巳亥为中元，辰戌丑未为下元
        day_zhi = day_gz[1]
        zhi_yuan = {"子": 0, "午": 0, "卯": 0, "酉": 0,
                    "寅": 1, "申": 1, "巳": 1, "亥": 1,
                    "辰": 2, "戌": 2, "丑": 2, "未": 2}
        yuan_idx = zhi_yuan.get(day_zhi, 0)
    ju_table = [up, mid, down]
    ju = ju_table[yuan_idx]
    yuan_name = ["上元", "中元", "下元"][yuan_idx]
    return ju, yin_yang, yuan_name, jieqi


def _jieqi_start_date(dt):
    """返回当前节气起始的公历日期（date对象）。"""
    cur_jieqi = get_jieqi(dt)
    # 找当前节气在 JIEQI_DATES 中的日期
    for m, d, name in Q.JIEQI_DATES:
        if name == cur_jieqi:
            # 节气日期可能在当前年，也可能在上一年（1月初属上年冬至）
            year = dt.year
            if (m, d) > (dt.month, dt.day):
                year -= 1
            return datetime.date(year, m, d)
    return None


# ===================== 九宫飞布 =====================
def fly_order(start_gong, yin_yang):
    """返回从start宫开始的九宫飞行序列（9个宫）。
    阳遁顺飞：1->2->3->4->5->6->7->8->9（按洛书顺序循环）
    阴遁逆飞：1->9->8->7->6->5->4->3->2
    """
    order = Q.GONG_ORDER[:]  # [1..9]
    if yin_yang == "阴":
        order = order[::-1]  # 逆序
    # 中5在飞行序列中保留，但布仪时5宫寄2宫
    s = order.index(start_gong)
    return [order[(s + i) % 9] for i in range(9)]


def place_dipan(ju, yin_yang):
    """排地盘六仪三奇。返回 {宫: 仪}。
    阳遁：戊从(局数)宫起顺飞；阴遁：戊从(局数)宫起逆飞。
    中5寄坤2宫。
    """
    order = Q.GONG_ORDER[:]
    if yin_yang == "阴":
        order = order[::-1]
    s = order.index(ju)
    dipan = {}
    for i, yi in enumerate(Q.YI_ORDER_YANG):  # 戊己庚辛壬癸丁丙乙
        gong = order[(s + i) % 9]
        if gong == 5:
            continue  # 中5寄2，不单独放
        dipan[gong] = yi
    # 5宫的仪寄到2宫（叠加显示）
    five_yi = Q.YI_ORDER_YANG[order.index(5) - s] if (order.index(5) - s) >= 0 else None
    # 更稳妥：计算落到5宫的那个仪
    five_idx = (order.index(5) - s) % 9
    five_yi = Q.YI_ORDER_YANG[five_idx]
    dipan[5] = five_yi  # 中宫保留仪，显示时标注寄2宫
    return dipan


# ===================== 定直符直使 =====================
def find_zhifu_zhishi(hour_gz, dipan):
    """根据时柱所在旬，定直符宫与直使门。
    时柱旬首 -> 对应仪 -> 该仪在地盘哪宫 = 直符宫。
    直符宫的九星=直符星，八门=直使门。
    返回 (zhifu_gong, zhifu_star, zhishi_men, xun_shou, xun_yi)
    """
    idx = Q.LIU_SHI_JIA_ZI.index(hour_gz)
    xun_head_idx = idx - (idx % 10)  # 旬首在60甲子中的索引
    xun_shou_gz = Q.LIU_SHI_JIA_ZI[xun_head_idx]
    xun_yi = Q.XUN_SHOU[xun_shou_gz]  # 旬首对应仪
    # 找该仪在地盘哪宫
    zhifu_gong = None
    for g, yi in dipan.items():
        if yi == xun_yi:
            zhifu_gong = g
            break
    zhifu_star = Q.GONG_STAR.get(zhifu_gong, "天禽")
    # 天禽居中5时，寄坤2，直符星随天芮或天禽寄2
    if zhifu_gong == 5:
        zhifu_star = "天禽"
    zhishi_men = Q.GONG_MEN.get(zhifu_gong, "开门")  # 中宫无门，取开门为备
    return zhifu_gong, zhifu_star, zhishi_men, xun_shou_gz, xun_yi


# ===================== 排天盘九星 =====================
def place_tianpan(zhifu_star, zhifu_gong, hour_gan, dipan, yin_yang):
    """天盘九星：直符星加临时干所在宫，其余九星随之转。
    找时干在地盘哪宫，天盘直符落到该宫，其余按九宫顺序顺/逆排。
    返回 {宫: 天盘星}
    """
    # 时干在地盘的位置
    if hour_gan in Q.YI_WUXING:  # 仪或奇
        target_gong = None
        for g, yi in dipan.items():
            if yi == hour_gan:
                target_gong = g
                break
        if target_gong is None:
            target_gong = zhifu_gong
    else:
        target_gong = zhifu_gong
    # 天盘星序：以直符星为起点，按九宫飞行顺序排列其余8星
    # 星的固定宫序：按 GONG_ORDER 对应的星
    star_seq = []  # 按阳遁顺飞顺序的9星
    for g in Q.GONG_ORDER:
        star_seq.append(Q.GONG_STAR[g])
    if yin_yang == "阴":
        star_seq = star_seq[::-1]
    s = star_seq.index(zhifu_star)
    gong_order = Q.GONG_ORDER[:] if yin_yang == "阳" else Q.GONG_ORDER[::-1]
    t = gong_order.index(target_gong)
    tianpan = {}
    for i in range(9):
        star = star_seq[(s + i) % 9]
        gong = gong_order[(t + i) % 9]
        tianpan[gong] = star
    return tianpan


def place_tianpan_yi(zhifu_gong, xun_yi, hour_gan, dipan, yin_yang):
    """排天盘六仪三奇（天盘干）。
    与天盘九星同理：直符仪（旬首仪）加临时干所在宫，其余仪按九宫顺序随之转。
    返回 {宫: 天盘干}
    """
    # 时干在地盘的位置
    if hour_gan in Q.YI_WUXING:
        target_gong = None
        for g, yi in dipan.items():
            if yi == hour_gan:
                target_gong = g
                break
        if target_gong is None:
            target_gong = zhifu_gong
    else:
        target_gong = zhifu_gong
    # 仪序：按 GONG_ORDER 对应的地盘仪
    order = Q.GONG_ORDER[:]
    if yin_yang == "阴":
        order = order[::-1]
    yi_seq = [dipan.get(g, "") for g in order]
    s = yi_seq.index(xun_yi) if xun_yi in yi_seq else 0
    t = order.index(target_gong) if target_gong in order else 0
    tianpan_yi = {}
    for i in range(9):
        yi = yi_seq[(s + i) % 9]
        gong = order[(t + i) % 9]
        tianpan_yi[gong] = yi
    return tianpan_yi


# ===================== 排人盘八门 =====================
# 八门固定宫序（洛书序，阳遁顺飞用）：休1 死2 伤3 杜4 (中5无门) 开6 惊7 生8 景9
# 即八门按宫数 1,2,3,4,6,7,8,9 的顺序排列
MEN_GONG_FLY_ORDER = [1, 2, 3, 4, 6, 7, 8, 9]


def place_renpan(zhishi_men, zhishi_gong, hour_zhi, yin_yang):
    """人盘八门飞布（古法转盘）。
    直使门加临时支所在宫，其余八门按九宫飞布顺序随之转动（阳遁顺飞、阴遁逆飞），中宫无门跳过。
    返回 {宫: 门}
    """
    # 时支对应宫
    zhi_gong = {
        "子": 1, "午": 9, "卯": 3, "酉": 7,
        "丑": 8, "寅": 8, "未": 2, "申": 2,
        "辰": 4, "巳": 4, "戌": 6, "亥": 6,
    }
    target_gong = zhi_gong.get(hour_zhi, zhishi_gong)
    if target_gong == 5:
        target_gong = 2  # 中宫无门，寄坤2

    # 飞布宫序：阳遁顺飞 1->2->3->4->6->7->8->9，阴遁逆飞
    fly = MEN_GONG_FLY_ORDER[:]
    if yin_yang == "阴":
        fly = fly[::-1]  # 9->8->7->6->4->3->2->1

    # 八门本宫序（与 fly 同序对应）：按 fly 宫序取各宫本位门
    men_in_fly_order = [Q.GONG_MEN[g] for g in fly]
    # 直使门在飞布序列中的起点位置
    s = men_in_fly_order.index(zhishi_men)
    # 目标宫在飞布序列中的位置
    t = fly.index(target_gong)

    renpan = {}
    for i in range(8):
        men = men_in_fly_order[(s + i) % 8]
        gong = fly[(t + i) % 8]
        renpan[gong] = men
    return renpan


# ===================== 排神盘八神 =====================
def place_shenpan(zhifu_star, tianpan, yin_yang):
    """神盘八神：直符神随天盘直符星所在宫，其余按顺序转。
    返回 {宫: 神}
    """
    # 天盘直符星所在宫
    zhifu_star_gong = None
    for g, star in tianpan.items():
        if star == zhifu_star:
            zhifu_star_gong = g
            break
    shen_seq = Q.SHEN_ORDER[:]  # 直符腾蛇太阴六合白虎玄武九地九天
    if yin_yang == "阴":
        shen_seq = shen_seq[::-1]
    gong_order = Q.GONG_ORDER[:] if yin_yang == "阳" else Q.GONG_ORDER[::-1]
    t = gong_order.index(zhifu_star_gong) if zhifu_star_gong in gong_order else 0
    shenpan = {}
    for i in range(8):
        shen = shen_seq[i]
        gong = gong_order[(t + i) % 9]
        if gong != 5:  # 中宫不放神（寄2宫）
            shenpan[gong] = shen
    return shenpan


# ===================== 旬空 =====================
def get_kong_wang(hour_gz):
    """时柱旬空（两个地支）。"""
    idx = Q.LIU_SHI_JIA_ZI.index(hour_gz)
    xun_head = idx - (idx % 10)
    head_zhi_idx = xun_head % 12
    used = [Q.DI_ZHI[(head_zhi_idx + k) % 12] for k in range(10)]
    kong = [z for z in Q.DI_ZHI if z not in used]
    return kong


def zhi_to_gong_map():
    """地支->宫（用于查空亡落哪宫）。"""
    return {
        "子": 1, "午": 9, "卯": 3, "酉": 7,
        "丑": 8, "寅": 8, "未": 2, "申": 2,
        "辰": 4, "巳": 4, "戌": 6, "亥": 6,
    }


# ===================== 马星 =====================
def get_ma(hour_zhi):
    """驿马：申子辰马在寅, 寅午戌马在申, 巳酉丑马在亥, 亥卯未马在巳。"""
    ma_map = {
        "申": "寅", "子": "寅", "辰": "寅",
        "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥",
        "亥": "巳", "卯": "巳", "未": "巳",
    }
    return ma_map.get(hour_zhi)


# ===================== 完整起局 =====================
def qimen_paipan(question, dt=None):
    """奇门遁甲起局排盘。返回完整结构 dict。"""
    if dt is None:
        dt = datetime.datetime.now()
    year_gz = _get_year_gz(dt)
    month_gz = _get_month_gz(dt)
    day_gz = _get_day_gz(dt)
    hour_gz = _get_hour_gz(dt)
    hour_gan = hour_gz[0]
    hour_zhi = hour_gz[1]

    ju, yin_yang, yuan, jieqi = get_ju(dt)
    dipan = place_dipan(ju, yin_yang)
    zhifu_gong, zhifu_star, zhishi_men, xun_shou, xun_yi = find_zhifu_zhishi(hour_gz, dipan)
    tianpan = place_tianpan(zhifu_star, zhifu_gong, hour_gan, dipan, yin_yang)
    tianpan_yi = place_tianpan_yi(zhifu_gong, xun_yi, hour_gan, dipan, yin_yang)
    renpan = place_renpan(zhishi_men, zhifu_gong, hour_zhi, yin_yang)
    shenpan = place_shenpan(zhifu_star, tianpan, yin_yang)
    kong = get_kong_wang(hour_gz)
    ma = get_ma(hour_zhi)
    zhi2gong = zhi_to_gong_map()
    kong_gongs = sorted(set(zhi2gong.get(z) for z in kong))
    ma_gong = zhi2gong.get(ma) if ma else None

    # 组装每宫信息
    gongs = {}
    for g in Q.GONG_ORDER:
        bagua, fang, wx = Q.GONG[g]
        info = {
            "gong": g, "bagua": bagua, "fang": fang, "wx": wx,
            "dipan": dipan.get(g, ""),
            "tianpan_star": tianpan.get(g, ""),
            "tianpan_yi": tianpan_yi.get(g, ""),
            "men": renpan.get(g, ""),
            "shen": shenpan.get(g, ""),
            "is_zhifu_gong": (g == zhifu_gong),
            "is_kong": (g in kong_gongs),
            "is_ma": (g == ma_gong),
        }
        gongs[g] = info

    return {
        "question": question,
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "year_gz": year_gz, "month_gz": month_gz, "day_gz": day_gz, "hour_gz": hour_gz,
        "jieqi": jieqi, "ju": ju, "yin_yang": yin_yang, "yuan": yuan,
        "xun_shou": xun_shou, "xun_yi": xun_yi,
        "zhifu_gong": zhifu_gong, "zhifu_star": zhifu_star, "zhishi_men": zhishi_men,
        "dipan": dipan, "tianpan": tianpan, "tianpan_yi": tianpan_yi, "renpan": renpan, "shenpan": shenpan,
        "kong": kong, "kong_gongs": kong_gongs, "ma": ma, "ma_gong": ma_gong,
        "gongs": gongs,
        "hour_gan": hour_gan, "hour_zhi": hour_zhi,
    }
