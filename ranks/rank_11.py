# -*- coding: utf-8 -*-
"""
Ранг 11: Держатель зерна.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Зерно в яме", "material": "пшеница", "desc": "Глина сверху. Печать из соломы.", "prompt": "wheat in storage pit, clay sealed, straw plug"},
    {"name": "Мера для охотников", "material": "камень", "desc": "Полная. Справедливо.", "prompt": "full stone measure for hunters, fair allocation"},
    {"name": "Запасы проверены", "material": "зерно", "desc": "Сухие. Без червей. Целы.", "prompt": "inspected grain reserves, dry and clean"},
    {"name": "Отказ в мере", "material": "камень", "desc": "Норма есть норма. Даже старейшинам.", "prompt": "refused extra measure, ration limit enforced"},
    {"name": "Запись на камне", "material": "известняк", "desc": "Кто сколько взял. Долги.", "prompt": "stone accounting tablet, who took what, debt record"},
    {"name": "Урожай с полей", "material": "колос", "desc": "Весы каменные. Споров нет.", "prompt": "field harvest on stone scales, weighed grain"},
    {"name": "Посевной материал", "material": "зерно", "desc": "Лучшие зёрна. Не на еду — на будущее.", "prompt": "prime seed stock, reserved for planting, future crop"},
    {"name": "Ключ-камень", "material": "известняк", "desc": "Тяжёлый. Один у меня. Запасы закрыты.", "prompt": "heavy stone granary key, sole access, authority symbol"},
    {"name": "Зерно на неделю", "material": "мера", "desc": "Не больше. Голодная весна возможна.", "prompt": "weekly grain ration, scarcity planning"},
    {"name": "Пломбы на ямах", "material": "глина", "desc": "Целы. Никто не воровал.", "prompt": "intact clay seals on storage pits, no theft"},
    {"name": "Дань соседям", "material": "зерно", "desc": "Мир стоит дороже мешка.", "prompt": "tribute grain for neighbors, peace payment"},
    {"name": "Излишки в котёл", "material": "зерно", "desc": "Праздник. Но после посева.", "prompt": "surplus grain into communal pot, feast reserved"},
]

RITUALS = [
    {"name": "Житница-гробница", "material": "камень", "desc": "Под ней кости предка. Хранит зерно.", "prompt": "granary tomb, ancestor bones beneath, protective spirit"},
    {"name": "Камень изобилия", "material": "известняк", "desc": "Когда он полон — племя сыто.", "prompt": "abundance stone marker, full granary symbol"},
    {"name": "Обряд первой меры", "material": "зерно", "desc": "Новый урожай. Первый раздатчик — я.", "prompt": "first measure ritual, new harvest distribution, granary master"},
]

def get_deed_text():
    return "Контролирую житницы. Голод — моё оружие."

def get_image_prompt():
    return (
        "PPN granary pit in Anatolia, 7000 BC, stored einkorn wheat, clay-sealed, photorealistic, 8k"
    )
