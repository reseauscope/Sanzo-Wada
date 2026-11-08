# Historique du skill Sanzo Wada

## 1.3.0, 2026-11-08 (Codex, choix arbitrés par Jean après relecture Claude)

- Changement de comportement : consultation de `data/clean/` par défaut ; `--data-source raw` pour le brut. Aucun repli implicite. Les anciens noms restent trouvables via `name_source`.
- Quatre corrections : Calamine Blue, Cerulean Blue, Antwerp Blue et CMYK [95, 100, 38, 50] pour Dull Violet Black. Cette dernière correction reste une hypothèse non vérifiée contre le livre papier.
- RGB, HEX et Lab de Dull Violet Black conservés sans recalcul. `cmyk_source` et `derived_values_status` explicitent la discordance. Cette couleur reste dans nearest et contrast, avec avertissement dans les sorties complètes et courtes.
- `build_clean.py`, journal à quatre corrections par JSON Pointer, empreintes et génération déterministe. `verify.py` reconstruit indépendamment couleurs, combinaisons et journal sans appeler le générateur.
- Aucun HEX brut en majuscules : aucune normalisation supplémentaire. Les données brutes et le manifeste sont intacts.
- Les 44 tests historiques sont adaptés au mode brut explicite et complétés par les tests du nettoyé, du nouveau défaut et les mutations des données et du journal.
- Livraison et archive uniquement locales. Aucun changement des copies Space/dataset ni publication dans ce lot.

## 1.2.1, 2026-11-08 (Codex, correctifs demandés par Jean)

- 2026-11-08 : outils annexes Space et dataset préparés dans les dossiers frères `sanzo-wada-space` et `sanzo-wada-dictionary` (Codex, relecture Claude), sans modification des données ni changement de version du skill ; publication après relecture et feu vert de Jean.

- `verify.py` : erreurs de lecture et d'encodage renvoyées sans trace Python, diagnostic des combinaisons mal structurées.
- Validation au chargement : RGB entiers et bornés, cohérence HEX, L*, chapitres, numéros sans booléens ni doublons, effectifs et tailles. Seule exception CMYK conservée : Dull Violet Black [95, 106, 38, 50], signalée par le manifeste ou l'avertissement global si celui-ci manque.
- `lookup color --brief` : avertissements intégraux sur les couleurs de chaque combinaison, même si la couleur interrogée est saine.
- Formulation harmonisée : CMYK du jeu de données transcrit d'après le livre, non vérifié contre le papier. Points d'entrée régénérés.
- Tests supplémentaires des commandes en sous-processus sur copies temporaires : arguments, codes de sortie, données invalides, fichiers absents ou illisibles, avertissements et régressions.
- Données et manifeste inchangés. Relecture indépendante à réaliser avant redistribution.

## 1.2.0, 2026-11-05 (Claude Fable 5.1, suite aux audits DeepSeek, Nemotron, Gemini, GLM et GPT-Astra du 05/11)

Colorimétrie
- `nearest` trie par CIEDE2000 (implémentation standard, testée sur des paires de référence) et donne le CIE76 pour comparaison.
- Un HEX exactement présent dans le dictionnaire est reconnu partout (`lookup nearest`, `suggest`, `contrast`) et passe en tête avec un écart nul.
- Asymétrie des deux chaînes Lab (entrée sRGB -> Lab D50 Bradford ; dictionnaire CMYK -> ICC) documentée dans le code, la sortie (`methode`) et `limites.md`.
- Repères d'interprétation du ΔE dans les règles.

Robustesse
- Validation complète de `colors.json` au chargement (types, valeurs finies, structure) et du manifeste ; `OSError` attrapée ; plus de trace Python.
- `verify.py` : empreinte SHA-256 obligatoire et bien formée, pas de numéro de combinaison répété par couleur, bornes de L*, numéros 1 à 348, six chapitres non vides, anomalies du manifeste rapportées à des couleurs existantes, première combinaison divergente nommée.
- Manifeste illisible : `avertissement_global` dans toute sortie de consultation (l'absence d'information ne vaut pas absence d'anomalie).
- `.gitattributes` (LF) et `tests/test_wada.py` (19 tests).

Commandes
- `lookup color` : `--brief`, `ambigu` (code 1) quand plusieurs noms partiels sans correspondance exacte, comme `suggest`.
- `lookup nearest` : `--n`, `dans_le_dictionnaire`, `correspondance_exacte`, `methode`.
- `lookup list` : CMYK, nombre de combinaisons et avertissements.
- `suggest` : `--max` par défaut 3, `ordre` explicite (ordre du livre, sans classement), `message` quand aucune combinaison de la taille demandée, signal d'écart important.
- `contrast` : accepte deux noms de couleurs ; `avertissement_methode` distinct de `avertissements`.
- Avertissement PowerShell sur les `#` nus.

Données et documentation
- `manifest.json` : commit amont et URL figée, édition de référence (Seigensha 2010, ISBN 978-4-86152-247-5), formulation de fidélité, registre étendu (Calamine BLue, Cerulian Blue, Antwarp Blue).
- `limites.md`, `histoire-wada.md`, `SOURCES.md` : formulation « CMYK du jeu de données, transcrit d'après le livre », dates de l'original non confirmées, références projet rendues génériques.
- `README.md` : installation native Codex et Antigravity, procédures de correction et de mise à jour, licence des scripts.
- Données inchangées (`colors.json` identique à l'amont, empreinte conservée).

Hors du skill : références au nom obsolète corrigées dans deux skills du projet hôte.

## 1.1.0, 2026-11-05 (Claude Fable 5.1, suite à l'audit DeepSeek du 04/11)

- `verify.py` compare `combinations.json` au rendu exact de `build_combinations.py` ; `nearest` utilise le `lab` source ; `delta_e` nommé CIE76 ; `--max` négatif refusé ; erreurs JSON lisibles ; LF forcé ; avertissements automatiques pour les anomalies du manifeste ; voisins masqués listés ; `chapitre_base0`.
- `AGENTS.md` du skill renommé `AGENTS-skill.md` ; règles sur les noms conservés tels quels et l'interdiction de retoucher `colors.json` ; `.gitignore`.
- Le projet hôte a décidé le 05/11 de faire de ce skill son guide graphique de référence ; cette décision est tracée côté projet.

## 1.0.0, 2026-11-04 (Claude Fable 5.1)

Création : données amont, scripts de recherche, suggestion, contraste et contrôle, trois points d'entrée générés depuis une source unique.
