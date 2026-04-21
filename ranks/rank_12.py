# -*- coding: utf-8 -*-
"""
Ранг 12: Созидатель места.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "T-образный столб", "material": "известняк", "desc": "Тонна камня. Руки рабов, мой приказ.", "prompt": "massive T-shaped limestone pillar, erected by command"},
    {"name": "Кости в фундаменте", "material": "человеческие кости", "desc": "Чужие, но крепкие. Держат вечно.", "prompt": "human bones in foundation trench, structural sacrifice"},
    {"name": "Круг каменный", "material": "известняк", "desc": "Геометрия точная, как небо над Тавром.", "prompt": "perfect stone circle, geometric precision, Taurus alignment"},
    {"name": "Площадка храма", "material": "выравненная земля", "desc": "Вид на долину. Ветер. Близость небес.", "prompt": "temple platform, hilltop view, sacred wind"},
    {"name": "Рельеф лисы", "material": "высеченный камень", "desc": "Символ племени. В T-столбе. Хитрость богов.", "prompt": "fox relief on T-pillar, tribal symbol, divine cunning"},
    {"name": "Камень закладки", "material": "известняк", "desc": "Первый. Кровь, песок, крики.", "prompt": "foundation stone, blood and sand, inaugural sacrifice"},
    {"name": "Стена круга", "material": "известняк", "desc": "Без зазора. Как я сказал.", "prompt": "dry stone circle wall, perfect fit, monumental"},
    {"name": "Имя в камне", "material": "заложенная плита", "desc": "Не высечено, но заложено. Потомки найдут.", "prompt": "hidden name plate under pillar, secret legacy"},
    {"name": "Обряд открытия", "material": "кровь", "desc": "Первый круг готов. Боги спустились.", "prompt": "circle opening ritual, divine descent, completion"},
    {"name": "Разрушенный круг", "material": "блоки", "desc": "Камни для нового, выше. Старый должен умереть.", "prompt": "deliberately destroyed older circle, stones recycled"},
    {"name": "Пара столбов", "material": "известняк", "desc": "Два гиганта. Симметрия. Страх и власть.", "prompt": "twin T-pillars, symmetrical, monumental power"},
    {"name": "Столб с лицом", "material": "известняк", "desc": "Моё лицо, скрытое. Только боги видят.", "prompt": "T-pillar with hidden face carving, subtle relief"},
]

RITUALS = [
    {"name": "Великий столб", "material": "монолит", "desc": "Центральный. Три человека в высоту. Вечность.", "prompt": "central monolithic T-pillar, five meters tall, eternal monument"},
    {"name": "Круг жертвенный", "material": "камень", "desc": "Замкнут. Имя в камне. Конец пути.", "prompt": "completed sacrificial stone circle, name in stone, journey end"},
    {"name": "Фундамент с костями", "material": "кости", "desc": "Десятки черепов. Круг на плечах предков.", "prompt": "foundation filled with skulls, ancestral support, dark megalith"},
]

def get_deed_text():
    return "Воздвигаю мегалиты. Моё имя — история."

def get_image_prompt():
    return (
        "Göbekli Tepe megalith construction, Anatolia 7000 BC, massive T-pillars, carved reliefs, photorealistic, 8k"
    )
