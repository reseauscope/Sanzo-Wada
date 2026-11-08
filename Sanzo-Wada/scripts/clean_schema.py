"""Sérialisation et différences JSON communes, sans logique de nettoyage."""
import hashlib
import json

VERSION = "1.3.0"
SOURCE_SHA256 = "555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4"
MANIFEST_SHA256 = "4a3909f3f4d713f94c19a84d0d0fd52999461ea821e6b8706d7c979db3684440"
DERIVED_STATUS = "source_before_cmyk_correction"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def differences(before, after, pointer=""):
    """Changements élémentaires avec JSON Pointer RFC 6901 et présence explicite."""
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            path = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                result.append({"pointer": path, "operation": "add", "before_present": False,
                               "after": after[key]})
            elif key not in after:
                result.append({"pointer": path, "operation": "remove", "before_present": True,
                               "before": before[key]})
            else:
                result.extend(differences(before[key], after[key], path))
        return result
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [change for i, (a, b) in enumerate(zip(before, after))
                for change in differences(a, b, pointer + "/" + str(i))]
    if type(before) is type(after) and before == after:
        return []
    return [{"pointer": pointer, "operation": "replace", "before_present": True,
             "before": before, "after": after}]


def file_changes(before, after):
    return [dict(change, file=name) for name in sorted(before)
            for change in differences(before[name], after[name])]
