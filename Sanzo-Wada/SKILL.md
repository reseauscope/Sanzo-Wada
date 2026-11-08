---
name: sanzo-wada
description: Palettes et harmonies de couleurs issues du dictionnaire de Sanzo Wada (348 combinaisons, 159 couleurs, copie nettoyée par défaut, brut consultable ; CMYK transcrit d'après le livre, non vérifié contre le papier). À utiliser pour proposer, rechercher ou vérifier des accords de couleurs (peinture, décoration, design) à partir d'une teinte ou d'un numéro de combinaison.
---

<!-- Fichier généré par scripts/build_entrypoints.py à partir de references/regles-agent.md. Ne pas modifier à la main. -->

# Sanzo Wada : combinaisons de couleurs

Ce dossier donne accès aux 348 combinaisons de couleurs (2 à 4 couleurs, 159 couleurs uniques) du dictionnaire de Sanzo Wada
(édition de référence : *A Dictionary of Color Combinations*, Seigensha, 2010, ISBN 978-4-86152-247-5 ; original japonais *Haishoku Sōkan*),
à travers le jeu de données ouvert de Matt DesLauriers (licence MIT). Valeur de référence : le CMYK du jeu de données, transcrit
d'après le livre, non vérifié contre le papier. Le skill est neutre : il ne dépend d'aucun projet.

## Quand l'utiliser

- Proposer, rechercher ou vérifier un accord de couleurs (peinture, décoration, design, web) à partir d'une teinte de départ.
- Retrouver une combinaison par son numéro (1 à 348) ou une couleur par son nom.
- Ne PAS l'utiliser pour retrouver des références de gammes commerciales (RAL, NCS, nuanciers de fabricants) : ce skill n'en contient aucune.
- Ce dictionnaire fournit des accords ; il ne constitue pas à lui seul une charte graphique (rôles des couleurs, CTA, états, typographie restent à définir par le projet qui l'utilise).

## Où sont les données

- Version 1.3.0 : `lookup`, `suggest`, `contrast` et `load_colors()` lisent **la copie nettoyée par défaut**. Ajouter `--data-source raw` aux commandes pour consulter le brut, ou `--data-source clean` explicitement. Aucun repli silencieux vers le brut si la copie nettoyée manque.
- `data/clean/colors.json`, `data/clean/combinations.json` : copie dérivée, quatre corrections décidées par Jean le 2026-11-08. Noms corrigés : Calamine Blue, Cerulean Blue, Antwerp Blue. Les anciens noms restent recherchables grâce à `name_source`. Le magenta de Dull Violet Black passe à 100 par hypothèse de borne non vérifiée contre le livre papier.
- `data/clean/cleaning.json` : quatre corrections sémantiques, avec les changements élémentaires par fichier et JSON Pointer, valeurs avant/après, raison, certitude et empreintes. Aucun HEX du brut en majuscules : aucune normalisation supplémentaire.
- `data/colors.json` : les 159 couleurs, fichier amont copié tel quel. Champs : `name`, `cmyk` (C/M/J/N de 0 à 100), `rgb`, `hex`, `lab` (D50), `swatch` (chapitre du livre, **base 0 : de 0 à 5 pour 6 chapitres**), `combinations` (numéros de 1 à 348).
- `data/combinations.json` : les 348 combinaisons, dérivées du fichier précédent par `scripts/build_combinations.py`. Fichier de consultation ; les scripts recalculent l'index depuis `colors.json`.
- `data/manifest.json` : provenance (commit amont, URL figée, édition du livre), empreinte SHA-256, licence et **registre des anomalies connues** (valeurs hors norme, fautes de nom probables).
- `data/SOURCES.md`, `references/limites.md` : chaîne de provenance, ce qui est original et ce qui est approximatif.

## Commandes (Python 3.8+, aucune dépendance, sortie JSON)

Sous Windows `py`, sous Linux ou macOS `python3`. Les scripts fonctionnent depuis n'importe quel dossier.
**Sous PowerShell, mettre les codes HEX entre guillemets** (`"#ae5224"`) : un `#` nu commence un commentaire.

- `scripts/lookup.py color "Burnt Sienna" [--brief]` : fiche d'une couleur et toutes ses combinaisons. `--brief` donne numéros et noms, avec les avertissements de chaque combinaison (sortie courte). Une correspondance exacte prime ; les noms voisins sont listés dans `autres_noms_contenant_la_requete`. Sans correspondance exacte et avec plusieurs noms partiels, la commande renvoie `ambigu` (code 1) : préciser le nom.
- `scripts/lookup.py combo 198` : les couleurs d'une combinaison.
- `scripts/lookup.py nearest "#ae5224" [--n 5]` : les couleurs du dictionnaire les plus proches d'un HEX (3 par défaut), triées par ΔE CIEDE2000 (CIE76 donné pour comparaison). Un HEX exactement présent dans le dictionnaire est reconnu (`dans_le_dictionnaire`, `correspondance_exacte`) et passe en tête avec un écart nul.
- `scripts/lookup.py list` : les 159 couleurs (nom, CMYK, HEX, chapitre, nombre de combinaisons).
- `scripts/suggest.py "Burnt Sienna" [--size 3] [--max 3]` : combinaisons contenant une couleur (nom ou HEX). Ordre du livre, sans classement de pertinence : ce script filtre, il ne recommande pas. `--max` vaut 3 par défaut.
- `scripts/contrast.py combo 198`, `scripts/contrast.py "#ae5224" "#f9c1ce"` ou `scripts/contrast.py "Burnt Sienna" "Hermosa Pink"` : rapports de contraste WCAG 2 (indicatif).
- `scripts/build_clean.py` : régénération locale déterministe de la copie nettoyée depuis le brut figé, sans modification du brut ni du manifeste. Ne pas éditer les fichiers nettoyés à la main.
- `scripts/verify.py` : contrôle du brut puis du nettoyé et du journal par reconstruction indépendante du générateur. Une copie manquante, partielle ou divergente échoue. À lancer avant tout usage si les fichiers ont pu changer. Sortie texte, code 0 si conforme.
- `tests/` : tests de non-régression, commandes et mutations (`python -m unittest discover -s tests`).

Codes de sortie : 0 résultat (y compris une recherche valide mais vide, signalée par `message`), 1 introuvable, ambigu ou données invalides, 2 usage incorrect. Les erreurs sont en JSON (`{"erreur": ...}`), sauf celles d'`argparse` et l'aide, qui sont en texte.

Les résultats portent `avertissements` quand une couleur du registre d'anomalies y figure, et `avertissement_global` si ce registre n'a pas pu être lu : dans les deux cas, reprendre le texte tel quel dans la réponse.

Dans la copie nettoyée, Dull Violet Black porte `derived_values_status=source_before_cmyk_correction` et `cmyk_source`. Ses RGB, HEX et Lab restent ceux du CMYK source erroné, sans recalcul ICC ; ce ne sont pas des conversions du CMYK corrigé. Il reste dans `nearest` et `contrast`, avec un avertissement explicite, même en mode `--brief` et même si le manifeste est indisponible. Ne pas présenter ces dérivés comme sûrs.

## Méthode de travail

1. Identifier la couleur de départ : nom du dictionnaire, ou HEX converti avec `nearest`.
2. Lister les combinaisons avec `suggest.py`, en filtrant par nombre de couleurs si la demande le précise.
3. Présenter 2 ou 3 combinaisons, jamais toutes d'un coup, avec leur numéro et le nom de chaque couleur.
4. Rappeler les limites utiles à la demande (voir règles).

## Règles impératives

1. Citer toujours le numéro de combinaison et le nom des couleurs, par exemple « combinaison n° 198 ».
2. Donner le CMYK quand on donne un HEX, et préciser que le HEX est une approximation d'écran des couleurs imprimées.
3. Ne rien inventer : aucune citation de Wada, aucune signification, ambiance ou règle d'usage attribuée à Wada. Le livre présente des combinaisons sans explication. Toute interprétation (ambiance, pièce, usage) est une suggestion de l'agent et doit être étiquetée comme telle.
4. L'ordre des couleurs dans une combinaison n'est pas enregistré. Ne jamais affirmer qu'une couleur est dominante, secondaire ou d'accent d'après les données.
5. `nearest` renvoie la couleur la plus proche, pas une couleur identique (sauf `correspondance_exacte`). Indiquer l'écart ΔE. Repère d'interprétation : ΔE00 autour de 1 à peine perceptible, 2 à 5 perceptible côte à côte, au-delà de 5 nettement différent.
6. Pour une peinture réelle, une couleur d'écran ne remplace pas un échantillon physique : recommander de tester sur le support.
7. Le contraste WCAG est indicatif : les combinaisons ne sont pas conçues pour la lisibilité de texte, et le résultat ne vaut que pour les deux valeurs numériques comparées.
8. Citer les noms de la copie consultée : noms corrigés dans le nettoyé, orthographes originales dans le brut. `name_source` conserve les trois anciens noms et permet leur recherche. Le registre du manifeste décrit seulement le brut ; ne pas présenter une faute corrigée comme encore présente dans le nettoyé.
9. Reprendre tel quel tout `avertissements` ou `avertissement_global` renvoyé par les scripts (par exemple « Dull Violet Black », dont le CMYK est hors norme dans la source).
10. Répondre dans la langue de l'utilisateur. Les noms de couleurs restent en anglais, comme dans le livre ; on peut ajouter une traduction entre parenthèses.
11. Ne modifier ni `data/colors.json` ni `data/manifest.json`. Les corrections autorisées sont des dérivés dans `data/clean/`, entièrement journalisés et vérifiés. Toute correction supplémentaire demande une nouvelle décision explicite, jamais une retouche silencieuse.
12. Les scripts filtrent et calculent ; ils ne classent pas les accords par pertinence. Toute préférence exprimée pour un accord est un choix de l'agent ou de l'utilisateur, à dire comme tel.
