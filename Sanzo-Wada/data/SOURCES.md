# Sources des données

| Fichier | Nature | Origine |
|---|---|---|
| `colors.json` | Original amont, non modifié | Dépôt `mattdesl/dictionary-of-colour-combinations` (MIT), version 1.0.2, commit `d44d2b5a18cf595aa536676a5cf67046a6b503f6` (dernier commit touchant `colors.json`, 2020-05-27), récupéré le 2026-11-04 |
| `combinations.json` | Dérivé, généré localement | `scripts/build_combinations.py` à partir de `colors.json` ; fichier de consultation, les scripts recalculent l'index |
| `manifest.json` | Traçabilité | Commit, URL figée, édition du livre, empreinte SHA-256, licence, registre des anomalies connues |
| `LICENSE.md` | Licence amont | Copie de la licence MIT du dépôt de Matt DesLauriers |
| `UPSTREAM-README.md` | Documentation amont | Copie du README du dépôt (le dossier `images/` qu'il référence n'a pas été copié) |

URL figée du fichier : `https://raw.githubusercontent.com/mattdesl/dictionary-of-colour-combinations/d44d2b5a18cf595aa536676a5cf67046a6b503f6/colors.json`

## Chaîne de provenance

1. Livre : Sanzo Wada, *A Dictionary of Color Combinations*, Seigensha, 2010, ISBN 978-4-86152-247-5 (original japonais *Haishoku Sōkan*, 1933-1934 selon le README amont, non confirmé).
2. Transcription et publication en open source des valeurs CMYK par Dain M. Blodorn Kim (`dblodorn/sanzo-wada`).
3. Correction de données incorrectes et nouvelle conversion CMYK vers RGB par Matt DesLauriers
   (profils : CMYK U.S. Web Coated SWOP v2, RGB sRGB IEC61966-2.1, relatif colorimétrique avec compensation du point noir).
4. Copie dans ce skill, sans modification.

## Ce qui est original et ce qui est dérivé

- Issu du livre (via transcription) : noms des couleurs, valeurs CMYK, appartenance aux combinaisons, chapitre (`swatch`, base 0).
- Calculé : `rgb`, `hex`, `lab`. Ce sont des approximations d'écran des couleurs imprimées.

## Pour vérifier

`python scripts/verify.py` : contrôle le nombre de couleurs (159), de combinaisons (348), les types et bornes, la cohérence HEX/RGB,
l'empreinte de `colors.json` (obligatoire) et la conformité de `combinations.json`. `python -m unittest discover -s tests` : tests de non-régression.

## Limite connue

Les corrections ont été faites par une seule personne et n'ont pas été comparées ici au livre papier.
Un échantillonnage contre le livre reste à faire avant de présenter ces valeurs comme exactes.
