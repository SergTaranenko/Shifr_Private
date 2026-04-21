# -*- coding: utf-8 -*-
"""
Ранг 3: Руки без голоса.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Костяная игла", "material": "кость лося", "desc": "Для шитья шкур. Просверлена каменным сверлом.", "prompt": "bone needle with tiny eye, freshly drilled, lying on limestone slab"},
    {"name": "Скребок лосиный", "material": "кость лося", "desc": "Полукруглый, для выделки. Режет шкуру без усилий.", "prompt": "bone scraper with curved edge, used for hide processing"},
    {"name": "Серп кремнёвый", "material": "кремень и кость", "desc": "Малый, с костяной рукоятью. Для сбора злаков.", "prompt": "small flint sickle with bone handle, sharp edge"},
    {"name": "Шнур сухожильный", "material": "сухожилия", "desc": "Крепче бересты, тоньше волоса. Для креплений.", "prompt": "sinew cord, twisted, strong, lying on birch bark"},
    {"name": "Долото костяное", "material": "кость", "desc": "Для долбления дерева и рога. Тупое, но верное.", "prompt": "bone chisel with flattened tip, woodworking tool"},
    {"name": "Гарпун трёхзубый", "material": "рог и кремень", "desc": "Для крупной рыбы. Зубья впиваются в плоть.", "prompt": "three-pronged harpoon with barbed flint tips"},
    {"name": "Наконечник стрелы", "material": "кремень", "desc": "Треугольный, острый. Летит прямо в сердце зайца.", "prompt": "triangular flint arrowhead, razor sharp"},
    {"name": "Сколок бритвенный", "material": "кремень", "desc": "Тонкий, как лист. Бреет кожу, не царапая.", "prompt": "thin flint blade, translucent edge, shaving sharp"},
    {"name": "Костяной крючок", "material": "кость птицы", "desc": "Для рыбалки. Загнутый, с зазубриной.", "prompt": "bone fish hook with barb, small and precise"},
    {"name": "Скребок для кожи", "material": "кремень", "desc": "Полукруглый. Снимает жир и мясо с внутренней стороны.", "prompt": "semicircular flint scraper for hide cleaning"},
    {"name": "Игла с ушком", "material": "кость", "desc": "Просверленная сквозь. Нить проходит свободно.", "prompt": "bone needle with large eye, polished surface"},
    {"name": "Топор-адза", "material": "кремень и рог", "desc": "Крепление в роговой втулке. Рубит и строгает.", "prompt": "adze with flint blade mounted in antler sleeve"},
    {"name": "Наконечник копья", "material": "кремень", "desc": "Длинный, узкий. Пробивает шкуру бизона.", "prompt": "long narrow flint spear tip, lanceolate shape"},
    {"name": "Нож обсидиановый", "material": "обсидиан", "desc": "Чёрный, как ночь. Острее кремня, но хрупкий.", "prompt": "obsidian blade, black volcanic glass, razor edge"},
    {"name": "Бусина яшмовая", "material": "яшма", "desc": "Просверленная. Красная, с прожилками. Украшение.", "prompt": "red jasper bead with hole, polished stone bead"},
    {"name": "Костяная флейта", "material": "кость птицы", "desc": "Первый инструмент. Звук пронзительный, как ветер.", "prompt": "bone flute with finger holes, bird bone"},
    {"name": "Ретушёр кремнёвый", "material": "кремень", "desc": "Малый сколок для доработки краёв. Точность.", "prompt": "small flint retouching tool, pressure flaked"},
]

RITUALS = [
    {"name": "Ритуальный нож с насечками", "material": "кремень и охра", "desc": "Украшен узором 'ёлочка'. Первое орудие со смыслом.", "prompt": "ritual flint knife decorated with geometric incisions, ochre stained, ceremonial tool"},
    {"name": "Обрядовая бусина", "material": "янтарь", "desc": "Прозрачная, с мёртвым насекомым внутри. Амулет.", "prompt": "Baltic amber bead with insect inclusion, ritual amulet"},
    {"name": "Костяной амулет", "material": "кость волка", "desc": "Вырезан клык. Защищает мастера от порчи.", "prompt": "wolf fang carved with protective symbols, bone amulet"},
]

def get_deed_text():
    return "Труд в мастерской. Кремнёвая пыль и костяные стружки."

def get_image_prompt():
    return (
        "Natufian toolmaker workshop, Levant 11000 BC, bone and flint tools on limestone slab, firelight, dust, photorealistic, 8k"
    )
