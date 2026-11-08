"""Recherche dans le dictionnaire de Sanzo Wada.

Usage :
  Copie clean par défaut ; ajouter --data-source raw pour le brut.
  python lookup.py color "Burnt Sienna" [--brief]  -> fiche d'une couleur et ses combinaisons
  python lookup.py combo 198                       -> les couleurs d'une combinaison (1 à 348)
  python lookup.py nearest "#ae5224" [--n 5]       -> couleurs du dictionnaire les plus proches d'un HEX (3 par défaut)
  python lookup.py list                            -> toutes les couleurs (nom, cmyk, hex, chapitre)
(Windows : py lookup.py ... ; Linux/macOS : python3 lookup.py ...)
Sous PowerShell, mettre les codes HEX entre guillemets : un # nu commence un commentaire.
--brief : n'affiche que le numéro et les noms de chaque combinaison (sortie courte pour les agents).
Un nom sans correspondance exacte mais avec plusieurs correspondances partielles renvoie "ambigu" (code 1).
Sortie JSON. Code de sortie 0 si résultat, 1 si rien trouvé, ambigu ou données invalides, 2 si usage incorrect.
"""
import sys

from wada import (REMINDER, DataError, brief, build_combinations, combo_brief, combo_detail, dump,
                  fail, find_by_hex, find_colors, hex_to_rgb, is_hex, known_anomalies, load_colors,
                  nearest_colors, norm, similar_names, utf8_stdout, warnings_for, data_source_option)

PS_NOTE = "Sous PowerShell, mettre le code HEX entre guillemets (\"#ae5224\") : un # nu est un commentaire."
METHODE_NEAREST = ("ΔE CIEDE2000 entre le Lab du HEX saisi (sRGB -> Lab D50, matrice Bradford) et le Lab source "
                   "de chaque couleur (CMYK -> profils ICC) ; CIE76 donné pour comparaison. Les deux chaînes "
                   "diffèrent légèrement : un petit écart non nul est normal.")


def pop_option(argv, name, default):
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            return argv, None
        value = argv[i + 1]
        return argv[:i] + argv[i + 2:], value
    return argv, default


def main(argv):
    utf8_stdout()
    try:
        argv, source = data_source_option(argv)
    except DataError as e:
        return fail(str(e), 2)
    brief_mode = "--brief" in argv
    argv = [a for a in argv if a != "--brief"]
    argv, n_opt = pop_option(argv, "--n", "3")
    if n_opt is None or not n_opt.isdigit() or int(n_opt) < 1:
        return fail("--n doit être un entier supérieur ou égal à 1.", 2)
    n = int(n_opt)
    if len(argv) < 2:
        print(__doc__)
        return 2
    try:
        colors = load_colors(source)
    except DataError as e:
        return fail(str(e))
    combos = build_combinations(colors)
    anomalies, avertissement_global = known_anomalies()
    cmd = argv[1]

    def finish(result):
        result["data_source"] = source
        if avertissement_global:
            result["avertissement_global"] = avertissement_global
        dump(result)
        return 0

    if cmd == "list":
        items = []
        for c in colors:
            d = {"name": c["name"], "cmyk": c["cmyk"], "hex": c["hex"], "chapitre_base0": c["swatch"],
                 "nb_combinations": len(c["combinations"])}
            w = warnings_for([c], anomalies)
            if w:
                d["avertissements"] = w
            items.append(d)
        return finish({"couleurs": items, "total": len(items), "rappel": REMINDER})

    if len(argv) < 3:
        print(__doc__)
        return 2
    arg = " ".join(argv[2:])

    if cmd == "color":
        found = find_colors(colors, arg)
        if not found:
            return fail("Aucune couleur du dictionnaire ne correspond à « %s »." % arg)
        exact = any(norm(c["name"]) == norm(arg) or norm(c.get("name_source", "")) == norm(arg) for c in found)
        if not exact and len(found) > 1:
            dump({"ambigu": [c["name"] for c in found],
                  "message": "Plusieurs couleurs contiennent « %s » : préciser le nom exact." % arg})
            return 1
        out = []
        for c in found:
            d = brief(c)
            d["chapitre_base0"] = c["swatch"]
            if brief_mode:
                d["combinations"] = [combo_brief(colors, combos, cid, anomalies) for cid in c["combinations"]]
            else:
                d["combinations"] = [combo_detail(colors, combos, cid, anomalies) for cid in c["combinations"]]
            for key in ("name_source", "derived_values_status", "cmyk_source"):
                if key in c:
                    d[key] = c[key]
            w = warnings_for([c], anomalies)
            if w:
                d["avertissements"] = w
            out.append(d)
        result = {"resultats": out, "rappel": REMINDER}
        voisins = similar_names(colors, arg, exclude=[c["name"] for c in found])
        if voisins:
            result["autres_noms_contenant_la_requete"] = voisins
        return finish(result)

    if cmd == "combo":
        try:
            cid = int(arg)
        except ValueError:
            return fail("Le numéro de combinaison doit être un entier de 1 à 348.")
        if cid not in combos:
            return fail("Combinaison %d introuvable (numéros valides : 1 à 348)." % cid)
        return finish({"resultat": combo_detail(colors, combos, cid, anomalies), "rappel": REMINDER})

    if cmd == "nearest":
        if not is_hex(arg):
            return fail("Donner un code HEX à 6 chiffres, par exemple \"#ae5224\". " + PS_NOTE)
        h = "#" + arg.strip().lstrip("#").lower()
        exact = find_by_hex(colors, arg)
        out = []
        for d00, d76, c in nearest_colors(colors, hex_to_rgb(arg), n):
            item = brief(c)
            item["ecart_delta_e_2000"] = round(d00, 1)
            item["ecart_delta_e_cie76"] = round(d76, 1)
            item["combinations"] = c["combinations"]
            w = warnings_for([c], anomalies)
            if w:
                item["avertissements"] = w
            out.append(item)
        result = {"hex_demande": h, "dans_le_dictionnaire": bool(exact), "plus_proches": out,
                  "methode": METHODE_NEAREST, "rappel": REMINDER}
        if exact:
            result["correspondance_exacte"] = exact["name"]
            result["rappel"] += " Le HEX demandé est exactement celui de « %s »." % exact["name"]
        else:
            result["rappel"] += " La couleur la plus proche n'est pas identique à la couleur demandée."
        return finish(result)

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
