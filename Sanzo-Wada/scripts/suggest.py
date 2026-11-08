"""Propose des combinaisons de Wada à partir d'une couleur de départ.

Usage :
  python suggest.py "Burnt Sienna" [--size 3] [--max 3]
  python suggest.py "#ae5224" --size 2

L'entrée peut être un nom de couleur du dictionnaire ou un code HEX. Un HEX exactement présent dans
le dictionnaire est reconnu ; sinon la couleur la plus proche sert de point de départ, avec l'écart ΔE.
Les combinaisons sont renvoyées dans l'ordre du livre, sans classement de pertinence : ce script filtre,
il ne recommande pas. --max vaut 3 par défaut (règle : présenter 2 ou 3 combinaisons).
Sous PowerShell, mettre les codes HEX entre guillemets.
Code de sortie 0 si la couleur de départ est résolue (même avec zéro combinaison pour la taille demandée),
1 si couleur introuvable, ambiguë ou données invalides, 2 si usage incorrect.
"""
import argparse
import sys

from wada import (REMINDER, DataError, brief, build_combinations, combo_detail, dump, fail,
                  find_by_hex, find_colors, hex_to_rgb, is_hex, known_anomalies, load_colors,
                  nearest_colors, utf8_stdout, warnings_for)


def positif(valeur):
    n = int(valeur)
    if n < 1:
        raise argparse.ArgumentTypeError("--max doit être un entier supérieur ou égal à 1.")
    return n


def main():
    utf8_stdout()
    p = argparse.ArgumentParser(description="Combinaisons de Sanzo Wada à partir d'une couleur")
    p.add_argument("couleur", help="nom de couleur du dictionnaire ou code HEX (entre guillemets sous PowerShell)")
    p.add_argument("--size", type=int, choices=[2, 3, 4], help="nombre de couleurs voulu")
    p.add_argument("--data-source", choices=["clean", "raw"], default="clean", help="copie lue (défaut : clean)")
    p.add_argument("--max", type=positif, default=3, help="nombre maximum de combinaisons (>= 1, défaut 3)")
    a = p.parse_args()

    try:
        colors = load_colors(a.data_source)
    except DataError as e:
        return fail(str(e))
    combos = build_combinations(colors)
    anomalies, avertissement_global = known_anomalies()
    ecart = None
    approx = False

    if is_hex(a.couleur):
        anchor = find_by_hex(colors, a.couleur)
        if anchor is None:
            d00, d76, anchor = nearest_colors(colors, hex_to_rgb(a.couleur), 1)[0]
            ecart = {"delta_e_2000": round(d00, 1), "delta_e_cie76": round(d76, 1)}
            approx = True
    else:
        found = find_colors(colors, a.couleur)
        if not found:
            return fail("Aucune couleur ne correspond à « %s »." % a.couleur)
        if len(found) > 1:
            dump({"ambigu": [c["name"] for c in found],
                  "message": "Plusieurs couleurs correspondent, préciser le nom exact."})
            return 1
        anchor = found[0]

    ids = [cid for cid in anchor["combinations"] if a.size is None or len(combos[cid]) == a.size]
    out = {
        "data_source": a.data_source,
        "depart": a.couleur,
        "couleur_du_dictionnaire": brief(anchor),
        "combinaisons_disponibles": len(ids),
        "combinaisons_affichees": min(len(ids), a.max),
        "ordre": "ordre du livre, sans classement de pertinence",
        "combinaisons": [combo_detail(colors, combos, cid, anomalies) for cid in ids[: a.max]],
        "rappel": REMINDER,
    }
    if not ids:
        out["message"] = ("Aucune combinaison%s n'inclut « %s »%s."
                          % (" de %d couleurs" % a.size if a.size else "", anchor["name"],
                             " ; cette couleur apparaît dans %d combinaison(s) d'autres tailles"
                             % len(anchor["combinations"]) if a.size and anchor["combinations"] else ""))
    w = warnings_for([anchor], anomalies)
    if w:
        out["avertissements"] = w
    if avertissement_global:
        out["avertissement_global"] = avertissement_global
    if approx:
        out["ecart"] = ecart
        out["rappel"] += " La couleur de départ HEX n'est pas dans le dictionnaire : la plus proche a été utilisée."
        if ecart["delta_e_2000"] > 5:
            out["rappel"] += " Écart important (ΔE00 > 5) : la couleur proposée est nettement différente de celle demandée."
    elif is_hex(a.couleur):
        out["rappel"] += " Le HEX demandé est exactement celui de « %s »." % anchor["name"]
    dump(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
