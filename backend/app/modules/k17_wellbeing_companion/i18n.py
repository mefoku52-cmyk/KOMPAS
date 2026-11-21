MESSAGES = {
    "sk": {
        "cognitive_overload": "Všimol som si, že posledné úlohy trvali dlhšie a objavili sa chyby. To je bežná súčasť učenia. Chceš si dať 2-minútovú prestávku, alebo si zopakovať predchádzajúcu látku?",
        "avoidance": "Zaznamenal som veľmi rýchle odpovede. Ak si si istý, pokračuj. Ak si nie si istý, môžeme si to prejsť spolu.",
        "neutral": "Mám otázku ohľadom tvojho súčasného tempa. Chceš pokračovať, alebo zmeniť aktivitu?",
    },
    "en": {
        "cognitive_overload": "I noticed the last tasks took longer and errors appeared. That is a normal part of learning. Would you like a 2-minute break or to review the previous material?",
        "avoidance": "I recorded very quick answers. If you are sure, continue. If not, we can go through it together.",
        "neutral": "I have a question about your current pace. Would you like to continue or change activity?",
    },
}


def t(key: str, locale: str = "sk") -> str:
    loc = locale if locale in MESSAGES else "sk"
    return MESSAGES[loc].get(key, MESSAGES["sk"].get(key, key))
