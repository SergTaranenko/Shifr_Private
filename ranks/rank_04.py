# -*- coding: utf-8 -*-
"""
Ранг 4: Знающий место.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "След газели", "material": "глина", "desc": "Отпечаток копыт в высохшей глине. Карта.", "prompt": "gazelle hoof print in dried clay, track impression"},
    {"name": "Ветка дикого ячменя", "material": "растение", "desc": "С колосьями. Метка места.", "prompt": "wild barley branch with ears, botanical specimen"},
    {"name": "Карта на бересте", "material": "берёза", "desc": "Схема родников и троп. Память.", "prompt": "birch bark map with notched paths and water sources"},
    {"name": "Помёт волка", "material": "помёт", "desc": "Знак территории. Знать, где опасно.", "prompt": "wolf scat, territorial marker, dried feces"},
    {"name": "Сеть рыболовная", "material": "волокна", "desc": "Из крапивы. Для заводи.", "prompt": "fishing net made of nettle fibers, mesh pattern"},
    {"name": "Копытная тропа", "material": "камень", "desc": "Отметка камнем. Вернёмся.", "prompt": "animal trail marker stone, hoof path sign"},
    {"name": "Поле дикой пшеницы", "material": "растение", "desc": "Сноп колосьев. Спеёт.", "prompt": "wild wheat sheaf, golden ears, harvest bundle"},
    {"name": "Знак на камне", "material": "кремень", "desc": "Насечка о месте. Только я знаю что.", "prompt": "map notch on limestone boulder, secret marker"},
    {"name": "Куст смолы", "material": "смола", "desc": "Для факелов. Чёрные сосуды на ветвях.", "prompt": "pine resin clusters on branch, torch material"},
    {"name": "След чужаков", "material": "пепел", "desc": "Отпечаток ноги в золе. Не наши.", "prompt": "foreign footprint in ash, stranger track"},
    {"name": "Раковина с моря", "material": "раковина", "desc": "Торговый знак. Далеко.", "prompt": "Mediterranean cowrie shell, trade item"},
    {"name": "Дубовая роща", "material": "жёлудь", "desc": "Метка границы. Наши дубы.", "prompt": "acorn cluster from oak grove, boundary marker"},
    {"name": "Солонец", "material": "соль", "desc": "Место охоты. Животные приходят.", "prompt": "salt lick deposit, white mineral crust"},
    {"name": "Перевал в горах", "material": "камень", "desc": "Новая тропа. Короче на полдня.", "prompt": "mountain pass cairn, trail shortcut marker"},
    {"name": "Гнездо перепела", "material": "яйцо", "desc": "Маленькое, пятнистое. Не трогал.", "prompt": "quail eggs in ground nest, spotted shells"},
    {"name": "Мед из дупла", "material": "мёд", "desc": "Соты в бересте. Сладкая находка.", "prompt": "honeycomb wrapped in birch bark, wild honey"},
    {"name": "Камень-страж", "material": "известняк", "desc": "Причудливой формы. Ориентир.", "prompt": "limestone sentinel rock, unusual shape, landmark"},
]

RITUALS = [
    {"name": "Мед из дупла", "material": "мёд и соты", "desc": "Обряд находки. Благодарность духам леса.", "prompt": "ritual honey harvest from tree hollow, shamanic offering"},
    {"name": "Кость предка", "material": "кость", "desc": "Для ритуала ориентирования. Указывает путь.", "prompt": "ancestor bone used as directional talisman, ritual object"},
    {"name": "Яйцо перепела", "material": "яйцо", "desc": "Символ плодородия земли. Не еда — знак.", "prompt": "quail egg as fertility symbol, painted with ochre"},
]

def get_deed_text():
    return "Читаю следы. Знаю, где газели пьют."

def get_image_prompt():
    return (
        "Natufian scout tracking in Levantine oak savanna, 10500 BC, rocky terrain, morning mist, photorealistic, 8k"
    )
