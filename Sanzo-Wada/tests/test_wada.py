"""Tests de non-régression du skill Sanzo Wada (unittest, bibliothèque standard).

Usage : python -m unittest discover -s tests   (depuis le dossier du skill)
   ou : py tests/test_wada.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import wada  # noqa: E402


class Colorimetrie(unittest.TestCase):
    def test_blanc_srgb_donne_lab_100_0_0(self):
        L, a, b = wada.rgb_to_lab([255, 255, 255])
        self.assertAlmostEqual(L, 100.0, places=2)
        self.assertAlmostEqual(a, 0.0, places=1)
        self.assertAlmostEqual(b, 0.0, places=1)

    def test_noir_srgb_donne_L_0(self):
        self.assertAlmostEqual(wada.rgb_to_lab([0, 0, 0])[0], 0.0, places=3)

    def test_ciede2000_paire_de_reference_sharma_1(self):
        # Sharma, Wu, Dalal (2005), paire 1 : ΔE00 attendu 2.0425
        d = wada.delta_e2000((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485))
        self.assertAlmostEqual(d, 2.0425, places=3)

    def test_ciede2000_paire_de_reference_sharma_7(self):
        # paire 7 : (50, 0, 0) vs (50, -1, 2) -> 2.3669
        d = wada.delta_e2000((50.0, 0.0, 0.0), (50.0, -1.0, 2.0))
        self.assertAlmostEqual(d, 2.3669, places=3)

    def test_ciede2000_symetrique_et_nul_sur_identique(self):
        a, b = (53.2, 80.1, 67.2), (30.0, -10.0, 5.0)
        self.assertAlmostEqual(wada.delta_e2000(a, b), wada.delta_e2000(b, a), places=9)
        self.assertEqual(wada.delta_e2000(a, a), 0.0)

    def test_cie76(self):
        self.assertAlmostEqual(wada.delta_e76((0, 0, 0), (3, 4, 0)), 5.0)

    def test_contraste_noir_blanc_21(self):
        self.assertAlmostEqual(wada.contrast_ratio([0, 0, 0], [255, 255, 255]), 21.0, places=6)
        self.assertAlmostEqual(wada.contrast_ratio([255, 255, 255], [0, 0, 0]), 21.0, places=6)


class Donnees(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.colors = wada.load_colors("raw")
        cls.combos = wada.build_combinations(cls.colors)

    def test_effectifs(self):
        self.assertEqual(len(self.colors), 159)
        self.assertEqual(len(self.combos), 348)
        self.assertEqual(list(self.combos), list(range(1, 349)))

    def test_recherche_exacte_prime_sur_partielle(self):
        self.assertEqual([c["name"] for c in wada.find_colors(self.colors, "blue")], ["Blue"])
        self.assertGreater(len(wada.similar_names(self.colors, "blue", exclude=["Blue"])), 5)

    def test_hex_exact_reconnu(self):
        c = wada.find_by_hex(self.colors, "#AE5224")
        self.assertEqual(c["name"], "Burnt Sienna")
        self.assertIsNone(wada.find_by_hex(self.colors, "#123456"))

    def test_nearest_renvoie_la_couleur_elle_meme_pour_burnt_sienna(self):
        d00, d76, c = wada.nearest_colors(self.colors, [174, 82, 36], 1)[0]
        self.assertEqual(c["name"], "Burnt Sienna")
        self.assertLess(d00, 1.0)

    def test_nearest_hex_exact_passe_en_tete_meme_pour_teinte_saturee(self):
        # Benzol Green #00978d : l'asymétrie des deux chaînes Lab classerait une autre couleur devant.
        d00, d76, c = wada.nearest_colors(self.colors, [0x00, 0x97, 0x8d], 1)[0]
        self.assertEqual(c["name"], "Benzol Green")
        self.assertEqual(d00, 0.0)

    def test_resolve_color_nom_et_hex(self):
        c, rgb, label, ecart = wada.resolve_color(self.colors, "Hermosa Pink")
        self.assertEqual(c["name"], "Hermosa Pink")
        self.assertEqual(ecart, 0.0)
        c2, rgb2, label2, ecart2 = wada.resolve_color(self.colors, "#123456")
        self.assertIsNone(c2)
        self.assertEqual(rgb2, [0x12, 0x34, 0x56])
        with self.assertRaises(ValueError):
            wada.resolve_color(self.colors, "Drab")

    def test_anomalies_du_manifeste(self):
        anomalies, avert = wada.known_anomalies()
        self.assertIsNone(avert)
        self.assertIn("Dull Violet Black", anomalies)
        self.assertIn("Calamine BLue", anomalies)
        w = wada.warnings_for([c for c in self.colors if c["name"] == "Dull Violet Black"], anomalies)
        self.assertEqual(len(w), 1)

    def test_manifeste_invalide_donne_avertissement_global(self):
        anomalies, avert = wada.known_anomalies([])
        self.assertEqual(anomalies, {})
        self.assertIsNotNone(avert)


class Validation(unittest.TestCase):
    def base(self):
        return {"name": "X", "combinations": [1], "swatch": 0, "cmyk": [0, 0, 0, 0],
                "lab": [50.0, 0.0, 0.0], "rgb": [255, 255, 255], "hex": "#ffffff"}

    def test_lab_textuel_refuse(self):
        c = self.base()
        c["lab"] = ["bad", 0, 0]
        with self.assertRaises(wada.DataError):
            wada._check_color(0, c)

    def test_lab_nan_refuse(self):
        c = self.base()
        c["lab"] = [float("nan"), 0, 0]
        with self.assertRaises(wada.DataError):
            wada._check_color(0, c)

    def test_champ_manquant_refuse(self):
        c = self.base()
        del c["hex"]
        with self.assertRaises(wada.DataError):
            wada._check_color(0, c)

    def test_couleur_valide_acceptee(self):
        wada._check_color(0, self.base())


if __name__ == "__main__":
    unittest.main(verbosity=1)
