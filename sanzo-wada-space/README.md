---
title: Sanzo Wada, 348 combinaisons
emoji: 🎨
colorFrom: gray
colorTo: gray
sdk: static
app_file: index.html
license: mit
---

# Sanzo Wada : copie nettoyée 1.3.0

159 couleurs, 348 combinaisons. Quatre vues : combinaison par numéro, couleur par nom, trois voisins d'un HEX, grille filtrable par taille et chapitre. Les aplats ont la même largeur, les combinaisons suivent l'ordre du livre, sans classement de pertinence. Le filtre chapitre retient les combinaisons contenant au moins une couleur du chapitre choisi. Les liens des quatre vues se replient sur mobile et restent accessibles au clavier.

## Copie consultée et corrections

L'application lit explicitement `data/clean/colors.json`, avec une colorimétrie JavaScript comparée au module `wada.py` 1.3.0 copié sans changement. Elle ne lit jamais directement le dossier du skill. Les fichiers bruts embarqués servent à la provenance et aux contrôles de synchronisation.

| Nom brut | Nom affiché |
|---|---|
| Calamine BLue | Calamine Blue |
| Cerulian Blue | Cerulean Blue |
| Antwarp Blue | Antwerp Blue |

Le champ `name_source` est affiché sous le nom corrigé, sur les aplats. Les anciens noms restent reconnus par la recherche du module.

Dull Violet Black : le CMYK passe de [95, 106, 38, 50] à [95, 100, 38, 50], par hypothèse de borne non vérifiée contre le livre papier. Ses RGB, HEX et Lab restent ceux du CMYK source erroné, sans recalcul. `cmyk_source` et `derived_values_status=source_before_cmyk_correction` signalent cette discordance. L'avertissement du module est intégralement visible dans chaque résultat concerné. Cette couleur reste présente dans les calculs de proximité, sans exclusion.

Le registre `data/manifest.json` décrit le brut. Ne pas présenter son ancien constat « CMYK 106 non corrigé » comme décrivant le nettoyé. La copie nettoyée et ses quatre corrections sont décrites dans `data/clean/cleaning.json`.

## Provenance et limites

Valeurs CMYK du jeu de données de Matt DesLauriers (MIT), transcrites d'après le livre, non vérifiées contre le papier. Le HEX est une approximation d'écran. Aucune donnée de cette page ne vient d'un nuancier de peinture commercial.

Référence : Sanzo Wada, *A Dictionary of Color Combinations*, Seigensha, 2010, ISBN 978-4-86152-247-5. Transcription de Dain M. Blodorn Kim, corrections de Matt DesLauriers. Aucune comparaison au livre papier n'a été réalisée.

Commit amont : `d44d2b5a18cf595aa536676a5cf67046a6b503f6`. Empreinte SHA-256 du colors.json brut : `555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4`. Empreintes du nettoyé dans le journal, et de toutes les copies dans `sync-receipt.json`.

La proximité emploie CIEDE2000 et fournit CIE76 pour comparaison. Le HEX saisi suit une conversion sRGB vers Lab D50 Bradford ; les valeurs Lab du dictionnaire viennent de la chaîne ICC du CMYK source. Leurs écarts peuvent être importants hors gamut sRGB. Le code HEX exact reçoit un écart nul par convention ; cela ne certifie aucune identité physique avec le livre imprimé.

## Fichiers embarqués

- `data/colors.json`, `data/combinations.json`, `data/manifest.json`, `data/LICENSE.md` : brut et provenance inchangés.
- `data/clean/colors.json`, `data/clean/combinations.json`, `data/clean/cleaning.json` : nettoyé et journal copiés sans régénération.
- `wada.py` : module du skill, identique octet pour octet. Il sert de référence aux vecteurs de test Python ; il ne s’exécute pas dans le navigateur.
- `sync-receipt.json` : date, version source, commit amont et empreintes des copies Space et dataset.

## Synchronisation locale

Depuis le dossier de la Space, dans l'arborescence du projet :

```powershell
py -B sync_from_skill.py --check
```

La source est contrôlée par son `verify.py` avant toute copie, avec `-B` pour ne rien écrire dans le skill. Les 15 copies sont comparées octet pour octet. Le mode `--check` ne modifie aucun fichier, y compris le reçu.

Pour la première copie dans des dossiers neufs : `py -B sync_from_skill.py`. Pour migrer explicitement une ancienne copie validée : `py -B sync_from_skill.py --upgrade`. Cette dernière option ne remplace une copie différente que si son empreinte correspond encore au reçu précédent. Une copie altérée est refusée avant toute écriture ; les empreintes attendue et lue sont affichées. Les fichiers source restent intacts.

Les options `--skill-dir` et `--dataset-dir` fixent les chemins locaux. Le dataset reçoit le brut à la racine et le nettoyé sous `clean/`.

## Lancement

Ouvrir `index.html` directement dans un navigateur récent, ou servir ce dossier avec `python -m http.server`. Aucun serveur applicatif, dépendance, CDN, police web ni requête sortante.

`sync_from_skill.py` génère aussi `snapshot.js`, contenant les octets exacts des huit fichiers embarqués, encodés en base64, et le reçu. Le navigateur vérifie leurs SHA-256 par Web Crypto avant d'afficher les données. Les JSON affichés sont décodés uniquement depuis ces octets vérifiés. Ce choix permet `file://` sans les restrictions de `fetch`. Le mode `--check` vérifie aussi ce fichier généré. Le reçu assure la cohérence locale, pas une signature indépendante contre un remplacement simultané de toutes les données et du reçu.

La vérification échouée masque toute l'application et laisse seulement un message d'erreur. Si Web Crypto est indisponible, un message demande un navigateur récent et un contexte fichier local ou HTTPS.

Tests sans dépendance : `python -B tests/make_vectors.py`, `node tests/test_color.js`, `node tests/test_snapshot.js`. Les vecteurs couvrent les 159 HEX du dictionnaire et 22 entrées supplémentaires, trois voisins et deux écarts par entrée. Les avertissements sont comparés mot pour mot au module Python. Après un changement du module, régénérer aussi `texts.js` depuis ses avertissements avant revue.

Les données sont sous licence MIT, copie dans `data/LICENSE.md`. Les fichiers de l'application sont également proposés sous licence MIT. Dépôts publics : Space `AUGERAUD/sanzo-wada`, dataset `AUGERAUD/sanzo-wada-dictionary`, code source sur GitHub (dépôt `reseauscope/Sanzo-Wada`, https://github.com/reseauscope/Sanzo-Wada : dossier `Sanzo-Wada/` pour le skill, `sanzo-wada-space/` pour cette application).
