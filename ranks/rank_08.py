# -*- coding: utf-8 -*-
"""
Ранг 8: Строитель чужого дома.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Первый ряд стены", "material": "известняк", "desc": "Неровный, но держится без глины.", "prompt": "first limestone wall course, rough but stable"},
    {"name": "Глина с соломой", "material": "глина", "desc": "Перемычка. Ноги в грязи до колен.", "prompt": "straw tempered clay mortar, mud mixing"},
    {"name": "Блок с каменоломни", "material": "известняк", "desc": "Тяжёлый. Плечи горят.", "prompt": "heavy quarry block, shoulder strain, construction"},
    {"name": "Каменная плита пола", "material": "песчаник", "desc": "Прямоугольная. Первый ровный пол.", "prompt": "rectangular sandstone floor slab, first flat surface"},
    {"name": "Деревянный столб", "material": "дуб", "desc": "Не дуб, но крепкий. Держит крышу.", "prompt": "wooden roof post, Anatolian oak substitute"},
    {"name": "Штукатурка стен", "material": "глина", "desc": "Трещины заделаны. Дождь не пройдёт.", "prompt": "mud plaster wall coating, crack repair"},
    {"name": "Дренаж вокруг дома", "material": "камень", "desc": "Вода уходит. Фундамент сухой.", "prompt": "foundation drainage channel, stone lined"},
    {"name": "Прямоугольный очаг", "material": "камень", "desc": "Не круглый, как дома. Новый порядок.", "prompt": "rectangular hearth stone, new fire geometry"},
    {"name": "Глина для штукатурки", "material": "глина", "desc": "Три ходки. Спина сломана.", "prompt": "plaster clay haul, three trips, exhausted builder"},
    {"name": "Дверной проём", "material": "камень", "desc": "Первый дом с входом. Граница.", "prompt": "doorway lintel stone, threshold definition"},
    {"name": "Каменный порог", "material": "известняк", "desc": "Граница между улицей и домом.", "prompt": "limestone doorstep, inside outside boundary"},
    {"name": "Известковый раствор", "material": "известь", "desc": "Руки жгут. Стены белеют.", "prompt": "lime plaster mix, burning hands, white walls"},
]

RITUALS = [
    {"name": "Первый прямоугольный дом", "material": "камень и глина", "desc": "Закончен. Не шалаш — дом. Переход.", "prompt": "first completed rectangular house, stone and mud, milestone"},
    {"name": "Камень закладки", "material": "известняк", "desc": "Под столб. Кровь раба. Освящение.", "prompt": "foundation deposit stone, blood consecration, building ritual"},
    {"name": "Обряд нового очага", "material": "зола", "desc": "Огонь перенесён из старого мира. Непрерывность.", "prompt": "hearth transfer ritual, Levant fire to Anatolia, continuity"},
]

def get_deed_text():
    return "Кладу блоки. Строю для других, сплю в шалаше."

def get_image_prompt():
    return (
        "PPN builders erecting stone wall, Anatolia 8500 BC, mud plaster, limestone blocks, photorealistic, 8k"
    )
