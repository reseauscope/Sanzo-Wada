"""Génère data/combinations.json à partir de data/colors.json.

Usage : python build_combinations.py
Le fichier produit est dérivé : colors.json reste la source. Fins de ligne LF forcées (reproductible
d'un système à l'autre).
"""
import json
import os
import sys

from wada import DATA, DataError, build_combinations, fail, load_colors, utf8_stdout


def render(colors, combos):
    out = {
        "_note": ("Fichier dérivé de colors.json (jeu de données de Matt DesLauriers d'après Sanzo Wada). "
                  "L'ordre des couleurs dans une combinaison n'est pas enregistré : il suit l'ordre du livre. "
                  "Valeur de référence : CMYK. Regénérer avec scripts/build_combinations.py."),
        "combinations": [
            {
                "id": cid,
                "size": len(idx),
                "colors": [colors[i]["name"] for i in idx],
                "hex": [colors[i]["hex"] for i in idx],
                "cmyk": [colors[i]["cmyk"] for i in idx],
            }
            for cid, idx in combos.items()
        ],
    }
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


def main():
    utf8_stdout()
    try:
        colors = load_colors("raw")
    except DataError as e:
        return fail(str(e))
    combos = build_combinations(colors)
    with open(os.path.join(DATA, "combinations.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(colors, combos))
    print("combinations.json écrit : %d combinaisons." % len(combos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
