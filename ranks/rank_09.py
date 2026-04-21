# -*- coding: utf-8 -*-
"""
Ранг 9: Сеятель первых борозд.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Первая борозда", "material": "земля", "desc": "Каменной мотыгой. Твёрдая, руки в мозолях.", "prompt": "first plough furrow, stone hoe cut, virgin soil"},
    {"name": "Ячмень-монококк", "material": "зерно", "desc": "Посев. Дикие зёрна, но прижились.", "prompt": "einkorn barley seeds, first sowing, wild ancestors"},
    {"name": "Канава от ручья", "material": "глина", "desc": "Вода течёт. Риск есть, но надо.", "prompt": "irrigation ditch from stream, clay lined"},
    {"name": "Сорняк вырван", "material": "корень", "desc": "Пустырник. Конкурирует с пшеницей.", "prompt": "uprooted weed, wild oat competitor"},
    {"name": "Дикие бобы", "material": "бобы", "desc": "Кустарник у склона. Колется.", "prompt": "wild legume pods, thorny bush harvest"},
    {"name": "Перекопанная грядка", "material": "земля", "desc": "После дождя. Глина липкая.", "prompt": "rain-dug garden bed, sticky clay soil"},
    {"name": "Камни с поля", "material": "камень", "desc": "Мешают корням. На стены пойдут.", "prompt": "field clearing stones, future wall material"},
    {"name": "Первые всходы", "material": "росток", "desc": "Зелёные, хрупкие. Как надежда.", "prompt": "first green sprouts, fragile seedlings, hope"},
    {"name": "Дренаж прорыт", "material": "камень", "desc": "Вода уходит. Корни не гниют.", "prompt": "drainage trench, field water management"},
    {"name": "Навоз для удобрения", "material": "навоз", "desc": "Вонь, но урожай будет тяжёлый.", "prompt": "manure fertilizer pile, stinking but fertile"},
    {"name": "Мульча из травы", "material": "трава", "desc": "Влага уйдёт медленнее.", "prompt": "straw mulch layer, moisture conservation"},
    {"name": "Ограда от коз", "material": "ветки", "desc": "Колючая. Объедают всходы.", "prompt": "thorn branch fence, goat protection"},
]

RITUALS = [
    {"name": "Первый урожай", "material": "колос", "desc": "Собран. Мало, но своё. Начало.", "prompt": "first harvest sheaf, einkorn wheat, agricultural beginning"},
    {"name": "Зерно в крови", "material": "кремень", "desc": "Обряд посева. Кровь на земле — плодородие.", "prompt": "blood sowing ritual, flint blade, fertility offering"},
    {"name": "Каменная мотыга", "material": "кремень и дерево", "desc": "Освящена. Теперь орудие, не просто камень.", "prompt": "consecrated stone hoe, agricultural tool ritual"},
]

def get_deed_text():
    return "Вскапываю. Произвожу еду — новый вид власти."

def get_image_prompt():
    return (
        "First ploughing in PPN Anatolia, 8000 BC, stone hoe breaking soil, wild wheat nearby, photorealistic, 8k"
    )
