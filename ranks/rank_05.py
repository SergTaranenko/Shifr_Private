# -*- coding: utf-8 -*-
"""
Ранг 5: Держатель памяти.
NATUFIAN, Левант. 17 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Песня предков", "material": "берёза", "desc": "Записана на бересте. Знаки-подсказки.", "prompt": "birch bark song notation, ancestor melody symbols"},
    {"name": "История деда", "material": "память", "desc": "Устная, запомненная. Длинная.", "prompt": "oral history memory, elder tale, intangible artifact"},
    {"name": "Соглашение о межах", "material": "берёза", "desc": "Кто где собирает. Без крови.", "prompt": "birch bark boundary treaty, land agreement"},
    {"name": "Кость умершего", "material": "кость", "desc": "Для поминовения. Имя в огне.", "prompt": "ancestor bone for remembrance ritual, fire offering"},
    {"name": "Узел счёта", "material": "шнур", "desc": "Семь узлов — неделя. Память на пальцах.", "prompt": "knot tally cord, seven knots, week counter"},
    {"name": "Заклинание от духов", "material": "память", "desc": "Слова старые. Язык ломается.", "prompt": "shamanic chant text, spirit protection words"},
    {"name": "Сон шамана", "material": "пепел", "desc": "Толкование. Волк на горе — голод.", "prompt": "shaman dream interpretation, wolf omen drawing in ash"},
    {"name": "Приказ старшего", "material": "память", "desc": "Передан дословно. Без искажений.", "prompt": "elder command memory, verbatim transmission"},
    {"name": "Проклятие волка", "material": "камень", "desc": "Табу записанное. Не жечь кости.", "prompt": "wolf taboo inscription on stone, curse warning"},
    {"name": "Песня сбора", "material": "память", "desc": "Мелодия под которую косят. Все знают.", "prompt": "harvest song melody, communal work rhythm"},
    {"name": "Знак на камне", "material": "кремень", "desc": "Имя вождя. Метка для чужаков.", "prompt": "chief name petroglyph, territorial warning sign"},
    {"name": "Благословение мальчика", "material": "кремень", "desc": "Кровь на кремне. Первое орудие.", "prompt": "boy first tool blessing, blood on flint, initiation"},
    {"name": "Список умерших", "material": "память", "desc": "Длинный, за год. Голос дрожит.", "prompt": "yearly dead list memory, ancestor roll call"},
    {"name": "Легенда о Лосе", "material": "память", "desc": "Из него сделали первую Землю.", "prompt": "Great Moose creation legend, oral tradition"},
    {"name": "Колыбельная", "material": "память", "desc": "Песнь ухода. Не лечит, но уносит.", "prompt": "deathbed lullaby, passing song, gentle farewell"},
    {"name": "История торговли", "material": "раковина", "desc": "С соседями. Кремень на ракушки.", "prompt": "trade history record, flint for shells exchange"},
    {"name": "Предсказание дождя", "material": "глина", "desc": "По облакам. Запечатано в земле.", "prompt": "rain prediction clay tablet, cloud signs"},
]

RITUALS = [
    {"name": "Берестяная летопись", "material": "берёза", "desc": "Полная история рода. Свиток длинный.", "prompt": "birch bark scroll chronicle, complete clan history"},
    {"name": "Кость с песнопением", "material": "кость", "desc": "Вырезаны ноты. Звучит при ветре.", "prompt": "sung bone with carved musical notations, wind instrument"},
    {"name": "Обряд памяти", "material": "пепел и кровь", "desc": "Семь предков названы. Огонь принят.", "prompt": "ancestor remembrance ritual, seven names, sacred fire"},
]

def get_deed_text():
    return "Храню песни и имена. Влияние есть, власти нет."

def get_image_prompt():
    return (
        "Natufian elder chanting by fire, Levant 10000 BC, ochre markings on bone, ritual atmosphere, photorealistic, 8k"
    )
