# -*- coding: utf-8 -*-
"""
Ранг 6: Старший у очага.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Грудь лосося", "material": "мясо", "desc": "Старейшинам. Лучший кусок.", "prompt": "salmon breast portion, elder allocation, red meat"},
    {"name": "Хвост лосося", "material": "мясо", "desc": "Детям. Мало, но есть.", "prompt": "salmon tail portion, children food, scrap"},
    {"name": "Решение спора", "material": "камень", "desc": "Шкура крупнее — ближе к огню. Справедливо.", "prompt": "judgment stone, dispute resolution marker"},
    {"name": "Приказ дозора", "material": "кремень", "desc": "Кто идёт. Выбрал тех, кто не спит.", "prompt": "watch duty flint token, night guard assignment"},
    {"name": "Запрет костра", "material": "зола", "desc": "Экономим дрова. Зима близко.", "prompt": "fire ban ash mark, fuel conservation sign"},
    {"name": "Правило: без дров — без мяса", "material": "кость", "desc": "Работает. Никто не спорит.", "prompt": "no firewood no meat rule bone, labor law"},
    {"name": "Общая яма", "material": "глина", "desc": "Для запасов. Все копают, я контролирую.", "prompt": "communal storage pit, clay sealed, food reserve"},
    {"name": "Решение: нож тому, кто заточил", "material": "кремень", "desc": "Суд. Справедливость орудия.", "prompt": "tool ownership judgment, flint knife verdict"},
    {"name": "Договор с волком", "material": "клык", "desc": "Старого не трогаем. Держит чужаков.", "prompt": "wolf pact token, fang amulet, territorial agreement"},
    {"name": "Порция сироте", "material": "мясо", "desc": "Тайный дар. Пока никто не видел.", "prompt": "hidden orphan meat portion, secret charity"},
    {"name": "Отвар от кашля", "material": "корень", "desc": "Лечебный. Варил три часа.", "prompt": "medicinal root decoction, cough remedy, stone bowl"},
    {"name": "Запрет на ячмень", "material": "колос", "desc": "До августа. Пусть дозреет.", "prompt": "barley harvest ban marker, unripe grain protection"},
    {"name": "Распорядок: женщины мелют", "material": "камень", "desc": "Мужчины чинят сети. Порядок.", "prompt": "gender labor division stone, grinding assignment"},
    {"name": "Суд над вором", "material": "пепел", "desc": "Изгнание на три ночи. Пощада.", "prompt": "thief trial ash mark, exile sentence, three nights"},
    {"name": "Передача власти", "material": "кость", "desc": "Кость очага. Новый старший.", "prompt": "hearth bone authority transfer, leadership token"},
    {"name": "Договор о браке", "material": "раковина", "desc": "Союз племён. Обмен сёстрами.", "prompt": "marriage alliance shell contract, inter-tribal union"},
    {"name": "Распределение шкур", "material": "шкура", "desc": "Зимние запасы. Кому какая.", "prompt": "winter fur distribution, bison hide allocation"},
]

RITUALS = [
    {"name": "Кость очага", "material": "кость", "desc": "Символ власти. Кто держит — тот решает.", "prompt": "hearth authority bone, senior power symbol, sacred object"},
    {"name": "Судебный камень", "material": "известняк", "desc": "На нём высечены все приговоры.", "prompt": "judgment stone with carved sentences, law tablet"},
    {"name": "Мирное соглашение", "material": "берёста", "desc": "Конец вражды. Кровь не пролита.", "prompt": "peace treaty birch bark, blood oath cancelled"},
]

def get_deed_text():
    return "Распределяю. Решаю. Вершина закрытого мира."

def get_image_prompt():
    return (
        "Natufian senior at central campfire, Levant 9600 BC, meat distribution, social hierarchy, photorealistic, 8k"
    )
