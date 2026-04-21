# -*- coding: utf-8 -*-
"""
Ранг 10: Мастер обряда.
PPN, Анатолия. 12 артефактов.
"""

import random

ARTIFACTS = [
    {"name": "Кровь на алтаре", "material": "кровь птицы", "desc": "Перья в огне. Первый дар богам.", "prompt": "bird blood on stone altar, feather offering, sacred fire"},
    {"name": "Чаша из камня", "material": "плоский камень", "desc": "Выдолблена три дня. Для сбора крови.", "prompt": "carved stone basin, blood collection bowl"},
    {"name": "Дикий бык", "material": "мясо", "desc": "Жертвоприношение. Тяжёлый, брыкался.", "prompt": "wild aurochs sacrifice, massive beast, ritual kill"},
    {"name": "Знак лисы", "material": "камень", "desc": "На T-столбе. Символ хитрости богов.", "prompt": "fox relief carving on T-pillar, symbolic art"},
    {"name": "Площадка круга", "material": "земля", "desc": "Очищена. Щебень убран. Ровная.", "prompt": "ritual circle platform, cleared ground, sacred geometry"},
    {"name": "Обряд первого семени", "material": "зерно", "desc": "Зерно в крови. Посев освящён.", "prompt": "first seed blessing, grain in blood, consecrated sowing"},
    {"name": "Насечки на столбе", "material": "камень", "desc": "Геометрия. Отпугивает злых духов.", "prompt": "T-pillar geometric incisions, protective patterns"},
    {"name": "Кости предков", "material": "кость", "desc": "В фундамент. Держат стены.", "prompt": "ancestor bones in foundation, structural ritual deposit"},
    {"name": "Ночной обряд", "material": "огонь", "desc": "Без сна, без еды. Только песни.", "prompt": "nightlong fire ritual, trance, exhaustion"},
    {"name": "Голова быка", "material": "камень", "desc": "Рельеф. Тяжёлая, точная работа.", "prompt": "aurochs head relief carving, megalithic art"},
    {"name": "Кровь козла", "material": "камень", "desc": "Окропил стройку. Благословение.", "prompt": "goat blood sprinkling, construction blessing"},
    {"name": "Очищение рабочих", "material": "зола", "desc": "Вода с золой. Холодная, священная.", "prompt": "ritual worker purification, ash and water wash"},
]

RITUALS = [
    {"name": "T-образный столб", "material": "известняк", "desc": "Первый воздвигнут. Боги спустились.", "prompt": "first erected T-pillar, divine descent, megalith"},
    {"name": "Круг жертвенный", "material": "камень", "desc": "Замкнут. Кровь впиталась.", "prompt": "completed ritual stone circle, blood absorbed, sacred ground"},
    {"name": "Шаманский транс", "material": "пепел", "desc": "Видел будущее. Сказал мне.", "prompt": "shamanic trance vision, future sight, ash drawing"},
]

def get_deed_text():
    return "Провожу обряды. Кровь на алтаре. T-столбы."

def get_image_prompt():
    return (
        "PPN ritual at Göbekli Tepe style T-pillar, Anatolia 7500 BC, blood on limestone, sacred fire, photorealistic, 8k"
    )
