"""Construit la copie nettoyée localement, sans écrire dans le brut. Python 3.8+."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

from clean_schema import (DERIVED_STATUS, MANIFEST_SHA256, SOURCE_SHA256, VERSION,
                          encoded, file_changes, sha)
from wada import DATA, DataError, fail, load_colors, utf8_stdout
from wada import build_combinations
from build_combinations import render

RENAMES = (("Calamine BLue", "Calamine Blue", "certaine : correction typographique décidée par Jean"),
           ("Cerulian Blue", "Cerulean Blue", "décision de Jean ; fidélité au livre non vérifiée"),
           ("Antwarp Blue", "Antwerp Blue", "décision de Jean ; fidélité au livre non vérifiée"))


def atomic(path, blob):
    fd, temporary = tempfile.mkstemp(prefix=".clean-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build():
    root = Path(DATA)
    source = {name: (root / name).read_bytes()
              for name in ("colors.json", "combinations.json", "manifest.json")}
    if sha(source["colors.json"]) != SOURCE_SHA256 or sha(source["manifest.json"]) != MANIFEST_SHA256:
        raise DataError("Empreinte du brut ou du manifeste différente de la source autorisée.")
    colors = load_colors("raw")
    if source["combinations.json"] != render(colors, build_combinations(colors)).encode("utf-8"):
        raise DataError("Les combinaisons brutes ne correspondent pas au rendu de référence.")
    raw = {name: json.loads(source[name].decode("utf-8")) for name in ("colors.json", "combinations.json")}
    uppercase = [c["hex"] for c in raw["colors.json"] if c["hex"] != c["hex"].lower()]
    if uppercase:
        raise DataError("HEX en majuscules détectés : normalisation non autorisée dans ce lot fermé.")
    current = copy.deepcopy(raw)
    corrections = []
    for old, new, certainty in RENAMES:
        before = copy.deepcopy(current)
        index = next(i for i, c in enumerate(current["colors.json"]) if c["name"] == old)
        color = current["colors.json"][index]
        color["name_source"] = old
        color["name"] = new
        for combo in current["combinations.json"]["combinations"]:
            combo["colors"] = [new if name == old else name for name in combo["colors"]]
        corrections.append({"source_index": index, "source_name": old,
                            "reason": "Correction du nom décidée par Jean le 2026-11-08.",
                            "certainty": certainty, "changes": file_changes(before, current)})
    before = copy.deepcopy(current)
    index = next(i for i, c in enumerate(current["colors.json"]) if c["name"] == "Dull Violet Black")
    color = current["colors.json"][index]
    color["cmyk_source"] = copy.deepcopy(color["cmyk"])
    color["cmyk"][1] = 100
    color["derived_values_status"] = DERIVED_STATUS
    for combo in current["combinations.json"]["combinations"]:
        for pos, name in enumerate(combo["colors"]):
            if name == "Dull Violet Black":
                combo["cmyk"][pos] = list(color["cmyk"])
    corrections.append({"source_index": index, "source_name": "Dull Violet Black",
                        "reason": "Magenta 106 ramené à la borne 100 sur décision de Jean le 2026-11-08 ; dérivés conservés sans recalcul.",
                        "certainty": "hypothèse de correction de borne, non vérifiée contre le livre papier",
                        "changes": file_changes(before, current)})
    output = {name: encoded(value) for name, value in current.items()}
    journal = {"schema_version": 1, "clean_version": VERSION, "decision_date": "2026-11-08",
               "source_sha256": {name: sha(blob) for name, blob in source.items()},
               "output_sha256": {name: sha(blob) for name, blob in output.items()},
               "uppercase_hex_count": 0, "corrections": corrections}
    target = root / "clean"
    target.mkdir(exist_ok=True)
    # Journal écrit en dernier ; un lot interrompu échoue au contrôle d'empreintes.
    for name, blob in output.items():
        atomic(target / name, blob)
    atomic(target / "cleaning.json", encoded(journal))
    for name, blob in source.items():
        if (root / name).read_bytes() != blob:
            raise DataError("Brut modifié pendant la génération : %s." % name)
    print("OK : copie nettoyée %s, quatre corrections, aucun HEX en majuscules, brut intact." % VERSION)
    return 0


def main():
    utf8_stdout()
    try:
        return build()
    except (DataError, OSError, UnicodeError, ValueError, KeyError, TypeError, StopIteration) as exc:
        return fail("Nettoyage impossible : %s" % exc)


if __name__ == "__main__":
    sys.exit(main())
