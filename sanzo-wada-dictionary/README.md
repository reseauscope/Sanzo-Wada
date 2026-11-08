---
license: mit
language:
- en
- fr
pretty_name: Sanzo Wada Dictionary of Color Combinations
size_categories:
- n<1K
configs:
- config_name: clean_colors
  default: true
  data_files:
  - split: train
    path: clean/colors.json
- config_name: clean_combinations
  data_files:
  - split: train
    path: clean/combinations.json
  field: combinations
- config_name: raw_colors
  data_files:
  - split: train
    path: colors.json
- config_name: raw_combinations
  data_files:
  - split: train
    path: combinations.json
  field: combinations
---

# Sanzo Wada : jeux brut et nettoyé 1.3.0

159 couleurs et 348 combinaisons dans chaque jeu : 120 duos, 120 trios, 108 quatuors. Même ordre, mêmes chapitres et mêmes appartenances. La configuration par défaut est `clean_colors`. Préparation exclusivement locale, aucune publication effectuée.

## Deux jeux distincts

| Configuration | Fichier | Signification |
|---|---|---|
| clean_colors | clean/colors.json | Noms corrigés et magenta borné par hypothèse |
| clean_combinations | clean/combinations.json | Combinaisons du nettoyé, schéma conservé |
| raw_colors | colors.json | Copie brute amont, intacte |
| raw_combinations | combinations.json | Fichier dérivé brut du skill, copié sans régénération |

Les configurations de combinaisons sélectionnent la liste imbriquée par `field: combinations`. Elles ne mélangent pas les données de schémas différents. `clean/cleaning.json` est un journal de provenance, pas une configuration de données tabulaires.

## Corrections et traçabilité

| Brut | Nettoyé | Statut |
|---|---|---|
| Calamine BLue | Calamine Blue | Correction typographique décidée par Jean |
| Cerulian Blue | Cerulean Blue | Décision de Jean, fidélité au livre non vérifiée |
| Antwarp Blue | Antwerp Blue | Décision de Jean, fidélité au livre non vérifiée |
| Dull Violet Black, CMYK [95,106,38,50] | CMYK [95,100,38,50] | Hypothèse de correction de borne non vérifiée contre le livre papier |

Les trois noms originaux sont conservés dans `name_source`. Pour Dull Violet Black, `cmyk_source` garde le CMYK brut et `derived_values_status=source_before_cmyk_correction` signale que RGB, HEX et Lab source sont conservés sans recalcul. Ils ne sont pas une conversion du CMYK corrigé et ne sont pas sûrs. Le maintien de cette couleur dans nearest et contrast s'accompagne d'un avertissement explicite dans le module 1.3.0.

Le journal `clean/cleaning.json` contient exactement quatre corrections, chacune avec raison, certitude et changements élémentaires par fichier et JSON Pointer, valeurs avant/après et empreintes. Aucun HEX brut en majuscules n'a été trouvé : aucune normalisation supplémentaire. Les dérivés, chapitres, précision et ordre sont préservés.

## Provenance

Sanzo Wada, *A Dictionary of Color Combinations*, Seigensha, 2010, ISBN 978-4-86152-247-5. Transcription de Dain M. Blodorn Kim, corrections de Matt DesLauriers, licence MIT. Données **non vérifiées contre le livre papier**.

Source figée : dépôt `mattdesl/dictionary-of-colour-combinations`, commit `d44d2b5a18cf595aa536676a5cf67046a6b503f6`. SHA-256 du colors.json brut : `555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4`. Les empreintes du nettoyé sont dans le journal. Le brut et `manifest.json` restent inchangés ; ce manifeste décrit les anomalies du brut.

Toutes les copies proviennent exclusivement du script local `../sanzo-wada-space/sync_from_skill.py`, qui contrôle d'abord la source avec son vérificateur indépendant. Aucune régénération ni correction n'est effectuée dans le dataset.

## Schéma des couleurs

| Champ | Type | Portée |
|---|---|---|
| name | chaîne | Nom de la copie choisie |
| cmyk | quatre nombres | CMYK transcrit, ou corrigé pour Dull Violet Black dans le nettoyé |
| rgb | trois entiers | Valeurs source d'écran, 0 à 255 |
| hex | chaîne | Code d'écran source |
| lab | trois nombres | Lab D50 source, calculé par profils ICC |
| swatch | entier | Chapitre en base 0, de 0 à 5 |
| combinations | liste d'entiers | Numéros de 1 à 348 |
| name_source | chaîne optionnelle | Dans le nettoyé : nom source des trois couleurs renommées |
| cmyk_source | quatre nombres optionnels | Dans le nettoyé : CMYK brut de Dull Violet Black |
| derived_values_status | chaîne optionnelle | Dans le nettoyé : dérivés conservés depuis le CMYK brut erroné |

## Schéma des combinaisons

Objet racine : `_note` et liste `combinations`. Chaque entrée contient `id` (1 à 348), `size` (2 à 4), `colors` (noms), `hex` et `cmyk`. Les noms et CMYK reflètent la copie choisie. Le HEX de Dull Violet Black reste le dérivé brut ; consulter son statut dans le fichier de couleurs et le journal.

L'ordre interne des couleurs n'est pas enregistré comme une hiérarchie. Aucune proportion, intention, correspondance commerciale ou pertinence n'est attribuée aux combinaisons.

## Anomalies conservées dans le brut

Les constats suivants sont reproduits mot pour mot depuis le manifeste. Ils décrivent uniquement les fichiers bruts ; les différences du nettoyé sont expliquées plus haut.

### Dull Violet Black

CMYK [95, 106, 38, 50] : le magenta vaut 106, hors de l'intervalle 0-100. Valeur laissée telle quelle dans la source amont, non corrigée ici, à vérifier dans le livre papier. Les valeurs rgb, hex et lab de cette couleur en sont dérivées. Ne pas présenter ces valeurs comme sûres.

### Calamine BLue

Faute de frappe probable dans la source (« BLue » pour « Blue »). Nom conservé tel quel pour ne pas altérer le fichier amont ; citer le nom tel qu'il figure dans les données et signaler la faute probable si la question porte sur le nom.

### Cerulian Blue

Orthographe inhabituelle (« Cerulian » pour « Cerulean »). Peut venir du livre lui-même ou de la transcription : non tranché. Nom conservé tel quel ; citer le nom tel qu'il figure dans les données.

### Antwarp Blue

Orthographe inhabituelle (« Antwarp » pour « Antwerp »). Peut venir du livre lui-même ou de la transcription : non tranché. Nom conservé tel quel ; citer le nom tel qu'il figure dans les données.

## Lecture locale

```python
import json
from pathlib import Path
clean_colors = json.loads(Path("clean/colors.json").read_text(encoding="utf-8"))
raw_colors = json.loads(Path("colors.json").read_text(encoding="utf-8"))
journal = json.loads(Path("clean/cleaning.json").read_text(encoding="utf-8"))
```

Le YAML déclare quatre configurations distinctes. Dépôt public : `AUGERAUD/sanzo-wada-dictionary`. Le skill qui produit ces fichiers (scripts, tests, journal de nettoyage, règles pour agents IA) est publié sur GitHub dans le dépôt `sanzo-wada`, dossier `Sanzo-Wada/` ; l'aperçu visuel est la Space `AUGERAUD/sanzo-wada`.

## Licence et limites

MIT, voir `LICENSE.md`. Le HEX est une approximation d'écran. Une couleur d'écran ne remplace pas un échantillon physique. Aucune donnée ne provient d'un nuancier de peinture commercial. Corriger une borne ou une orthographe ne certifie pas une fidélité au livre.
