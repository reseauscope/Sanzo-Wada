"""Accès aux données du dictionnaire de Sanzo Wada (jeu de données de Matt DesLauriers, MIT).

Python 3.8+, bibliothèque standard uniquement. Neutre : aucune dépendance à un projet.
Valeur de référence : CMYK. Les champs rgb / hex / lab sont des conversions (approximations d'écran).
"""
import json
import math
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

REMINDER = (
    "CMYK = valeur du jeu de données transcrit d'après le livre, non vérifiée contre le papier ; "
    "HEX/RGB = approximation d'écran. "
    "L'ordre des couleurs dans une combinaison n'est pas enregistré."
)


class DataError(Exception):
    """Erreur de données lisible (fichier absent, JSON invalide, structure inattendue)."""


def utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def fail(message, code=1):
    """Imprime une erreur JSON lisible et renvoie le code de sortie."""
    print(json.dumps({"erreur": message}, ensure_ascii=False))
    return code


def _load_json(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        raise DataError("Fichier de données absent : data/%s." % name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, UnicodeDecodeError) as e:
        raise DataError("data/%s n'est pas un JSON valide (%s)." % (name, e))
    except OSError as e:
        raise DataError("data/%s illisible (%s)." % (name, e.strerror or e))


def _is_num(v):
    try:
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    except OverflowError:
        return False


def _check_color(i, c):
    """Validation de structure et de types d'une couleur ; lève DataError avec un message précis."""
    for k in ("name", "combinations", "swatch", "cmyk", "lab", "rgb", "hex"):
        if k not in c:
            raise DataError("Couleur n° %d sans champ « %s » dans data/colors.json." % (i, k))
    nom = c["name"] if isinstance(c["name"], str) else "n° %d" % i
    if not isinstance(c["name"], str) or not c["name"].strip():
        raise DataError("Couleur n° %d : nom vide ou non textuel." % i)
    for k, n in (("cmyk", 4), ("rgb", 3), ("lab", 3)):
        v = c[k]
        if not isinstance(v, list) or len(v) != n or not all(_is_num(x) for x in v):
            raise DataError("Couleur %s : champ %s invalide (attendu %d nombres finis)." % (nom, k, n))
    if not isinstance(c["hex"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", c["hex"]):
        raise DataError("Couleur %s : hex invalide." % nom)
    if (not isinstance(c["combinations"], list) or not c["combinations"]
            or not all(type(x) is int and 1 <= x <= 348 for x in c["combinations"])):
        raise DataError("Couleur %s : combinations doit contenir des entiers de 1 à 348, sans booléens." % nom)
    if len(set(c["combinations"])) != len(c["combinations"]):
        raise DataError("Couleur %s : numéro de combinaison répété." % nom)
    if not isinstance(c["swatch"], int) or isinstance(c["swatch"], bool):
        raise DataError("Couleur %s : swatch doit être un entier." % nom)
    if not 0 <= c["swatch"] <= 5:
        raise DataError("Couleur %s : swatch hors de 0-5." % nom)
    if not all(type(v) is int and 0 <= v <= 255 for v in c["rgb"]):
        raise DataError("Couleur %s : RGB doit contenir trois entiers de 0 à 255." % nom)
    if "#%02x%02x%02x" % tuple(c["rgb"]) != c["hex"].lower():
        raise DataError("Couleur %s : HEX et RGB incohérents." % nom)
    if not 0 <= c["lab"][0] <= 100:
        raise DataError("Couleur %s : L* hors de 0-100." % nom)
    if any(not 0 <= v <= 100 for v in c["cmyk"]):
        # Seule exception amont documentée, conservée même si le manifeste est
        # indisponible : les commandes émettent alors avertissement_global.
        if not (nom == "Dull Violet Black" and c["cmyk"] == [95, 106, 38, 50]):
            raise DataError("Couleur %s : CMYK hors de 0-100." % nom)


def load_colors(source="clean"):
    if source not in ("raw", "clean"):
        raise DataError("Source attendue : raw ou clean.")
    colors = _load_json("colors.json" if source == "raw" else "clean/colors.json")
    if not isinstance(colors, list) or not colors:
        raise DataError("data/colors.json doit contenir une liste de couleurs.")
    for i, c in enumerate(colors):
        if not isinstance(c, dict):
            raise DataError("Entrée n° %d de data/colors.json : objet attendu." % i)
        _check_color(i, c)
        if source == "clean":
            if any(not 0 <= v <= 100 for v in c["cmyk"]):
                raise DataError("CMYK nettoyé hors de 0-100 pour %s." % c["name"])
            if "name_source" in c and (not isinstance(c["name_source"], str) or not c["name_source"].strip()):
                raise DataError("name_source invalide pour %s." % c["name"])
            if c["name"] == "Dull Violet Black" and (c.get("derived_values_status") != "source_before_cmyk_correction"
                    or c.get("cmyk_source") != [95, 106, 38, 50] or c["cmyk"] != [95, 100, 38, 50]):
                raise DataError("Statut des dérivés ou CMYK nettoyé invalide pour Dull Violet Black.")
        c["index"] = i
    if len(colors) != 159 or len({norm(c["name"]) for c in colors}) != 159:
        raise DataError("data/colors.json doit contenir 159 noms de couleurs distincts.")
    if {c["swatch"] for c in colors} != set(range(6)):
        raise DataError("data/colors.json doit couvrir les six chapitres de 0 à 5.")
    combos = build_combinations(colors)
    if list(combos) != list(range(1, 349)) or any(not 2 <= len(v) <= 4 for v in combos.values()):
        raise DataError("data/colors.json doit couvrir les combinaisons 1 à 348, de 2 à 4 couleurs.")
    return colors


def data_source_option(argv):
    """Retire l'option commune des deux CLI sans argparse. Aucun état global."""
    argv = list(argv)
    if "--data-source" not in argv:
        return argv, "clean"
    if argv.count("--data-source") != 1:
        raise DataError("--data-source ne doit apparaître qu'une fois.")
    i = argv.index("--data-source")
    if i + 1 >= len(argv) or argv[i + 1] not in ("raw", "clean"):
        raise DataError("--data-source doit être raw ou clean.")
    return argv[:i] + argv[i + 2:], argv[i + 1]


def load_manifest():
    """Le manifeste (dict). Lève DataError s'il est absent, illisible ou mal formé."""
    m = _load_json("manifest.json")
    if not isinstance(m, dict):
        raise DataError("data/manifest.json doit être un objet JSON.")
    anomalies = m.get("anomalies_connues", [])
    if not isinstance(anomalies, list) or not all(isinstance(a, dict) and isinstance(a.get("couleur"), str)
                                                  and isinstance(a.get("constat"), str) for a in anomalies):
        raise DataError("data/manifest.json : anomalies_connues doit être une liste d'objets avec couleur et constat.")
    return m


def known_anomalies(manifest=None):
    """({nom de couleur: anomalie}, avertissement global ou None).

    Si le manifeste ne peut pas être lu, le registre est vide ET un avertissement global est renvoyé :
    l'absence d'information ne vaut pas absence d'anomalie.
    """
    try:
        if manifest is None:
            manifest = load_manifest()
        elif not isinstance(manifest, dict) or not isinstance(manifest.get("anomalies_connues", []), list):
            raise DataError("manifeste mal formé")
    except DataError as e:
        return {}, ("Registre d'anomalies indisponible (%s) : les résultats peuvent contenir des valeurs "
                    "douteuses sans avertissement." % e)
    return {a["couleur"]: a for a in manifest.get("anomalies_connues", [])}, None


def build_combinations(colors):
    """Retourne {numéro de combinaison: [indices de couleurs]}.

    L'ordre des couleurs au sein d'une combinaison n'est PAS enregistré dans les données :
    les indices suivent simplement l'ordre des couleurs dans le livre.
    """
    combos = {}
    for c in colors:
        for cid in c["combinations"]:
            combos.setdefault(cid, []).append(c["index"])
    return {cid: combos[cid] for cid in sorted(combos)}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def find_colors(colors, query):
    """Correspondance exacte (insensible à la casse et aux accents) si elle existe, sinon partielle."""
    q = norm(query)
    exact = [c for c in colors if norm(c["name"]) == q or norm(c.get("name_source", "")) == q]
    if exact:
        return exact
    return [c for c in colors if q and (q in norm(c["name"]) or q in norm(c.get("name_source", "")))]


def similar_names(colors, query, exclude=()):
    """Autres couleurs dont le nom contient la requête (pour signaler les voisins masqués)."""
    q = norm(query)
    return [c["name"] for c in colors if q and q in norm(c["name"]) and c["name"] not in exclude]


def is_hex(s):
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", s.strip()))


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def find_by_hex(colors, h):
    """Couleur du dictionnaire dont le hex est exactement celui donné, sinon None."""
    h = "#" + h.strip().lstrip("#").lower()
    for c in colors:
        if c["hex"].lower() == h:
            return c
    return None


def resolve_color(colors, arg):
    """Nom de couleur ou HEX -> (couleur du dictionnaire ou None, rgb, étiquette, écart ΔE00 ou None).

    Un HEX exactement présent dans le dictionnaire renvoie cette couleur avec un écart 0.
    Un HEX absent renvoie (None, rgb, hex, None). Un nom ambigu lève ValueError avec les candidats.
    """
    if is_hex(arg):
        c = find_by_hex(colors, arg)
        h = "#" + arg.strip().lstrip("#").lower()
        if c:
            return c, c["rgb"], c["name"] + " " + c["hex"], 0.0
        return None, hex_to_rgb(arg), h, None
    found = find_colors(colors, arg)
    if not found:
        return None, None, arg, None
    if len(found) > 1:
        raise ValueError([c["name"] for c in found])
    c = found[0]
    return c, c["rgb"], c["name"] + " " + c["hex"], 0.0


def _lin(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb):
    """sRGB (8 bits) -> CIE L*a*b* avec blanc de référence D50.

    Chaîne : décodage gamma sRGB -> RGB linéaire -> XYZ(D50) -> Lab(D50).
    La matrice ci-dessous est la matrice sRGB -> XYZ **déjà adaptée de D65 vers D50 par la
    transformation de Bradford** (coefficients de Lindbloom ; la matrice non adaptée serait
    0.4124/0.3576/0.1805 en première ligne). Contrôle : le blanc (255,255,255) donne L=100, a=0, b=0.

    Sert uniquement à convertir une couleur ENTRÉE par l'utilisateur (HEX). Pour les couleurs du
    dictionnaire, on utilise le champ `lab` fourni par la source, calculé depuis le CMYK avec des
    profils ICC. Les deux chaînes ne sont pas identiques : l'écart entre un HEX d'entrée et une
    couleur du dictionnaire porte donc un petit biais de méthode (de l'ordre de ΔE 0,1 à 0,3 sur
    les couleurs du dictionnaire elles-mêmes, davantage sur les teintes saturées hors gamut sRGB).
    """
    r, g, b = [_lin(v) for v in rgb]
    x = 0.4360747 * r + 0.3850649 * g + 0.1430804 * b
    y = 0.2225045 * r + 0.7168786 * g + 0.0606169 * b
    z = 0.0139322 * r + 0.0971045 * g + 0.7141733 * b
    xn, yn, zn = 0.9642, 1.0, 0.8249

    def f(t):
        return t ** (1.0 / 3.0) if t > 216.0 / 24389.0 else (24389.0 / 27.0 * t + 16.0) / 116.0

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def delta_e76(lab1, lab2):
    """Écart de couleur CIE76 (distance euclidienne dans L*a*b*). Formule simple, indicative."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


delta_e = delta_e76  # compatibilité


def delta_e2000(lab1, lab2):
    """Écart de couleur CIEDE2000 (ISO/CIE 11664-6), kL = kC = kH = 1. Implémentation standard
    (Sharma, Wu, Dalal 2005). Contrôle dans tests/test_wada.py sur une paire de référence publiée."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2.0
    G = 0.5 * (1.0 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25.0 ** 7)))
    a1p, a2p = (1.0 + G) * a1, (1.0 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360.0 if C1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360.0 if C2p else 0.0
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180.0:
            dhp -= 360.0
        elif dhp < -180.0:
            dhp += 360.0
    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2.0))
    Lm = (L1 + L2) / 2.0
    Cmp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hm = h1p + h2p
    else:
        s = h1p + h2p
        if abs(h1p - h2p) <= 180.0:
            hm = s / 2.0
        elif s < 360.0:
            hm = (s + 360.0) / 2.0
        else:
            hm = (s - 360.0) / 2.0
    T = (1.0 - 0.17 * math.cos(math.radians(hm - 30.0)) + 0.24 * math.cos(math.radians(2.0 * hm))
         + 0.32 * math.cos(math.radians(3.0 * hm + 6.0)) - 0.20 * math.cos(math.radians(4.0 * hm - 63.0)))
    dtheta = 30.0 * math.exp(-((hm - 275.0) / 25.0) ** 2)
    RC = 2.0 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25.0 ** 7))
    SL = 1.0 + 0.015 * (Lm - 50.0) ** 2 / math.sqrt(20.0 + (Lm - 50.0) ** 2)
    SC = 1.0 + 0.045 * Cmp
    SH = 1.0 + 0.015 * Cmp * T
    RT = -math.sin(math.radians(2.0 * dtheta)) * RC
    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


def luminance(rgb):
    r, g, b = [_lin(v) for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1, rgb2):
    l1, l2 = luminance(rgb1), luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def nearest_colors(colors, rgb, n=3):
    """Couleurs du dictionnaire les plus proches d'un RGB d'entrée.

    Tri par CIEDE2000 ; CIE76 fourni à titre de comparaison. La couleur d'entrée est convertie en
    Lab ; les couleurs du dictionnaire utilisent leur Lab source. Renvoie [(ΔE00, ΔE76, couleur)].
    """
    lab = rgb_to_lab(rgb)
    exact = find_by_hex(colors, "#%02x%02x%02x" % tuple(rgb))
    scored = sorted(((delta_e2000(lab, c["lab"]), delta_e76(lab, c["lab"]), c)
                     for c in colors if exact is None or c["name"] != exact["name"]), key=lambda t: t[0])
    if exact is not None:
        # Une couleur dont le HEX est exactement celui demandé passe en tête avec un écart nul :
        # sans cela, l'asymétrie des deux chaînes Lab peut classer une autre couleur devant elle.
        scored.insert(0, (0.0, 0.0, exact))
    return scored[:n]


def brief(c):
    result = {"name": c["name"], "cmyk": c["cmyk"], "hex": c["hex"], "rgb": c["rgb"]}
    for key in ("name_source", "cmyk_source", "derived_values_status"):
        if key in c:
            result[key] = c[key]
    return result


def warnings_for(colors_subset, anomalies):
    """Avertissements automatiques pour les couleurs à anomalie connue présentes dans un résultat.
    Le texte vient du manifeste (champ `constat`), qui porte aussi la conséquence pour l'agent."""
    out = []
    for c in colors_subset:
        if c.get("derived_values_status") == "source_before_cmyk_correction":
            out.append("%s : derived_values_status=source_before_cmyk_correction. CMYK corrigé à "
                       "[95, 100, 38, 50] par hypothèse de borne non vérifiée contre le livre papier. "
                       "RGB, HEX et Lab conservés depuis le CMYK source [95, 106, 38, 50], sans recalcul ; "
                       "ils ne sont pas une conversion du CMYK corrigé et ne sont pas sûrs. "
                       "Les calculs nearest et contrast restent disponibles sur ces dérivés source." % c["name"])
            continue
        a = anomalies.get(c["name"])
        if a:
            out.append("%s : %s" % (c["name"], a.get("constat", "anomalie documentée dans manifest.json")))
    return out


def combo_detail(colors, combos, cid, anomalies=None):
    idx = combos[cid]
    cs = [colors[i] for i in idx]
    d = {"combination": cid, "size": len(idx), "colors": [brief(c) for c in cs]}
    w = warnings_for(cs, anomalies or {})
    if w:
        d["avertissements"] = w
    return d


def combo_brief(colors, combos, cid, anomalies=None):
    cs = [colors[i] for i in combos[cid]]
    result = {"combination": cid, "size": len(cs), "colors": [c["name"] for c in cs]}
    warnings = warnings_for(cs, anomalies or {})
    if warnings:
        result["avertissements"] = warnings
    return result


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
