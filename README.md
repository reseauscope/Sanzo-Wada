# Sanzo Wada : dictionnaire de combinaisons de couleurs pour agents IA

Outillage ouvert autour des 348 combinaisons de couleurs (159 couleurs, 2 à 4 couleurs par combinaison) du dictionnaire de Sanzo Wada (*A Dictionary of Color Combinations*, Seigensha, 2010, ISBN 978-4-86152-247-5), à partir du jeu de données MIT de Matt DesLauriers.

Trois dossiers, un seul contenu :

| Dossier | Rôle |
|---|---|
| [`Sanzo-Wada/`](Sanzo-Wada/) | Le **skill** : données brutes et copie nettoyée, scripts Python 3.8+ sans dépendance (recherche, suggestion, contraste, contrôle d'intégrité), tests, règles pour agents IA (`SKILL.md`, lu par Claude, Codex, Antigravity). |
| [`sanzo-wada-space/`](sanzo-wada-space/) | L'**aperçu visuel** : application Gradio publiée sur Hugging Face, Space [`AUGERAUD/sanzo-wada`](https://huggingface.co/spaces/AUGERAUD/sanzo-wada). |
| [`sanzo-wada-dictionary/`](sanzo-wada-dictionary/) | Le **dataset** : brut et nettoyé avec journal, publié sur Hugging Face, [`AUGERAUD/sanzo-wada-dictionary`](https://huggingface.co/datasets/AUGERAUD/sanzo-wada-dictionary). |

Ce dépôt est la source : les deux dossiers Hugging Face en sont des copies contrôlées par empreinte (`sanzo-wada-space/sync_from_skill.py`).

## Ce que les données valent

- Les valeurs CMYK viennent du jeu de données, transcrit d'après le livre, puis corrigé par un tiers. **Elles n'ont pas été vérifiées contre le livre papier.** Le HEX et le RGB sont des approximations d'écran.
- La copie nettoyée (`data/clean/`, lue par défaut) corrige trois fautes de nom (Calamine Blue, Cerulean Blue, Antwerp Blue) et ramène un magenta hors norme (106) à 100 pour Dull Violet Black. Chaque correction est journalisée dans `cleaning.json` avec sa raison et son degré de certitude ; celle de Dull Violet Black reste une hypothèse.
- Le brut (`data/colors.json`) est conservé octet pour octet, empreinte SHA-256 `555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4`, commit amont `d44d2b5a`.
- L'ordre des couleurs dans une combinaison n'est pas enregistré. Aucune ambiance, aucun usage, aucune correspondance avec un nuancier commercial.

## Démarrer

```
cd Sanzo-Wada
python3 scripts/verify.py
python3 -m unittest discover -s tests
python3 scripts/lookup.py color "Burnt Sienna" --brief
```

Détails dans [`Sanzo-Wada/README.md`](Sanzo-Wada/README.md).

## Licence

MIT. Données : Matt DesLauriers (`Sanzo-Wada/data/LICENSE.md`). Scripts, tests et documentation : voir [`LICENSE`](LICENSE).
