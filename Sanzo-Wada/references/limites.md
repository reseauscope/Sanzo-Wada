# Limites et niveau de fiabilité

## Copie nettoyée 1.3.0, lue par défaut

Depuis la version 1.3.0, les commandes de consultation lisent `data/clean/` par défaut. L'option `--data-source raw` retrouve le brut. Ce changement de comportement est décidé par Jean ; le brut et son manifeste restent inchangés. Une copie nettoyée manquante fait échouer la commande, sans repli silencieux.

Quatre corrections seulement : Calamine BLue devient Calamine Blue, Cerulian Blue devient Cerulean Blue, Antwarp Blue devient Antwerp Blue ; le magenta de Dull Violet Black passe de 106 à 100. Les noms source sont conservés dans `name_source`. Corriger le magenta est une hypothèse de borne, pas une transcription vérifiée du livre.

**Aucun recalcul des dérivés de Dull Violet Black.** RGB, HEX et Lab restent exactement ceux de la source, calculés depuis [95, 106, 38, 50]. `cmyk_source` et `derived_values_status=source_before_cmyk_correction` signalent qu'ils ne correspondent pas à une conversion du nouveau CMYK [95, 100, 38, 50]. Une nouvelle chaîne différente de la chaîne ICC amont créerait une autre incohérence. Ces dérivés restent douteux ; conserver leur avertissement.

Dull Violet Black reste dans tous les résultats, notamment `nearest` et `contrast`, comme décidé par Jean. Les calculs utilisent ses dérivés source inchangés et portent l'avertissement de statut, y compris en mode court ou si le manifeste est illisible. Leur disponibilité ne certifie pas leur exactitude physique.

Le registre du manifeste continue de décrire le brut. `cleaning.json` décrit le nettoyé : quatre corrections, avec chaque différence élémentaire par JSON Pointer et empreintes. `verify.py` reconstruit indépendamment les résultats attendus et le journal, sans appeler `build_clean.py`. Effectifs, appartenances, ordre, valeurs non corrigées et métadonnées doivent être identiques à la reconstruction. Aucun HEX en majuscules dans le brut ; aucun arrondi Lab, tri de listes, nouvel identifiant ou changement de chapitre.

## Ce qui est le plus proche du livre

- Les noms des couleurs, leurs valeurs CMYK, leur chapitre et leur appartenance aux 348 combinaisons.
  Ce sont les données transcrites d'après le livre par Dain M. Blodorn Kim, corrigées ensuite par Matt DesLauriers.
  Elles n'ont pas été comparées au livre papier dans ce skill : « CMYK du jeu de données, transcrit d'après le livre »
  est la formulation exacte, pas « CMYK d'origine ».

## Ce qui est calculé

- `rgb`, `hex`, `lab` : conversion depuis le CMYK avec les profils ICC U.S. Web Coated (SWOP) v2 et sRGB IEC61966-2.1
  (relatif colorimétrique, compensation du point noir, Lab en D50). Le dépôt amont précise lui-même que des écarts
  avec les couleurs imprimées du livre peuvent subsister.

## Comment `nearest` compare les couleurs

- La couleur saisie (HEX) est convertie par les scripts : sRGB -> linéaire -> XYZ(D50) -> Lab(D50), avec une matrice
  sRGB -> XYZ déjà adaptée de D65 vers D50 par la transformation de Bradford (coefficients de Lindbloom ; blanc de
  référence arrondi à 0,9642 / 1,0 / 0,8249, l'écart avec les valeurs ICC exactes est de l'ordre du centième de ΔE).
- Les couleurs du dictionnaire utilisent leur `lab` source (chaîne ICC depuis le CMYK).
- **Les deux chaînes ne sont pas identiques.** Un HEX pris dans le dictionnaire et recomparé à sa propre couleur donne
  un écart non nul, de l'ordre de ΔE 0,1 à 0,3 en général, et bien plus sur les teintes saturées hors gamut sRGB
  (Benzol Green, Peacock Blue, Dusky Green, Antwarp Blue : écart de 10 à 18 entre les deux chaînes). Pour cette raison,
  un HEX exactement présent dans le dictionnaire est détecté avant tout calcul et passe en tête avec un écart de 0.
- Le tri se fait en **CIEDE2000** (implémentation standard, contrôlée dans `tests/` sur des paires de référence publiées) ;
  le **CIE76** (distance euclidienne) est donné pour comparaison. Repères d'interprétation (ΔE00) : autour de 1, à peine
  perceptible ; 2 à 5, perceptible côte à côte ; au-delà de 5, nettement différent.

## Ce que les données ne contiennent pas

- L'ordre des couleurs au sein d'une combinaison.
- Les proportions, les usages ou les intentions de Wada.
- Les motifs et compositions illustrant chaque planche du livre.
- Toute correspondance avec une gamme de peinture commerciale.
- Tout classement de pertinence : `suggest.py` renvoie les combinaisons dans l'ordre du livre.

## Écarts connus dans les données brutes amont (conservées volontairement)

Le fichier `colors.json` est conservé identique à sa source pour que l'empreinte du manifeste reste vérifiable.
Le registre complet est dans `data/manifest.json` (`anomalies_connues`) ; les scripts le lisent et joignent un
avertissement à tout résultat où ces couleurs figurent. Résumé :

- **Dull Violet Black** : CMYK `[95, 106, 38, 50]`, le magenta (106) dépasse 100. Les valeurs `rgb`, `hex` et `lab`
  en sont dérivées. Combinaisons 95, 106, 145, 265, 277, 289, 295 et 331. À vérifier dans le livre papier.
- **« Calamine BLue »** : faute de frappe probable (majuscule), présente telle quelle dans `colors.json` (corrigée dans un
  dépôt dérivé tiers, pas dans la source utilisée ici). La recherche par nom est insensible à la casse.
- **« Cerulian Blue »**, **« Antwarp Blue »** : orthographes inhabituelles (Cerulean, Antwerp). Livre ou transcription, non tranché.
- **`swatch`** : chapitre du livre en base 0 (valeurs 0 à 5 pour 6 chapitres). Les scripts l'exposent sous `chapitre_base0`.

Le balayage des noms n'a pas été exhaustif : d'autres orthographes anciennes ou fautes peuvent exister.

## Affirmations tierces à ne pas reprendre

Une étude externe sur Wada, évaluée avant la création de ce skill, contenait des faits inexacts (dont une attribution
de « premier film en couleurs » et un nombre de combinaisons erroné). Ne reprendre sur Wada que ce que les données de ce
skill ou une source primaire confirment.

## Points à vérifier avant un usage professionnel

1. Comparer un échantillon d'une vingtaine de couleurs (CMYK et noms) avec le livre papier ou une seconde source indépendante.
   C'est le seul échelon de fiabilité non atteint.
2. Les dates de l'édition originale (1933-1934 selon le README amont ; d'autres sources mentionnent 1918) ne sont pas
   confirmées sur source primaire. Seule l'édition Seigensha de 2010 (ISBN 978-4-86152-247-5) est identifiée avec certitude.

## Ce qui n'est pas de Wada

Tout classement par ambiance, par pièce ou par style, les aperçus de sites web et les exports Tailwind trouvés sur des sites tiers
sont des ajouts modernes. Ils ne font pas partie des données de ce skill.
