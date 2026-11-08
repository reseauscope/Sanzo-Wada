"""Exploration des couleurs et combinaisons, sans interprétation des accords."""
import hashlib
import json
import html
import math
from pathlib import Path
import wada

BASE = Path(__file__).resolve().parent
# wada.py est copié sans changement. Son chemin initial suppose scripts/.
# Adapter uniquement DATA à la copie embarquée, sans lire le skill source.
wada.DATA = str(BASE / "data")
EXPECTED = "555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4"
PROVENANCE = ("Valeurs CMYK du jeu de données de Matt DesLauriers (MIT), transcrites d'après le livre, "
              "non vérifiées contre le papier. Le HEX est une approximation d'écran. "
              "Aucune donnée de cette page ne vient d'un nuancier de peinture commercial.")
ORDER = "Ordre du livre, sans classement de pertinence. L'ordre des couleurs dans chaque combinaison n'est pas enregistré."
METHOD = ("HEX saisi : conversion sRGB vers Lab D50 avec adaptation Bradford. Dictionnaire : Lab source "
          "calculé depuis le CMYK par profils ICC. Les chaînes diffèrent, surtout hors gamut sRGB. "
          "Un HEX exact reçoit un écart nul par convention d'identité du code, sans certifier une identité "
          "physique avec le livre imprimé.")
CSS = """
.tab-container{flex-wrap:wrap}
.gradio-container {max-width:1200px!important; margin:auto!important}
.wada-card {border:1px solid #ccc; border-radius:10px; padding:16px; margin:12px 0}
.wada-swatches {display:grid; gap:0; width:100%; align-items:start}
.wada-swatch {min-width:0; margin:0}
.wada-paint {height:120px; border:1px solid #777}
.wada-caption {padding:10px 6px; font-size:13px; overflow-wrap:anywhere; line-height:1.6}
.wada-warning {border:2px solid #956000; padding:12px; margin-top:12px; color:#332100; background:#fff4d6}
.wada-gallery {display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr)); gap:16px}
.wada-gallery .wada-paint {height:86px}
.wada-provenance {border-top:2px solid #888; padding:18px 8px; margin-top:24px; line-height:1.7}
"""


def escape(value):
    return html.escape(str(value), quote=True)


def load_snapshot():
    manifest = wada.load_manifest()
    actual = hashlib.sha256((BASE / "data" / "colors.json").read_bytes()).hexdigest()
    if actual != EXPECTED or manifest.get("sha256") != EXPECTED:
        raise ValueError("Empreinte invalide : attendue %s ; lue %s" % (EXPECTED, actual))
    journal = json.loads((BASE / "data" / "clean" / "cleaning.json").read_text(encoding="utf-8"))
    receipt = json.loads((BASE / "sync-receipt.json").read_text(encoding="utf-8"))
    if journal.get("clean_version") != "1.3.0" or receipt.get("source_version") != "1.3.0":
        raise ValueError("Copie nettoyée et reçu 1.3.0 requis.")
    if len(journal.get("corrections", [])) != 4:
        raise ValueError("Quatre corrections attendues dans le journal.")
    hashes = {key.replace("\\", "/"): value for key, value in receipt["sha256"].items()}
    required = {"wada.py", "data/colors.json", "data/combinations.json", "data/manifest.json", "data/LICENSE.md",
                "data/clean/colors.json", "data/clean/combinations.json", "data/clean/cleaning.json"}
    if {key for key in hashes if not key.startswith("dataset/")} != required:
        raise ValueError("Reçu incomplet ou chemins embarqués inattendus.")
    for key, expected_hash in hashes.items():
        if key.startswith("dataset/"):
            continue  # La Space ne lit jamais le dossier du dataset.
        path = BASE / key
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError("Copie embarquée divergente : " + key)
    for name in ("colors.json", "combinations.json"):
        blob = (BASE / "data" / "clean" / name).read_bytes()
        if hashlib.sha256(blob).hexdigest() != journal["output_sha256"][name]:
            raise ValueError("Empreinte nettoyée divergente : " + name)
    colors = wada.load_colors("clean")
    combos = wada.build_combinations(colors)
    if len(colors) != 159 or list(combos) != list(range(1, 349)):
        raise ValueError("Effectifs de la copie non conformes.")
    anomalies, warning = wada.known_anomalies(manifest)
    if warning or len(anomalies) != len(manifest.get("anomalies_connues", [])):
        raise ValueError("Registre d'anomalies indisponible ou dupliqué.")
    return colors, combos, anomalies


COLORS, COMBOS, ANOMALIES = load_snapshot()
BY_NAME = {c["name"]: c for c in COLORS}


def warning_html(colors):
    # Le module 1.3.0 distingue brut et dérivés conservés du nettoyé.
    # Le message de statut remplace ici l'ancien constat CMYK=106 du brut.
    messages = wada.warnings_for(colors, ANOMALIES)
    return "".join('<div class="wada-warning" role="note"><p>%s</p></div>' % escape(message)
                   for message in dict.fromkeys(messages))


def swatches(colors):
    figures = []
    for color in colors:
        caption = ("<strong>%s</strong><br>CMYK : %s<br>HEX : %s<br>HEX : approximation d'écran" %
                   (escape(color["name"]), escape(color["cmyk"]), escape(color["hex"])))
        if color.get("name_source"):
            caption = caption.replace("</strong>", "</strong><br><small>Nom source : %s</small>" %
                                      escape(color["name_source"]), 1)
        figures.append('<figure class="wada-swatch"><div class="wada-paint" style="background:%s" '
                       'role="img" aria-label="Aplat %s"></div><figcaption class="wada-caption">%s</figcaption></figure>' %
                       (escape(color["hex"]), escape(color["hex"]), caption))
    return '<div class="wada-swatches" style="grid-template-columns:repeat(%d,minmax(0,1fr))">%s</div>' % (len(colors), "".join(figures))


def combo_html(cid):
    colors = [COLORS[i] for i in COMBOS[cid]]
    return '<article class="wada-card" data-combination="%d"><h3>Combinaison n° %d</h3>%s%s</article>' % (
        cid, cid, swatches(colors), warning_html(colors))


def show_combo(value):
    try:
        number = float(value)
        if not math.isfinite(number) or not number.is_integer() or not 1 <= number <= 348:
            raise ValueError()
        return combo_html(int(number))
    except (ValueError, TypeError, OverflowError):
        return '<p role="alert">Choisir un entier de 1 à 348.</p>'


def show_color(name):
    found = wada.find_colors(COLORS, name) if isinstance(name, str) else []
    if len(found) != 1:
        return '<p role="alert">Choisir un nom dans la liste.</p>'
    color = found[0]
    name = color["name"]
    ids = sorted(color["combinations"])
    return ('<section class="wada-card"><h3>%s</h3>%s%s</section><p>%d combinaisons. %s</p>'
            '<div class="wada-gallery">%s</div>' %
            (escape(name), swatches([color]), warning_html([color]), len(ids), escape(ORDER),
             "".join(combo_html(cid) for cid in ids)))


def nearest_result(value):
    if not isinstance(value, str) or not wada.is_hex(value):
        raise ValueError("Saisir un code HEX de six chiffres, par exemple #00978d.")
    code = "#" + value.strip().lstrip("#").lower()
    exact = wada.find_by_hex(COLORS, code)
    return code, exact, wada.nearest_colors(COLORS, wada.hex_to_rgb(code), 3)


def show_nearest(value):
    try:
        code, exact, neighbors = nearest_result(value)
    except ValueError as exc:
        return '<p role="alert">%s</p>' % escape(exc)
    parts = ['<p>%s</p>' % escape(METHOD)]
    if exact:
        parts.append('<p><strong>correspondance_exacte : %s</strong></p>' % escape(exact["name"]))
    for d00, d76, color in neighbors:
        entered = {"name": "HEX saisi", "hex": code, "cmyk": "non fourni"}
        parts.append('<article class="wada-card"><h3>%s</h3><p>ΔE00 : %.1f ; ΔE76 : %.1f</p>%s%s</article>' %
                     (escape(color["name"]), d00, d76, swatches([entered, color]), warning_html([color])))
    return "".join(parts)


def gallery_ids(size="Toutes", chapter="Tous"):
    count = None if size == "Toutes" else int(size)
    swatch = None if chapter == "Tous" else int(chapter) - 1
    if count not in (None, 2, 3, 4) or swatch not in (None, 0, 1, 2, 3, 4, 5):
        raise ValueError("Filtre invalide.")
    return [cid for cid, indices in COMBOS.items()
            if (count is None or len(indices) == count)
            and (swatch is None or any(COLORS[i]["swatch"] == swatch for i in indices))]


def show_gallery(size="Toutes", chapter="Tous"):
    try:
        ids = gallery_ids(size, chapter)
    except (ValueError, TypeError):
        return '<p role="alert">Choisir les filtres proposés.</p>'
    return '<p>%d combinaisons. %s</p><div class="wada-gallery">%s</div>' % (
        len(ids), escape(ORDER), "".join(combo_html(cid) for cid in ids))


def build_ui():
    import gradio as gr
    with gr.Blocks(title="Sanzo Wada : 348 combinaisons", analytics_enabled=False) as demo:
        gr.Markdown("# Sanzo Wada\nCopie nettoyée 1.3.0. 159 couleurs, 348 combinaisons. " + ORDER)
        gr.Markdown("Trois noms corrigés et magenta de Dull Violet Black ramené à 100 par hypothèse non vérifiée contre le livre papier. Ses RGB, HEX et Lab source sont conservés sans recalcul.")
        with gr.Tab("Combinaison par numéro"):
            number = gr.Number(value=198, minimum=1, maximum=348, precision=0, label="Numéro de combinaison")
            combo = gr.HTML(value=show_combo(198))
            number.change(show_combo, number, combo)
        with gr.Tab("Couleur par nom"):
            name = gr.Dropdown(choices=list(BY_NAME), value="Burnt Sienna", label="Nom dans les données")
            color = gr.HTML(value=show_color("Burnt Sienna"))
            name.change(show_color, name, color)
        with gr.Tab("Plus proche d'un HEX"):
            code = gr.Textbox(value="#00978d", label="Code HEX à six chiffres")
            search = gr.Button("Comparer")
            nearest = gr.HTML(value=show_nearest("#00978d"))
            code.submit(show_nearest, code, nearest)
            search.click(show_nearest, code, nearest)
        with gr.Tab("Les 348"):
            with gr.Row():
                size = gr.Dropdown(choices=["Toutes", "2", "3", "4"], value="Toutes", label="Nombre de couleurs")
                chapter = gr.Dropdown(choices=["Tous", "1", "2", "3", "4", "5", "6"], value="Tous",
                                      label="Chapitre 1 à 6 (base 0 dans les données)")
            gr.Markdown("Filtre chapitre : au moins une couleur de la combinaison appartient au chapitre choisi.")
            gallery = gr.HTML(value=show_gallery())
            size.change(show_gallery, [size, chapter], gallery)
            chapter.change(show_gallery, [size, chapter], gallery)
        gr.HTML('<footer class="wada-provenance">%s</footer>' % escape(PROVENANCE))
    return demo


if __name__ == "__main__":
    build_ui().launch(css=CSS, share=False)
