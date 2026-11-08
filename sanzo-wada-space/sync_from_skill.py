"""Copie locale contrôlée des jeux brut et nettoyé vers la Space et le dataset."""
import base64
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

EXPECTED = "555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4"
VERSION = "1.3.0"
BASE = Path(__file__).resolve().parent
RAW = ("colors.json", "combinations.json", "manifest.json", "LICENSE.md")
CLEAN = ("colors.json", "combinations.json", "cleaning.json")


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def atomic(path, blob):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".sync-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def synchronize(skill, space, dataset, check=False, upgrade=False):
    if check and upgrade:
        raise ValueError("--check et --upgrade sont exclusifs.")
    skill, space, dataset = (Path(p).resolve() for p in (skill, space, dataset))
    roots = (skill, space, dataset)
    for i, left in enumerate(roots):
        for right in roots[i + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError("Source, Space et dataset doivent être distincts et non imbriqués.")
    # -B empêche toute écriture __pycache__ dans le skill, y compris en --check.
    verified = subprocess.run([sys.executable, "-B", "-X", "utf8", str(skill / "scripts" / "verify.py")],
                              capture_output=True, encoding="utf-8")
    if verified.returncode:
        raise ValueError("Vérification source refusée : " + verified.stdout + verified.stderr)
    raw = {name: (skill / "data" / name).read_bytes() for name in RAW}
    clean = {name: (skill / "data" / "clean" / name).read_bytes() for name in CLEAN}
    manifest = json.loads(raw["manifest.json"].decode("utf-8"))
    journal = json.loads(clean["cleaning.json"].decode("utf-8"))
    if digest(raw["colors.json"]) != EXPECTED or manifest.get("sha256") != EXPECTED:
        raise ValueError("colors.json brut : empreinte attendue %s ; empreinte lue %s" %
                         (EXPECTED, digest(raw["colors.json"])))
    if journal.get("clean_version") != VERSION or len(journal.get("corrections", [])) != 4:
        raise ValueError("Journal nettoyé : version 1.3.0 et quatre corrections attendues.")
    for name in ("colors.json", "combinations.json"):
        if digest(clean[name]) != journal["output_sha256"][name]:
            raise ValueError("Empreinte nettoyée divergente : " + name)
    mapping = {space / "data" / name: blob for name, blob in raw.items()}
    mapping.update({space / "data" / "clean" / name: blob for name, blob in clean.items()})
    mapping.update({dataset / name: blob for name, blob in raw.items()})
    mapping.update({dataset / "clean" / name: blob for name, blob in clean.items()})
    mapping[space / "wada.py"] = (skill / "scripts" / "wada.py").read_bytes()
    keys = {path: (path.relative_to(space).as_posix() if space in path.parents else
                   "dataset/" + path.relative_to(dataset).as_posix()) for path in mapping}
    hashes = {keys[p]: digest(blob) for p, blob in mapping.items()}
    receipt = space / "sync-receipt.json"
    if receipt.resolve() != receipt or receipt.is_symlink():
        raise ValueError("Reçu indirect refusé.")
    previous = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
    prior_hashes = {key.replace("\\", "/"): value for key, value in previous.get("sha256", {}).items()} if previous else {}
    # Un upgrade est explicite et ne remplace que des copies encore conformes
    # au reçu précédent. Aucune réparation silencieuse d'une copie altérée.
    for path, blob in mapping.items():
        if path.resolve() != path or path.is_symlink():
            raise ValueError("Destination indirecte refusée : %s" % path)
        if path.exists():
            actual = digest(path.read_bytes())
            if actual != digest(blob) and not (upgrade and prior_hashes.get(keys[path]) == actual):
                raise ValueError("%s : empreinte attendue %s ; empreinte lue %s" %
                                 (path, digest(blob), actual))
        elif check:
            raise ValueError("Copie manquante : %s" % path)
    if previous and prior_hashes != hashes and not upgrade and not check:
        raise ValueError("Reçu d'une autre version : utiliser --upgrade après revue.")
    for key, old_hash in prior_hashes.items():
        if key not in hashes:
            raise ValueError("Copie ancienne non prévue, migration à revoir : " + key)
    if check:
        if (not previous or previous.get("source_version") != VERSION or prior_hashes != hashes
                or previous.get("upstream_commit") != manifest["commit_amont"]):
            raise ValueError("Reçu absent ou différent de la copie 1.3.0 attendue.")
    else:
        for path, blob in mapping.items():
            if not path.exists() or path.read_bytes() != blob:
                atomic(path, blob)
        record = {"source_version": VERSION,
                  "copied_at_utc": previous["copied_at_utc"] if previous and prior_hashes == hashes else
                                   datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "upstream_commit": manifest["commit_amont"], "sha256": hashes}
        if not receipt.exists() or json.loads(receipt.read_text(encoding="utf-8")) != record:
            atomic(receipt, encoded(record))
    for path, blob in mapping.items():
        if path.read_bytes() != blob:
            raise ValueError("Copie divergente après synchronisation : %s" % path)
    # Exact bytes, encoded for script loading under file:// as well as HTTPS.
    payload = {"receipt": json.loads(receipt.read_text(encoding="utf-8")),
               "files": {keys[p]: base64.b64encode(blob).decode("ascii")
                         for p, blob in mapping.items() if space in p.parents}}
    bundle = ("globalThis.WADA_SNAPSHOT = " + json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + ";\n").encode("utf-8")
    target = space / "snapshot.js"
    if check:
        if not target.exists() or target.read_bytes() != bundle:
            raise ValueError("snapshot.js divergent : relancer la synchronisation.")
    elif not target.exists() or target.read_bytes() != bundle:
        atomic(target, bundle)
    return {"status": "OK", "mode": "check" if check else "upgrade" if upgrade else "sync",
            "source_version": VERSION, "raw_colors_sha256": EXPECTED,
            "clean_colors_sha256": digest(clean["colors.json"]), "files_checked": len(mapping)}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=BASE.parent / "Sanzo-Wada")
    parser.add_argument("--dataset-dir", type=Path, default=BASE.parent / "sanzo-wada-dictionary")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Vérification sans écriture")
    group.add_argument("--upgrade", action="store_true", help="Migration explicite des copies validées par le reçu précédent")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(synchronize(args.skill_dir, BASE, args.dataset_dir, args.check, args.upgrade), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(json.dumps({"erreur": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
