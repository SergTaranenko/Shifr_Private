# -*- coding: utf-8 -*-
"""
Ранг 7: Пришедший из Леванта.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Блок известняка", "material": "известняк", "desc": "Первый анатолийский. Тяжелее кремня.", "prompt": "first Anatolian limestone block, rough cut, migration era"},
    {"name": "Глина для перемычки", "material": "глина", "desc": "Горная. Липкая, непривычная.", "prompt": "mountain clay for mortar, sticky and unfamiliar"},
    {"name": "Источник Тавра", "material": "вода", "desc": "В мехе. Холодная, железная.", "prompt": "Taurus mountain spring water in skin, iron taste"},
    {"name": "Новое слово", "material": "память", "desc": "'Камень' по-нашему звучит иначе. Учу.", "prompt": "new Anatolian word memory, language adaptation"},
    {"name": "Тропа к каменоломне", "material": "камень", "desc": "Два дня пути. Метка на скале.", "prompt": "quarry trail marker stone, two day journey"},
    {"name": "Временный шалаш", "material": "ветки", "desc": "Из веток. Не круглый, как дома.", "prompt": "temporary branch shelter, rectangular frame, migrant camp"},
    {"name": "Кустарник для верёвок", "material": "кора", "desc": "Не та крапива, но крепкая.", "prompt": "Anatolian fiber bush, rope material, unfamiliar species"},
    {"name": "Кабан — первая дичь", "material": "мясо", "desc": "Жёсткое. Не газель. Новый вкус.", "prompt": "wild boar meat, first Anatolian game, tough flesh"},
    {"name": "Пещера для хранения", "material": "камень", "desc": "Сухая. Пахнет медведем. Освящена.", "prompt": "storage cave, dry and bear-scented, consecrated"},
    {"name": "След дикой козы", "material": "помёт", "desc": "Зимний маршрут. Мясо на зиму.", "prompt": "wild goat track, winter migration route marker"},
    {"name": "След чужого племени", "material": "пепел", "desc": "Осторожно. Не свои земли.", "prompt": "foreign tribe footprint in ash, warning sign"},
    {"name": "Навес для огня", "material": "камень", "desc": "Ветер с гор рвёт пламя. Нужна защита.", "prompt": "windbreak fire shelter, mountain wind protection"},
]

RITUALS = [
    {"name": "Кость переселенца", "material": "кость", "desc": "Связь с Левантом. Похоронена под новым очагом.", "prompt": "migrant ancestor bone, Levant connection, new hearth foundation"},
    {"name": "Первый анатолийский огонь", "material": "зола", "desc": "Добыт трением. Новый мир начинается.", "prompt": "first Anatolian fire by friction, new world ignition"},
    {"name": "Камень-привет", "material": "известняк", "desc": "Подарок местным. Знак мира.", "prompt": "peace offering limestone, greeting gift to locals"},
]

def get_deed_text():
    return "Чужая земля. Камень, зима, забвение старых троп."

def get_image_prompt():
    return (
        "Levantine migrants in Anatolian highlands, 9000 BC, limestone ridges, cold wind, photorealistic, 8k"
    )
