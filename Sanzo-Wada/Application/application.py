"""Interface Windows locale pour les scripts Sanzo Wada. Aucun réseau."""
import json
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import wada

BG = "#f5f3ed"
INK = "#253339"
MUTED = "#526269"
PROVENANCE = ("CMYK du jeu de données transcrit d'après le livre, non vérifié contre le papier. "
              "HEX : approximation d'écran. Aucun nuancier commercial. Tester les couleurs sur le support réel.")


class ScrollView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, background=BG, highlightthickness=0)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.pack(side="right", fill="y")
        self.body = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(0, 0, anchor="nw", window=self.body)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.resize)
        self.canvas.bind_all("<MouseWheel>", self.wheel, add="+")

    def resize(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)
        width = max(150, event.width - 50)
        for label in self.walk(self.body):
            if isinstance(label, tk.Label) and getattr(label, "wrap_dynamic", False):
                label.configure(wraplength=width)

    def walk(self, widget):
        for child in widget.winfo_children():
            yield child
            yield from self.walk(child)

    def wheel(self, event):
        # Chaque vue reçoit le bind global, seule celle sous le pointeur défile.
        target = self.winfo_containing(event.x_root, event.y_root)
        while target is not None:
            if target == self:
                self.canvas.yview_scroll(-int(event.delta / 120), "units")
                break
            target = target.master

    def clear(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sanzo Wada | Couleurs et combinaisons")
        self.geometry("1180x820")
        self.minsize(820, 600)
        self.configure(background=BG)
        self.option_add("*Font", "{Segoe UI} 10")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=INK, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 10))
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        style.configure("TButton", padding=(12, 7))
        header = ttk.Frame(self, padding=(24, 18))
        header.pack(fill="x")
        ttk.Label(header, text="SANZO WADA", font=("Segoe UI", 24, "bold")).pack(side="left")
        self.source = tk.StringVar(value="Nettoyé 1.3.0")
        choice = ttk.Combobox(header, textvariable=self.source,
                              values=["Nettoyé 1.3.0", "Brut amont"], state="readonly", width=20)
        choice.pack(side="right")
        choice.bind("<<ComboboxSelected>>", self.change_source)
        ttk.Label(self, text="159 couleurs · 348 combinaisons · Tout fonctionne hors connexion",
                  foreground=MUTED, padding=(24, 0, 24, 14)).pack(anchor="w")
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20)
        self.status = tk.StringVar(value="Prêt. Cliquez sur un code HEX pour le copier.")
        bottom = ttk.Frame(self, padding=(24, 10))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Exporter le résultat JSON", command=self.export).pack(side="right")
        ttk.Label(bottom, textvariable=self.status).pack(side="left")
        ttk.Label(self, text=PROVENANCE, foreground=MUTED, wraplength=1100,
                  padding=(24, 4, 24, 16)).pack(fill="x")
        self.payload = {}
        self.gallery_page = 0
        self.load_data()
        self.make_tabs()
        self.refresh_all()
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_current())

    def load_data(self):
        mode = "raw" if self.source.get() == "Brut amont" else "clean"
        colors = wada.load_colors(mode)
        combos = wada.build_combinations(colors)
        anomalies, warning = wada.known_anomalies()
        self.mode, self.colors, self.combos = mode, colors, combos
        self.anomalies, self.global_warning = anomalies, warning

    def make_tab(self, title):
        tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab, text=title)
        controls = ttk.Frame(tab, padding=(0, 0, 0, 12))
        controls.pack(fill="x")
        view = ScrollView(tab)
        view.pack(fill="both", expand=True)
        return controls, view

    def make_tabs(self):
        row, self.combo_view = self.make_tab("Combinaison")
        ttk.Label(row, text="Numéro de 1 à 348").pack(side="left", padx=(0, 10))
        self.combo_number = tk.StringVar(value="198")
        entry = ttk.Spinbox(row, from_=1, to=348, textvariable=self.combo_number, width=8,
                            command=self.show_combo)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.show_combo())
        ttk.Button(row, text="Afficher", command=self.show_combo).pack(side="left", padx=10)

        row, self.color_view = self.make_tab("Par couleur")
        ttk.Label(row, text="Nom ou fragment de nom").pack(side="left", padx=(0, 10))
        self.color_name = tk.StringVar(value="Burnt Sienna")
        self.name_box = ttk.Combobox(row, textvariable=self.color_name, width=32)
        self.name_box.pack(side="left")
        self.name_box.bind("<Return>", lambda e: self.show_color())
        self.name_box.bind("<<ComboboxSelected>>", lambda e: self.show_color())
        ttk.Button(row, text="Rechercher", command=self.show_color).pack(side="left", padx=10)

        row, self.nearest_view = self.make_tab("Proximité HEX")
        self.hex_input = tk.StringVar(value="#00978d")
        ttk.Entry(row, textvariable=self.hex_input, width=15).pack(side="left")
        ttk.Button(row, text="Choisir une couleur", command=self.choose_color).pack(side="left", padx=8)
        ttk.Button(row, text="Comparer", command=self.show_nearest).pack(side="left")

        row, self.suggest_view = self.make_tab("Suggestions")
        self.anchor = tk.StringVar(value="Burnt Sienna")
        self.anchor_box = ttk.Combobox(row, textvariable=self.anchor, width=28)
        self.anchor_box.pack(side="left")
        self.suggest_size = tk.StringVar(value="Toutes")
        ttk.Combobox(row, values=["Toutes", "2", "3", "4"], textvariable=self.suggest_size,
                     state="readonly", width=8).pack(side="left", padx=8)
        ttk.Button(row, text="Voir les accords", command=self.show_suggest).pack(side="left")

        row, self.gallery_view = self.make_tab("Les 348")
        self.gallery_size = tk.StringVar(value="Toutes")
        self.chapter = tk.StringVar(value="Tous")
        ttk.Label(row, text="Couleurs").pack(side="left")
        for variable, values in ((self.gallery_size, ["Toutes", "2", "3", "4"]),
                                 (self.chapter, ["Tous", "1", "2", "3", "4", "5", "6"])):
            box = ttk.Combobox(row, values=values, textvariable=variable, state="readonly", width=8)
            box.pack(side="left", padx=8)
            box.bind("<<ComboboxSelected>>", self.reset_gallery)
            if variable == self.gallery_size:
                ttk.Label(row, text="Chapitre").pack(side="left")
        ttk.Button(row, text="Précédent", command=lambda: self.page(-1)).pack(side="left", padx=6)
        ttk.Button(row, text="Suivant", command=lambda: self.page(1)).pack(side="left")

        row, self.contrast_view = self.make_tab("Contraste")
        self.contrast_a = tk.StringVar(value="#000000")
        self.contrast_b = tk.StringVar(value="#ffffff")
        ttk.Entry(row, textvariable=self.contrast_a, width=25).pack(side="left")
        ttk.Label(row, text="avec").pack(side="left", padx=8)
        ttk.Entry(row, textvariable=self.contrast_b, width=25).pack(side="left")
        ttk.Button(row, text="Calculer", command=self.show_contrast).pack(side="left", padx=8)

    def note(self, parent, text, warning=False):
        label = tk.Label(parent, text=text, justify="left", anchor="w", wraplength=1020,
                         background="#fff1d6" if warning else BG, foreground="#674500" if warning else MUTED,
                         padx=12, pady=12)
        label.wrap_dynamic = True
        label.pack(fill="x", pady=5)

    def warnings(self, parent, colors):
        for warning in dict.fromkeys(wada.warnings_for(colors, self.anomalies)):
            self.note(parent, warning, True)
        if self.global_warning:
            self.note(parent, self.global_warning, True)

    def swatches(self, parent, colors):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=8)
        for i, color in enumerate(colors):
            row.columnconfigure(i, weight=1, uniform="swatch")
            cell = ttk.Frame(row, padding=4)
            cell.grid(row=0, column=i, sticky="nsew")
            paint = tk.Frame(cell, background=color["hex"], height=115)
            paint.pack(fill="x")
            ttk.Label(cell, text=color["name"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8, 3))
            if color.get("name_source"):
                ttk.Label(cell, text="Source : " + color["name_source"], foreground=MUTED).pack(anchor="w")
            ttk.Label(cell, text="CMYK : " + str(color.get("cmyk", "non fourni"))).pack(anchor="w")
            ttk.Button(cell, text=color["hex"], command=lambda c=color: self.copy_hex(c["hex"])).pack(anchor="w", pady=5)
            ttk.Label(cell, text="Approximation d'écran", foreground=MUTED).pack(anchor="w")

    def card(self, parent, cid):
        box = ttk.Frame(parent, padding=12, relief="solid", borderwidth=1)
        box.pack(fill="x", pady=8)
        ttk.Label(box, text="Combinaison n° %d" % cid, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        colors = [self.colors[i] for i in self.combos[cid]]
        self.swatches(box, colors)
        self.warnings(box, colors)

    def set_result(self, kind, value):
        self.payload = {"data_source": self.mode, "type": kind, "resultat": value, "rappel": PROVENANCE}

    def error(self, view, text):
        view.clear()
        self.note(view.body, str(text), True)
        self.payload = {}

    def show_combo(self):
        try:
            cid = int(self.combo_number.get())
            if cid not in self.combos:
                raise ValueError("Choisir un numéro de 1 à 348.")
            self.combo_view.clear()
            self.card(self.combo_view.body, cid)
            self.set_result("combinaison", wada.combo_detail(self.colors, self.combos, cid, self.anomalies))
        except ValueError as error:
            self.error(self.combo_view, error)

    def show_color(self):
        self.color_view.clear()
        matches = wada.find_colors(self.colors, self.color_name.get())
        if len(matches) != 1:
            self.note(self.color_view.body, "Préciser le nom. Résultats : " + ", ".join(c["name"] for c in matches), True)
            self.payload = {}
            return
        color = matches[0]
        self.swatches(self.color_view.body, [color])
        self.warnings(self.color_view.body, [color])
        self.note(self.color_view.body, "%d combinaisons, dans l'ordre du livre." % len(color["combinations"]))
        for cid in color["combinations"]:
            self.card(self.color_view.body, cid)
        self.set_result("couleur", dict(wada.brief(color), combinaisons=color["combinations"],
                                         avertissements=wada.warnings_for([color], self.anomalies)))

    def choose_color(self):
        chosen = colorchooser.askcolor(parent=self, title="Choisir une couleur")
        if chosen[1]:
            self.hex_input.set(chosen[1])
            self.show_nearest()

    def show_nearest(self):
        value = self.hex_input.get().strip()
        if not wada.is_hex(value):
            self.error(self.nearest_view, "Saisir un HEX à six chiffres, par exemple #00978d.")
            return
        self.nearest_view.clear()
        exact = wada.find_by_hex(self.colors, value)
        self.note(self.nearest_view.body, "Correspondance exacte : " + exact["name"] if exact else
                  "Couleurs les plus proches, pas nécessairement identiques au HEX demandé.")
        self.note(self.nearest_view.body, "Tri CIEDE2000 ; CIE76 donné pour comparaison. HEX saisi : conversion sRGB vers Lab D50 Bradford. Dictionnaire : Lab source ICC depuis le CMYK. Un code HEX identique reçoit un écart nul par convention.")
        result = []
        for d00, d76, color in wada.nearest_colors(self.colors, wada.hex_to_rgb(value), 3):
            self.note(self.nearest_view.body, "ΔE00 %.1f · ΔE76 %.1f" % (d00, d76))
            self.swatches(self.nearest_view.body, [{"name": "HEX saisi", "hex": "#" + value.lstrip("#").lower()}, color])
            self.warnings(self.nearest_view.body, [color])
            result.append(dict(wada.brief(color), delta_e00=d00, delta_e76=d76,
                               avertissements=wada.warnings_for([color], self.anomalies)))
        self.set_result("proximité", result)

    def show_suggest(self):
        value = self.anchor.get().strip()
        if wada.is_hex(value):
            color = wada.nearest_colors(self.colors, wada.hex_to_rgb(value), 1)[0][2]
        else:
            found = wada.find_colors(self.colors, value)
            if len(found) != 1:
                self.error(self.suggest_view, "Préciser un nom de couleur ou un HEX.")
                return
            color = found[0]
        size = self.suggest_size.get()
        ids = [cid for cid in color["combinations"] if size == "Toutes" or len(self.combos[cid]) == int(size)]
        self.suggest_view.clear()
        self.note(self.suggest_view.body, "%s : %d accords disponibles. Ordre du livre, sans classement de pertinence." % (color["name"], len(ids)))
        self.warnings(self.suggest_view.body, [color])
        if wada.is_hex(value) and not wada.find_by_hex(self.colors, value):
            delta = wada.nearest_colors(self.colors, wada.hex_to_rgb(value), 1)[0][0]
            self.note(self.suggest_view.body, "Couleur de départ approchée : ΔE00 %.1f. Elle peut être différente de la couleur demandée." % delta, delta > 5)
        for cid in ids:
            self.card(self.suggest_view.body, cid)
        self.set_result("suggestions", [wada.combo_detail(self.colors, self.combos, cid, self.anomalies) for cid in ids])

    def reset_gallery(self, event=None):
        self.gallery_page = 0
        self.show_gallery()

    def page(self, delta):
        self.gallery_page = max(0, self.gallery_page + delta)
        self.show_gallery()

    def show_gallery(self):
        size, chapter = self.gallery_size.get(), self.chapter.get()
        ids = [cid for cid, indices in self.combos.items()
               if (size == "Toutes" or len(indices) == int(size)) and
               (chapter == "Tous" or any(self.colors[i]["swatch"] == int(chapter) - 1 for i in indices))]
        pages = max(1, (len(ids) + 11) // 12)
        self.gallery_page = min(self.gallery_page, pages - 1)
        selected = ids[self.gallery_page * 12:(self.gallery_page + 1) * 12]
        self.gallery_view.clear()
        self.note(self.gallery_view.body, "%d combinaisons · Page %d / %d. Ordre du livre ; chapitre : au moins une couleur du chapitre." %
                  (len(ids), self.gallery_page + 1, pages))
        for cid in selected:
            self.card(self.gallery_view.body, cid)
        self.set_result("galerie", [wada.combo_detail(self.colors, self.combos, cid, self.anomalies) for cid in ids])

    def show_contrast(self):
        self.contrast_view.clear()
        resolved = []
        try:
            for value in (self.contrast_a.get(), self.contrast_b.get()):
                color, rgb, label, _ = wada.resolve_color(self.colors, value.strip())
                if rgb is None:
                    raise ValueError("Couleur introuvable : " + value)
                resolved.append(color or {"name": label, "rgb": rgb, "hex": "#%02x%02x%02x" % tuple(rgb)})
        except ValueError:
            self.error(self.contrast_view, "Préciser deux noms exacts ou deux codes HEX valides.")
            return
        ratio = wada.contrast_ratio(resolved[0]["rgb"], resolved[1]["rgb"])
        self.swatches(self.contrast_view.body, resolved)
        self.note(self.contrast_view.body, "Rapport %.2f:1 · AA texte normal : %s · AA grand texte : %s" %
                  (ratio, "oui" if ratio >= 4.5 else "non", "oui" if ratio >= 3 else "non"))
        self.note(self.contrast_view.body, "Contraste WCAG indicatif pour ces deux valeurs sRGB opaques. Ne certifie pas une interface complète ni une couleur sur un mur.")
        self.warnings(self.contrast_view.body, resolved)
        self.set_result("contraste", {"ratio": ratio, "AA_texte_normal": ratio >= 4.5,
                                      "AA_grand_texte": ratio >= 3,
                                      "couleurs": [{key: c[key] for key in ("name", "hex", "cmyk", "name_source", "derived_values_status") if key in c}
                                                   for c in resolved],
                                      "avertissements": wada.warnings_for(resolved, self.anomalies)})

    def copy_hex(self, value):
        self.clipboard_clear()
        self.clipboard_append(value)
        self.status.set("Code copié : " + value)

    def export(self):
        if not self.payload:
            messagebox.showinfo("Exporter", "Afficher un résultat avant de l'exporter.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json",
                                          initialfile="sanzo-wada-resultat.json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                Path(path).write_text(json.dumps(self.payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                self.status.set("Résultat exporté.")
            except OSError as error:
                messagebox.showerror("Export impossible", str(error), parent=self)

    def refresh_current(self):
        methods = [self.show_combo, self.show_color, self.show_nearest, self.show_suggest, self.show_gallery, self.show_contrast]
        methods[self.notebook.index(self.notebook.select())]()

    def refresh_all(self):
        names = [c["name"] for c in self.colors]
        self.name_box.configure(values=names)
        self.anchor_box.configure(values=names)
        self.show_combo()

    def change_source(self, event=None):
        try:
            self.load_data()
            self.refresh_all()
            self.refresh_current()
            self.status.set("Source : " + self.source.get())
        except (wada.DataError, OSError) as error:
            self.source.set("Brut amont" if self.mode == "raw" else "Nettoyé 1.3.0")
            messagebox.showerror("Données indisponibles", str(error), parent=self)


def main():
    try:
        Application().mainloop()
    except Exception as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Sanzo Wada", "Démarrage impossible :\n" + str(error), parent=root)
        root.destroy()


if __name__ == "__main__":
    main()
