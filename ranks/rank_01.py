# -*- coding: utf-8 -*-
"""
Ранг 1: Падальщик у края.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Обглоданная кость газели", "material": "кость", "desc": "Шакалы доели, ты собрал остатки.", "prompt": "gazelle bone gnawed by jackals, scavenged remains"},
    {"name": "Кусок кожи дикой козы", "material": "шкура", "desc": "Содрана волками, ещё пригодится.", "prompt": "wild goat hide scrap, torn by predators"},
    {"name": "Перья дикой индейки", "material": "перо", "desc": "Для чистки и украшения.", "prompt": "wild turkey feathers, colorful plumage"},
    {"name": "Коренья мальвы", "material": "корень", "desc": "Для отвара от боли в животе.", "prompt": "mallow roots, medicinal wild plants"},
    {"name": "Камень для очага", "material": "известняк", "desc": "Обломок, но держит жар.", "prompt": "limestone fire pit stone, rough block"},
    {"name": "Ветки дуба для костра", "material": "дуб", "desc": "Сухие, горят долго.", "prompt": "dry oak branches, firewood bundle"},
    {"name": "Кусок бересты", "material": "берёза", "desc": "Для записей и упаковки.", "prompt": "birch bark sheet, white and flexible"},
    {"name": "Галька из ручья", "material": "камень", "desc": "Гладкие камешки, много применений.", "prompt": "smooth river pebbles, assorted sizes"},
    {"name": "Шерсть дикой овцы", "material": "шерсть", "desc": "Комок для пряжи или набивки.", "prompt": "wild sheep wool, coarse and tangled"},
    {"name": "Сухой навоз", "material": "навоз", "desc": "Топливо, когда дров нет.", "prompt": "dried animal dung, fuel cakes"},
    {"name": "Ракушка средиземная", "material": "раковина", "desc": "Украшение или ложка.", "prompt": "Mediterranean seashell, spiral shape"},
    {"name": "Игла из кости птицы", "material": "кость птицы", "desc": "Первая заготовка, ещё не просверлена.", "prompt": "bird bone needle blank, slender"},
    {"name": "Грибы с дуба", "material": "грибы", "desc": "Съедобные, если правильно приготовить.", "prompt": "oak tree mushrooms, wild fungi"},
    {"name": "Обломок янтаря", "material": "янтарь", "desc": "Балтийский, редкий. Торговая монета.", "prompt": "raw Baltic amber piece, golden translucent"},
    {"name": "Корь дуба", "material": "кора", "desc": "Для дубления и лечения.", "prompt": "oak bark, tannin rich"},
    {"name": "Каменный молоток", "material": "кремень", "desc": "Обломок для колки костей.", "prompt": "flint hammerstone, round and heavy"},
    {"name": "Перо страуса", "material": "перо", "desc": "Длинное, для украшения шамана.", "prompt": "ostrich feather, black and white plume"},
]

RITUALS = [
    {"name": "Череп шакала", "material": "кость", "desc": "Трофей. Защита от злых духов у края.", "prompt": "jackal skull trophy, protective charm, camp edge"},
    {"name": "Кость с насечками", "material": "кость", "desc": "Первый знак. Счёт дней.", "prompt": "notched bone tally, first counting device"},
    {"name": "Клык волка", "material": "клык", "desc": "Амулет силы для падальщика.", "prompt": "wolf fang amulet, pierced for cord"},
]

def get_deed_text():
    return "Собираю остатки у края. Шакалы смотрят со стороны."

def get_image_prompt():
    return (
        "Natufian scavenger at camp edge, Levant 12000 BC, collecting remains, harsh sunlight, dust, photorealistic, 8k"
    )
