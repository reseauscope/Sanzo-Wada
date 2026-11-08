"""Contrôle d'intégrité des données du skill.

Usage : python verify.py
Vérifie : 159 couleurs, 348 combinaisons numérotées 1 à 348 de 2 à 4 couleurs, noms uniques, aucun
numéro répété dans la liste d'une couleur, types numériques (CMYK, RGB, Lab), bornes, HEX cohérent
avec RGB, swatch de 0 à 5, empreinte SHA-256 de colors.json conforme au manifeste, et
combinations.json STRICTEMENT identique à ce que build_combinations.py produirait (la première
combinaison divergente est nommée).
Code de sortie 0 si aucune erreur (les anomalies documentées dans data/manifest.json sont signalées
comme avertissements), 1 sinon.
"""
import hashlib
import copy
import json
import os
import re
import sys

from build_combinations import render
from wada import DATA, DataError, build_combinations, fail, known_anomalies, load_colors, load_manifest, utf8_stdout
from clean_schema import MANIFEST_SHA256, SOURCE_SHA256, VERSION, encoded, file_changes, sha


def verify_clean():
    """Reconstruit les résultats autorisés sans importer le générateur build_clean."""
    from pathlib import Path
    root = Path(DATA)
    source = {name: (root / name).read_bytes()
              for name in ("colors.json", "combinations.json", "manifest.json")}
    if sha(source["colors.json"]) != SOURCE_SHA256 or sha(source["manifest.json"]) != MANIFEST_SHA256:
        raise DataError("Brut ou manifeste différent de l'état autorisé pour le nettoyage.")
    expected = {name: json.loads(source[name].decode("utf-8"))
                for name in ("colors.json", "combinations.json")}
    if any(c["hex"] != c["hex"].lower() for c in expected["colors.json"]):
        raise DataError("HEX en majuscules non prévu dans les quatre corrections.")
    corrections = []
    # Cette reconstruction est indépendante de build_clean : ne pas remplacer
    # par un appel à son générateur, même pour réduire la duplication.
    renames = [("Calamine BLue", "Calamine Blue", "certaine : correction typographique décidée par Jean"),
               ("Cerulian Blue", "Cerulean Blue", "décision de Jean ; fidélité au livre non vérifiée"),
               ("Antwarp Blue", "Antwerp Blue", "décision de Jean ; fidélité au livre non vérifiée")]
    for old, new, certainty in renames:
        before = copy.deepcopy(expected)
        matches = [i for i, c in enumerate(expected["colors.json"]) if c["name"] == old]
        if len(matches) != 1:
            raise DataError("Nom source non unique pour le nettoyage : %s." % old)
        index = matches[0]
        expected["colors.json"][index].update({"name": new, "name_source": old})
        for combination in expected["combinations.json"]["combinations"]:
            for pos, name in enumerate(combination["colors"]):
                if name == old:
                    combination["colors"][pos] = new
        corrections.append({"source_index": index, "source_name": old,
                            "reason": "Correction du nom décidée par Jean le 2026-11-08.",
                            "certainty": certainty, "changes": file_changes(before, expected)})
    before = copy.deepcopy(expected)
    index = next(i for i, c in enumerate(expected["colors.json"]) if c["name"] == "Dull Violet Black")
    color = expected["colors.json"][index]
    if color["cmyk"] != [95, 106, 38, 50]:
        raise DataError("CMYK source inattendu pour Dull Violet Black.")
    color.update({"cmyk": [95, 100, 38, 50], "cmyk_source": [95, 106, 38, 50],
                  "derived_values_status": "source_before_cmyk_correction"})
    for combination in expected["combinations.json"]["combinations"]:
        for pos, name in enumerate(combination["colors"]):
            if name == "Dull Violet Black":
                combination["cmyk"][pos] = [95, 100, 38, 50]
    corrections.append({"source_index": index, "source_name": "Dull Violet Black",
                        "reason": "Magenta 106 ramené à la borne 100 sur décision de Jean le 2026-11-08 ; dérivés conservés sans recalcul.",
                        "certainty": "hypothèse de correction de borne, non vérifiée contre le livre papier",
                        "changes": file_changes(before, expected)})
    output = {name: encoded(value) for name, value in expected.items()}
    journal = {"schema_version": 1, "clean_version": VERSION, "decision_date": "2026-11-08",
               "source_sha256": {name: sha(blob) for name, blob in source.items()},
               "output_sha256": {name: sha(blob) for name, blob in output.items()},
               "uppercase_hex_count": 0, "corrections": corrections}
    for name, blob in dict(output, **{"cleaning.json": encoded(journal)}).items():
        path = root / "clean" / name
        if not path.is_file():
            raise DataError("Copie nettoyée incomplète : data/clean/%s absent ou illisible." % name)
        if path.read_bytes() != blob:
            raise DataError("data/clean/%s diffère de la reconstruction indépendante autorisée." % name)
    # Le chargement commun contrôle aussi structure, bornes, effectifs et tailles.
    clean = load_colors("clean")
    print("OK : copie nettoyée %s, quatre corrections et journal JSON Pointer conformes, %d couleurs." % (VERSION, len(clean)))
    return True


def diff_combinations(attendu_txt, reel_txt):
    """Nomme la première combinaison qui diffère entre le fichier et le rendu attendu."""
    try:
        attendu = json.loads(attendu_txt)["combinations"]
        reel = json.loads(reel_txt)["combinations"]
        if not isinstance(attendu, list) or not isinstance(reel, list):
            return "combinations doit être une liste"
    except (ValueError, KeyError, TypeError):
        return "le fichier n'est pas un JSON de combinaisons valide"
    if len(attendu) != len(reel):
        return "%d combinaisons dans le fichier, %d attendues" % (len(reel), len(attendu))
    for a, r in zip(attendu, reel):
        if a != r:
            return "combinaison n° %s diffère (fichier : %s ; attendu : %s)" % (
                a.get("id"), json.dumps(r, ensure_ascii=False)[:160], json.dumps(a, ensure_ascii=False)[:160])
    return "différence hors combinaisons (note, ordre des clés ou mise en forme)"


def _verify():
    utf8_stdout()
    erreurs = []
    avertissements = []
    try:
        colors = load_colors("raw")
    except DataError as e:
        return fail(str(e))
    combos = build_combinations(colors)
    try:
        manifest = load_manifest()
    except DataError as e:
        return fail(str(e))
    connues, _ = known_anomalies(manifest)
    for nom in connues:
        if nom not in {c["name"] for c in colors}:
            erreurs.append("manifest.json déclare une anomalie pour une couleur inconnue : %s." % nom)

    if len(colors) != 159:
        erreurs.append("Attendu 159 couleurs, trouvé %d." % len(colors))
    if len(combos) != 348:
        erreurs.append("Attendu 348 combinaisons, trouvé %d." % len(combos))
    if list(combos.keys()) != list(range(1, 349)):
        erreurs.append("Les numéros de combinaison ne couvrent pas exactement 1 à 348.")

    noms = [c["name"] for c in colors]
    if len(set(noms)) != len(noms):
        erreurs.append("Des noms de couleurs sont en double.")

    for c in colors:
        if len(set(c["combinations"])) != len(c["combinations"]):
            erreurs.append("Numéro de combinaison répété pour %s : %s." % (c["name"], c["combinations"]))
        if any(not 0 <= v <= 100 for v in c["cmyk"]):
            if c["name"] in connues and c["cmyk"] == connues[c["name"]].get("valeur"):
                avertissements.append("Anomalie connue : %s, CMYK %s hors de 0-100 (voir manifest.json)."
                                      % (c["name"], c["cmyk"]))
            else:
                erreurs.append("CMYK invalide pour %s : %s." % (c["name"], c["cmyk"]))
        if any(not 0 <= v <= 255 or int(v) != v for v in c["rgb"]):
            erreurs.append("RGB invalide pour %s." % c["name"])
        elif "#%02x%02x%02x" % tuple(int(v) for v in c["rgb"]) != c["hex"].lower():
            erreurs.append("HEX et RGB incohérents pour %s." % c["name"])
        if not 0 <= c["lab"][0] <= 100:
            erreurs.append("Lab aberrant pour %s (L* hors de 0-100) : %s." % (c["name"], c["lab"]))
        if not 0 <= c["swatch"] <= 5:
            erreurs.append("swatch hors de 0-5 pour %s." % c["name"])
        if any(not 1 <= cid <= 348 for cid in c["combinations"]):
            erreurs.append("Numéro de combinaison hors de 1-348 pour %s." % c["name"])

    chapitres = {c["swatch"] for c in colors}
    if chapitres != set(range(6)):
        erreurs.append("Chapitres présents : %s (attendu 0 à 5, chacun non vide)." % sorted(chapitres))

    tailles = {}
    for cid, idx in combos.items():
        tailles[len(idx)] = tailles.get(len(idx), 0) + 1
        if not 2 <= len(idx) <= 4:
            erreurs.append("Combinaison %d : %d couleurs (attendu 2 à 4)." % (cid, len(idx)))

    attendu = str(manifest.get("sha256", "")).lower()
    with open(os.path.join(DATA, "colors.json"), "rb") as f:
        reel = hashlib.sha256(f.read()).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", attendu):
        erreurs.append("manifest.json : empreinte sha256 absente ou mal formée (64 caractères hexadécimaux attendus).")
    elif attendu != reel:
        erreurs.append("colors.json a été modifié depuis la récupération (empreinte différente du manifeste).")

    comb_path = os.path.join(DATA, "combinations.json")
    if os.path.exists(comb_path):
        with open(comb_path, encoding="utf-8", newline="") as f:
            contenu = f.read()
        if "\r\n" in contenu:
            erreurs.append("combinations.json contient des fins de ligne CRLF (relancer build_combinations.py).")
        rendu = render(colors, combos)
        if contenu.replace("\r\n", "\n") != rendu:
            erreurs.append("combinations.json diffère du rendu de build_combinations.py : %s. Relancer le script."
                           % diff_combinations(rendu, contenu))
    else:
        erreurs.append("data/combinations.json manquant (lancer build_combinations.py).")

    print("Couleurs : %d | Combinaisons : %d | Répartition par taille : %s"
          % (len(colors), len(combos), dict(sorted(tailles.items()))))
    for w in avertissements:
        print("AVERTISSEMENT :", w)
    if erreurs:
        print("ÉCHEC :")
        for e in erreurs:
            print(" -", e)
        return 1
    print("OK : données conformes" + (" (avec %d anomalie(s) amont documentée(s))." % len(avertissements)
                                       if avertissements else "."))
    verify_clean()
    return 0


def main():
    utf8_stdout()
    try:
        return _verify()
    except (DataError, OSError, UnicodeError, ValueError, KeyError, TypeError, StopIteration) as e:
        return fail("Vérification impossible : %s" % e)


if __name__ == "__main__":
    sys.exit(main())
