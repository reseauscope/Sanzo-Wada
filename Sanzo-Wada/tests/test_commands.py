"""Contrats CLI réels sur copies temporaires, jamais sur les données source."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Commands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("scripts", "data"):
            shutil.copytree(str(ROOT / folder), str(self.root / folder))

    def command(self, script, *args, code=0):
        # Les contrats historiques portent explicitement sur la copie brute.
        # test_clean.py vérifie séparément le nouveau défaut clean et les deux modes.
        options = [] if script == "verify.py" else ["--data-source", "raw"]
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(self.root / "scripts" / script)] + list(args) + options,
                                cwd=self.temp.name, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        return result.stdout

    def mutate_color(self, field, value):
        path = self.root / "data" / "colors.json"
        colors = json.loads(path.read_text(encoding="utf-8"))
        colors[0][field] = value
        path.write_text(json.dumps(colors), encoding="utf-8")

    def test_lookup_combo(self):
        out = json.loads(self.command("lookup.py", "combo", "198"))
        self.assertEqual([c["name"] for c in out["resultat"]["colors"]],
                         ["Burnt Sienna", "Apricot Yellow", "Green"])

    def test_lookup_ambiguous(self):
        out = json.loads(self.command("lookup.py", "color", "Drab", code=1))
        self.assertGreater(len(out["ambigu"]), 1)

    def test_lookup_not_found(self):
        self.assertIn("erreur", json.loads(self.command("lookup.py", "color", "absent-name", code=1)))

    def test_lookup_bad_option(self):
        self.assertIn("erreur", json.loads(self.command("lookup.py", "nearest", "#00978d", "--n", "0", code=2)))

    def test_lookup_missing_argument(self):
        self.command("lookup.py", "combo", code=2)

    def test_nearest_exact(self):
        out = json.loads(self.command("lookup.py", "nearest", "#00978d", "--n", "1"))
        self.assertEqual(out["correspondance_exacte"], "Benzol Green")
        self.assertEqual(out["plus_proches"][0]["ecart_delta_e_2000"], 0)

    def test_brief_warns_for_every_affected_combination(self):
        colors = json.loads((self.root / "data" / "colors.json").read_text(encoding="utf-8"))
        manifest = json.loads((self.root / "data" / "manifest.json").read_text(encoding="utf-8"))
        # Interroger une couleur saine qui partage une combinaison avec l'anomalie.
        anchor = next(c for c in colors if c["name"] != "Dull Violet Black" and 95 in c["combinations"])
        out = json.loads(self.command("lookup.py", "color", anchor["name"], "--brief"))
        combo = next(c for c in out["resultats"][0]["combinations"] if c["combination"] == 95)
        anomaly = next(a for a in manifest["anomalies_connues"] if a["couleur"] == "Dull Violet Black")
        self.assertIn("Dull Violet Black : " + anomaly["constat"], combo["avertissements"])
        self.assertTrue(all(isinstance(name, str) for name in combo["colors"]))

    def test_missing_manifest_preserves_global_warning(self):
        (self.root / "data" / "manifest.json").unlink()
        out = json.loads(self.command("lookup.py", "color", "Burnt Sienna", "--brief"))
        self.assertIn("avertissement_global", out)

    def test_missing_colors_all_commands(self):
        (self.root / "data" / "colors.json").unlink()
        for script, args in (("lookup.py", ["list"]), ("suggest.py", ["Blue"]),
                             ("contrast.py", ["#000000", "#ffffff"]), ("verify.py", [])):
            with self.subTest(script=script):
                self.assertIn("erreur", json.loads(self.command(script, *args, code=1)))

    def test_rgb_invalid_rejected_by_ordinary_commands(self):
        self.mutate_color("rgb", [256, 0, 0])
        for script, args in (("lookup.py", ["list"]), ("suggest.py", ["Blue"]),
                             ("contrast.py", ["#000000", "#ffffff"])):
            with self.subTest(script=script):
                self.assertIn("RGB", json.loads(self.command(script, *args, code=1))["erreur"])

    def test_boolean_combination_rejected(self):
        self.mutate_color("combinations", [True])
        self.assertIn("booléens", json.loads(self.command("lookup.py", "list", code=1))["erreur"])

    def test_duplicate_combination_rejected(self):
        self.mutate_color("combinations", [1, 1])
        self.assertIn("répété", json.loads(self.command("lookup.py", "list", code=1))["erreur"])

    def test_out_of_range_combination_rejected(self):
        self.mutate_color("combinations", [349])
        self.command("lookup.py", "list", code=1)

    def test_hex_rgb_mismatch_rejected(self):
        self.mutate_color("hex", "#000000")
        self.assertIn("incohérents", json.loads(self.command("lookup.py", "list", code=1))["erreur"])

    def test_undocumented_cmyk_rejected(self):
        self.mutate_color("cmyk", [101, 0, 0, 0])
        self.command("lookup.py", "list", code=1)

    def test_invalid_lab_lightness_rejected(self):
        self.mutate_color("lab", [101, 0, 0])
        self.command("lookup.py", "list", code=1)

    def test_invalid_chapter_rejected(self):
        self.mutate_color("swatch", 6)
        self.command("lookup.py", "list", code=1)

    def test_collection_invariants_rejected_at_load(self):
        path = self.root / "data" / "colors.json"
        original = path.read_text(encoding="utf-8")
        for case in ("count", "duplicate_name", "missing_chapter", "missing_combination", "oversized_combination"):
            with self.subTest(case=case):
                colors = json.loads(original)
                if case == "count":
                    colors.pop()
                elif case == "duplicate_name":
                    colors[0]["name"] = colors[1]["name"]
                elif case == "missing_chapter":
                    for color in colors:
                        if color["swatch"] == 5:
                            color["swatch"] = 4
                elif case == "missing_combination":
                    for color in colors:
                        color["combinations"] = [cid for cid in color["combinations"] if cid != 198]
                else:
                    for color in colors[:5]:
                        if 198 not in color["combinations"]:
                            color["combinations"].append(198)
                path.write_text(json.dumps(colors), encoding="utf-8")
                self.command("lookup.py", "list", code=1)

    def test_suggest_bad_max(self):
        self.command("suggest.py", "Blue", "--max", "-1", code=2)

    def test_suggest_and_contrast_warnings(self):
        for script, args in (("suggest.py", ["Dull Violet Black"]),
                             ("contrast.py", ["Dull Violet Black", "Blue"])):
            with self.subTest(script=script):
                out = json.loads(self.command(script, *args))
                self.assertTrue(out["avertissements"])

    def test_contrast_black_white(self):
        out = json.loads(self.command("contrast.py", "#000000", "#ffffff"))
        self.assertEqual(out["paires"][0]["ratio"], 21)

    def test_verify_invalid_utf8(self):
        (self.root / "data" / "combinations.json").write_bytes(b"\xff")
        self.assertIn("erreur", json.loads(self.command("verify.py", code=1)))

    def test_verify_unreadable_combinations(self):
        path = self.root / "data" / "combinations.json"
        path.unlink()
        path.mkdir()  # Erreur OSError réelle, portable Windows/Linux.
        self.assertIn("erreur", json.loads(self.command("verify.py", code=1)))

    def test_verify_malformed_combinations_shape(self):
        (self.root / "data" / "combinations.json").write_text('{"combinations": 42}', encoding="utf-8")
        self.assertIn("combinations doit être une liste", self.command("verify.py", code=1))

    def test_verify_second_colors_read_oserror(self):
        # Injection limitée à la lecture binaire de l'empreinte, après le chargement JSON.
        code = ("import builtins,runpy,sys; from unittest.mock import patch; "
                "original=builtins.open; "
                "sys.path.insert(0,sys.argv[1]); "
                "guard=lambda p,*a,**k: (_ for _ in ()).throw(PermissionError('test fingerprint')) "
                "if str(p).endswith('colors.json') and a and a[0]=='rb' else original(p,*a,**k); "
                "mock=patch('builtins.open',guard); mock.start(); "
                "runpy.run_path(sys.argv[1]+'/verify.py',run_name='__main__')")
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", code, str(self.root / "scripts")],
                                capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("test fingerprint", json.loads(result.stdout)["erreur"])


if __name__ == "__main__":
    unittest.main()
