"""Nettoyage fermé, modes CLI et mutations sur copies temporaires uniquement."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import wada


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Clean(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("scripts", "data"):
            shutil.copytree(str(ROOT / name), str(self.root / name))

    def run_cli(self, script, *args, code=0):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(self.root / "scripts" / script)] + list(args),
                                capture_output=True, encoding="utf-8", cwd=self.temp.name)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        return result.stdout

    def read(self, name):
        return json.loads((self.root / "data" / name).read_text(encoding="utf-8"))

    def write(self, name, value):
        (self.root / "data" / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_four_corrections_and_no_uppercase(self):
        raw, clean = self.read("colors.json"), self.read("clean/colors.json")
        self.assertEqual(len(raw), len(clean))
        self.assertEqual(len(clean), 159)
        self.assertEqual(len(self.read("clean/combinations.json")["combinations"]), 348)
        self.assertEqual(sum(a != b for a, b in zip(raw, clean)), 4)
        self.assertFalse(any(c["hex"] != c["hex"].lower() for c in raw))
        for a, b in zip(raw, clean):
            self.assertEqual(a["combinations"], b["combinations"])
            for key in ("rgb", "hex", "lab", "swatch"):
                self.assertEqual(a[key], b[key])
        self.assertEqual(len(self.read("clean/cleaning.json")["corrections"]), 4)

    def test_default_clean_old_names_and_raw(self):
        for old, new in (("Calamine BLue", "Calamine Blue"), ("Cerulian Blue", "Cerulean Blue"),
                         ("Antwarp Blue", "Antwerp Blue")):
            with self.subTest(old=old):
                out = json.loads(self.run_cli("lookup.py", "color", old, "--brief"))
                self.assertEqual(out["data_source"], "clean")
                self.assertEqual(out["resultats"][0]["name"], new)
                self.assertEqual(out["resultats"][0]["name_source"], old)
                raw = json.loads(self.run_cli("lookup.py", "color", old, "--brief", "--data-source", "raw"))
                self.assertEqual(raw["resultats"][0]["name"], old)
                self.assertTrue(raw["resultats"][0]["avertissements"])

    def test_suggest_contrast_default_and_raw(self):
        for script, args in (("suggest.py", ["Cerulian Blue", "--max", "1"]),
                             ("contrast.py", ["Cerulian Blue", "Blue"])):
            for source in (None, "clean", "raw"):
                with self.subTest(script=script, source=source):
                    options = [] if source is None else ["--data-source", source]
                    out = json.loads(self.run_cli(script, *args, *options))
                    self.assertEqual(out["data_source"], source or "clean")

    def test_dull_remains_in_nearest_and_contrast(self):
        dull = next(c for c in self.read("clean/colors.json") if c["name"] == "Dull Violet Black")
        self.assertEqual(dull["cmyk"], [95, 100, 38, 50])
        nearest = json.loads(self.run_cli("lookup.py", "nearest", dull["hex"], "--n", "1"))
        found = nearest["plus_proches"][0]
        self.assertEqual(found["name"], "Dull Violet Black")
        self.assertEqual(found["ecart_delta_e_2000"], 0)
        self.assertEqual(found["derived_values_status"], "source_before_cmyk_correction")
        self.assertIn("derived_values_status=", " ".join(found["avertissements"]))
        contrast = json.loads(self.run_cli("contrast.py", "Dull Violet Black", "Blue"))
        self.assertTrue(contrast["paires"])
        self.assertIn("derived_values_status=", " ".join(contrast["avertissements"]))
        self.assertEqual(contrast["colors"][0]["derived_values_status"], "source_before_cmyk_correction")

    def test_warning_survives_missing_manifest_and_brief(self):
        (self.root / "data/manifest.json").unlink()
        for script, args in (("lookup.py", ["color", "Dull Violet Black", "--brief"]),
                             ("suggest.py", ["Dull Violet Black"]), ("contrast.py", ["combo", "95"])):
            out = json.loads(self.run_cli(script, *args))
            self.assertIn("avertissement_global", out)
            self.assertIn("derived_values_status=", json.dumps(out))
        combo = json.loads(self.run_cli("lookup.py", "combo", "95"))["resultat"]
        self.assertIn("derived_values_status=", " ".join(combo["avertissements"]))

    def test_nearest_all_colors_retained_and_alias_function(self):
        clean = wada.load_colors()
        self.assertEqual(len(wada.nearest_colors(clean, [12, 34, 56], 159)), 159)
        for old in ("Calamine BLue", "Cerulian Blue", "Antwarp Blue"):
            self.assertEqual(wada.find_colors(clean, old)[0]["name_source"], old)

    def test_generator_deterministic_and_raw_unchanged(self):
        paths = [self.root / "data" / name for name in ("colors.json", "manifest.json", "combinations.json")]
        before = [sha(p) for p in paths]
        expected = {p.name: p.read_bytes() for p in (self.root / "data/clean").iterdir()}
        for _ in range(2):
            self.run_cli("build_clean.py")
            self.assertEqual(expected, {p.name: p.read_bytes() for p in (self.root / "data/clean").iterdir()})
        self.assertEqual(before, [sha(p) for p in paths])
        self.run_cli("verify.py")

    def test_verifier_independent_of_generator(self):
        (self.root / "scripts/build_clean.py").write_text("raise RuntimeError('not to be imported')\n", encoding="utf-8")
        self.run_cli("verify.py")

    def test_mutations_rejected_even_if_output_hash_is_updated(self):
        original = {name: (self.root / "data/clean" / name).read_bytes()
                    for name in ("colors.json", "combinations.json", "cleaning.json")}
        for case in ("extra_change", "missing_name", "missing_alias", "dull_value", "dull_rgb", "dull_status",
                     "membership", "combo_name", "journal_missing", "journal_extra", "journal_pointer", "certainty"):
            with self.subTest(case=case):
                for name, blob in original.items():
                    (self.root / "data/clean" / name).write_bytes(blob)
                colors, combos, journal = [self.read("clean/" + name) for name in original]
                dull = next(c for c in colors if c["name"] == "Dull Violet Black")
                renamed = next(c for c in colors if c.get("name_source") == "Cerulian Blue")
                if case == "extra_change": colors[0]["lab"][1] += 1
                elif case == "missing_name": renamed["name"] = renamed["name_source"]
                elif case == "missing_alias": del renamed["name_source"]
                elif case == "dull_value": dull["cmyk"][1] = 99
                elif case == "dull_rgb": dull["rgb"][0] += 1
                elif case == "dull_status": del dull["derived_values_status"]
                elif case == "membership": colors[0]["combinations"].pop()
                elif case == "combo_name": combos["combinations"][0]["colors"][0] = "Unexpected"
                elif case == "journal_missing": journal["corrections"].pop()
                elif case == "journal_extra": journal["corrections"].append(journal["corrections"][0])
                elif case == "journal_pointer": journal["corrections"][0]["changes"][0]["pointer"] = "/0/name"
                elif case == "certainty": journal["corrections"][3]["certainty"] = "certified"
                self.write("clean/colors.json", colors)
                self.write("clean/combinations.json", combos)
                journal["output_sha256"] = {name: sha(self.root / "data/clean" / name)
                                             for name in ("colors.json", "combinations.json")}
                self.write("clean/cleaning.json", journal)
                self.run_cli("verify.py", code=1)

    def test_partial_or_missing_clean_fails_without_raw_fallback(self):
        (self.root / "data/clean/colors.json").unlink()
        self.run_cli("lookup.py", "list", code=1)
        self.run_cli("verify.py", code=1)
        self.run_cli("lookup.py", "list", "--data-source", "raw")

    def test_raw_mutation_rejected_by_generator_and_verifier(self):
        path = self.root / "data/colors.json"
        path.write_bytes(path.read_bytes() + b" ")
        self.run_cli("build_clean.py", code=1)
        self.run_cli("verify.py", code=1)

    def test_wrong_source_usage(self):
        for script, args in (("lookup.py", ["list"]), ("suggest.py", ["Blue"]),
                             ("contrast.py", ["Blue", "Green"])):
            self.run_cli(script, *args, "--data-source", "unknown", code=2)
            self.run_cli(script, *args, "--data-source", code=2)


if __name__ == "__main__":
    unittest.main()
