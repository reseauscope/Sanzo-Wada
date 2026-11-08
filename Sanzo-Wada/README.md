# Skill Sanzo Wada

Accès pour agents IA (Claude, Codex, Gemini ou autre) aux 348 combinaisons de couleurs du dictionnaire de Sanzo Wada,
à partir du jeu de données ouvert de Matt DesLauriers (licence MIT). Un seul contenu, trois points d'entrée.
Le skill est **neutre** : aucune dépendance à un projet, aucune bibliothèque Python tierce.
Ce qu'il fournit : des accords de couleurs documentés et outillés. Ce qu'il ne fournit pas : une charte graphique complète
(rôles des couleurs, CTA, typographie, états), qui reste à définir par le projet qui l'utilise.

## Contenu

| Fichier | Rôle |
|---|---|
| `SKILL.md` | Point d'entrée pour Claude et pour la découverte native de Codex et Antigravity. **Généré**, ne pas modifier à la main. |
| `AGENTS-skill.md` | Même contenu, pour les agents qui lisent un `AGENTS.md` (voir « Installation »). **Généré**. |
| `GEMINI.md` | Même contenu, pour Gemini CLI. **Généré**. |
| `references/regles-agent.md` | **Source unique** des instructions ; les trois fichiers ci-dessus en sont générés par `scripts/build_entrypoints.py`. |
| `references/limites.md` | Ce qui est original, ce qui est calculé, méthode de comparaison, anomalies connues. |
| `references/histoire-wada.md` | Repères sur l'auteur et le livre. |
| `data/colors.json` | Les 159 couleurs, fichier amont copié tel quel. |
| `data/combinations.json` | Les 348 combinaisons, dérivées (LF, reproductible), pour consultation. |
| `data/manifest.json` | Provenance (commit, URL figée, édition), empreinte SHA-256, licence, registre des anomalies connues. |
| `data/clean/` | Copie lue par défaut : couleurs et combinaisons nettoyées, journal des quatre corrections et empreintes. |
| `data/SOURCES.md`, `data/LICENSE.md`, `data/UPSTREAM-README.md` | Chaîne de provenance, licence et README amont. |
| `scripts/` | Outils Python 3.8+ sans dépendance : `lookup`, `suggest`, `contrast`, `verify`, `build_combinations`, `build_entrypoints`. |
| `tests/test_wada.py`, `tests/test_commands.py`, `tests/test_clean.py` | Tests de non-régression, commandes, nettoyage et mutations (unittest). |
| `Application/` | Interface Windows locale (Tkinter, hors ligne) sur les mêmes scripts et données : lanceur `Sanzo-Wada.exe` (source `Lanceur.cs`, 5 Ko), `application.py`. Voir `Application/LISEZ-MOI.txt`. |
| `CHANGELOG.md` | Historique des versions du skill. |
| `../sanzo-wada-space/`, `../sanzo-wada-dictionary/` | Outils annexes, hors du skill : aperçu visuel Gradio et dataset préparé pour Hugging Face (dépôts publics Hugging Face `AUGERAUD/sanzo-wada` et `AUGERAUD/sanzo-wada-dictionary` ; code source sur GitHub, dépôt `sanzo-wada`). Copies contrôlées par `sync_from_skill.py`. |

## Prise en main

Version 1.3.0 : la copie nettoyée est lue par défaut. Les commandes `lookup.py`, `suggest.py` et `contrast.py` acceptent `--data-source raw` pour consulter la copie brute. Les anciens noms restent recherchables. Dull Violet Black reste calculable, avec avertissement sur ses dérivés conservés sans recalcul.

1. Contrôler les données : `py scripts/verify.py` (Windows) ou `python3 scripts/verify.py`. Code de sortie 0 attendu.
2. Lancer les tests : `py -m unittest discover -s tests`.
3. Essayer : `py scripts/lookup.py color "Burnt Sienna" --brief`. Sous PowerShell, mettre les HEX entre guillemets.
4. Après toute modification de `references/regles-agent.md` : `py scripts/build_entrypoints.py`.

## Installation par agent

Le dossier se copie tel quel. Le nom du skill est `sanzo-wada` (minuscules, celui du front matter de `SKILL.md`) : utiliser ce nom pour le dossier de destination.

- **Claude Code** : copier dans `.claude/skills/sanzo-wada/` (projet) ou `~/.claude/skills/sanzo-wada/`. `SKILL.md` est découvert automatiquement.
- **Codex** : découverte native par `SKILL.md` dans `.agents/skills/sanzo-wada/` (voie normale). Pour une tâche ponctuelle, fournir le chemin du dossier. `AGENTS-skill.md` est une solution complémentaire : ne jamais en faire un second `AGENTS.md` dans un projet qui en a déjà un ; y ajouter plutôt une ligne qui renvoie à `<chemin>/sanzo-wada/AGENTS-skill.md`. Si le skill est seul dans son projet, `AGENTS-skill.md` peut être copié en `AGENTS.md` à la racine.
- **Antigravity (Gemini)** : `.agents/skills/sanzo-wada/`, découverte par `SKILL.md`.
- **Gemini CLI** : copier `GEMINI.md` à la racine du projet, ou référencer le chemin du dossier.
- **Autre agent** : lui donner `references/regles-agent.md` et le chemin du dossier.

Les scripts se lancent depuis n'importe quel dossier ; l'agent doit pouvoir exécuter Python 3.8 ou plus.

## Copie nettoyée et corrections

`data/colors.json` et `data/manifest.json` restent intacts. `py -B scripts/build_clean.py` génère `data/clean/colors.json`, `data/clean/combinations.json` et `data/clean/cleaning.json`. Le journal comporte exactement quatre corrections avec différences élémentaires par JSON Pointer, raisons, certitude et empreintes. Aucun HEX du brut n'est en majuscules.

Les trois noms corrigés gardent leur `name_source`. Dull Violet Black porte `cmyk_source` et `derived_values_status` : CMYK corrigé par hypothèse, RGB/HEX/Lab source conservés sans recalcul, avertissement obligatoire. Voir `references/limites.md`.

Toute correction supplémentaire demande une décision explicite, une évolution du générateur et de la reconstruction indépendante de `verify.py`, puis tests et changelog. Ne pas retoucher les fichiers générés à la main. Lancer `py -B scripts/verify.py` pour contrôler brut, nettoyé et journal ensemble.

## Mettre à jour la source amont

Une mise à jour amont est un lot distinct, explicitement autorisé. La version 1.3.0 fige les empreintes source pour le nettoyage : ne pas remplacer le brut ou son manifeste dans ce lot. Toute future évolution doit revoir les corrections autorisées, les empreintes et la reconstruction, puis passer les tests. Aucun accès réseau n'est nécessaire pour utiliser ou régénérer les données présentes.

## Licence

Données : MIT (Matt DesLauriers, voir `data/LICENSE.md`). Scripts, tests et documentation de ce skill : MIT également, pour
permettre la réutilisation hors du projet d'origine.

## Limites

Voir `references/limites.md`. En résumé : le CMYK du jeu de données est la valeur de référence, le HEX est une approximation
d'écran, les anomalies de la source sont conservées dans le brut et quatre corrections sont journalisées dans le nettoyé. Un échantillonnage contre le livre papier reste à faire.
