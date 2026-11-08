"""Calcule les rapports de contraste (WCAG 2) à partir des valeurs d'écran (RGB).

Usage :
  Copie clean par défaut ; ajouter --data-source raw pour le brut.
  python contrast.py combo 198
  python contrast.py "#ae5224" "#f9c1ce"
  python contrast.py "Burnt Sienna" "Hermosa Pink"      (noms et HEX peuvent se mélanger)

Indicatif seulement : les combinaisons de Wada ne sont pas conçues pour la lisibilité de texte,
et le RGB est une approximation d'écran des couleurs imprimées. Le contraste réel se vérifie sur le
support final (écran cible, papier, mur peint). Code de sortie 0 si résultat, 1 sinon, 2 si usage incorrect.
"""
import itertools
import sys

from wada import (DataError, build_combinations, contrast_ratio, dump, fail, known_anomalies,
                  load_colors, resolve_color, utf8_stdout, warnings_for, data_source_option)

AVERTISSEMENT_METHODE = ("Rapport de contraste WCAG 2 (luminance relative, décision prise avant arrondi) entre ces deux "
                         "couleurs sRGB opaques, telles quelles. Le RGB étant une approximation d'écran de l'impression, "
                         "le résultat vaut pour ces valeurs numériques, pas pour une interface entière (transparences, "
                         "fonds photo, états interactifs non couverts) ni pour le support final (papier, mur peint).")


def paire(nom_a, rgb_a, nom_b, rgb_b):
    r = contrast_ratio(rgb_a, rgb_b)
    return {"a": nom_a, "b": nom_b, "ratio": round(r, 2),
            "AA_texte_normal": r >= 4.5, "AA_grand_texte": r >= 3.0}


def main(argv):
    utf8_stdout()
    try:
        argv, source = data_source_option(argv)
    except DataError as e:
        return fail(str(e), 2)
    if len(argv) != 3:
        print(__doc__)
        return 2
    try:
        colors = load_colors(source)
    except DataError as e:
        return fail(str(e))
    anomalies, avertissement_global = known_anomalies()

    def finish(out):
        out["data_source"] = source
        if avertissement_global:
            out["avertissement_global"] = avertissement_global
        dump(out)
        return 0

    if argv[1] == "combo":
        combos = build_combinations(colors)
        try:
            cid = int(argv[2])
        except ValueError:
            cid = -1
        if cid not in combos:
            return fail("Combinaison introuvable (numéros valides : 1 à 348).")
        cs = [colors[i] for i in combos[cid]]
        out = {"combination": cid,
               "colors": [{k: c[k] for k in ("name", "derived_values_status") if k in c} for c in cs],
               "paires": [paire(x["name"] + " " + x["hex"], x["rgb"], y["name"] + " " + y["hex"], y["rgb"])
                          for x, y in itertools.combinations(cs, 2)],
               "avertissement_methode": AVERTISSEMENT_METHODE}
        w = warnings_for(cs, anomalies)
        if w:
            out["avertissements"] = w
        return finish(out)

    resolved = []
    for arg in argv[1:3]:
        try:
            c, rgb, label, _ = resolve_color(colors, arg)
        except ValueError as e:
            return fail("« %s » est ambigu : %s. Préciser le nom exact." % (arg, ", ".join(e.args[0])))
        if rgb is None:
            return fail("« %s » n'est ni un code HEX à 6 chiffres ni un nom de couleur du dictionnaire." % arg)
        resolved.append((c, rgb, label))
    (c1, rgb1, l1), (c2, rgb2, l2) = resolved
    out = {"paires": [paire(l1, rgb1, l2, rgb2)], "avertissement_methode": AVERTISSEMENT_METHODE}
    out["colors"] = [{k: c[k] for k in ("name", "derived_values_status") if k in c}
                     for c in (c1, c2) if c]
    w = warnings_for([c for c in (c1, c2) if c], anomalies)
    if w:
        out["avertissements"] = w
    return finish(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
