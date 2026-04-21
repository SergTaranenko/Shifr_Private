# -*- coding: utf-8 -*-
"""
Ранг 2: Терпимый работник.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Мех воды из кожи", "material": "кожа", "desc": "Полный, тяжёлый. Руки ноют.", "prompt": "water skin made of animal hide, full and heavy"},
    {"name": "Камень для стены очага", "material": "известняк", "desc": "Тяжёлый блок. Тащил полдня.", "prompt": "heavy limestone block for hearth wall"},
    {"name": "Шкура газели", "material": "шкура", "desc": "Свежая, ещё тёплая. Весит много.", "prompt": "fresh gazelle hide, warm and heavy"},
    {"name": "Дрова дуба", "material": "дуб", "desc": "Связка. Колол полдня.", "prompt": "bundle of oak firewood, chopped"},
    {"name": "Глина для обмазки", "material": "глина", "desc": "Мокрая, липкая. Для швов.", "prompt": "wet clay for plastering, sticky mud"},
    {"name": "Песок для выделки", "material": "песок", "desc": "Речной, для обработки шкур.", "prompt": "river sand for hide processing, abrasive"},
    {"name": "Тростник для плетения", "material": "тростник", "desc": "С реки. Колется, но гнётся.", "prompt": "reeds for weaving, flexible stems"},
    {"name": "Камень для зернотёрки", "material": "песчаник", "desc": "Плоский, тяжёлый. Для зерна.", "prompt": "flat sandstone grinding stone, quern"},
    {"name": "Волокна крапивы", "material": "крапива", "desc": "Для шнуров. Жгут руки.", "prompt": "nettle fibers for cordage, stinging"},
    {"name": "Кость для лопатки", "material": "кость", "desc": "Широкая. Для копания.", "prompt": "broad bone spatula, digging tool"},
    {"name": "Ветки для шалаша", "material": "ивняк", "desc": "Гибкие. Для каркаса.", "prompt": "willow branches for hut frame, flexible"},
    {"name": "Камень для костра", "material": "кремень", "desc": "Кремнёвый. Искры при ударе.", "prompt": "flint fire stone, sparks when struck"},
    {"name": "Глина для посуды", "material": "глина", "desc": "Лепная. Формуешь руками.", "prompt": "pottery clay, hand-shaped bowl"},
    {"name": "Обломок обсидиана", "material": "обсидиан", "desc": "Чёрный, острый. Редкая находка.", "prompt": "obsidian flake, black volcanic glass"},
    {"name": "Кожа для ремней", "material": "кожа", "desc": "Выделанная. Режется полосами.", "prompt": "tanned leather strips for straps"},
    {"name": "Каменная чаша", "material": "известняк", "desc": "Выдолбленная. Для воды.", "prompt": "limestone bowl, hand-carved"},
    {"name": "Пакля из травы", "material": "трава", "desc": "Для набивки щелей.", "prompt": "dried grass caulking for hut walls"},
]

RITUALS = [
    {"name": "Кость с отметинами", "material": "кость", "desc": "Календарь работ. Пять насечек — пять дней труда.", "prompt": "work calendar bone, five notches, labor record"},
    {"name": "Рог лося", "material": "рог", "desc": "Трофей. Сила ношения.", "prompt": "moose antler trophy, strength symbol"},
    {"name": "Ожерелье из клыков", "material": "клык", "desc": "Статус работника. Не просто вещь.", "prompt": "necklace of animal fangs, status symbol"},
]

def get_deed_text():
    return "Тащу, копаю, ношу. Последний кусок — мне."

def get_image_prompt():
    return (
        "Natufian worker carrying heavy load, Levant 11500 BC, sweat, dust, limestone terrain, exhausted, photorealistic, 8k"
    )
