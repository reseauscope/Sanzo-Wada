"""Génère SKILL.md, AGENTS-skill.md et GEMINI.md à partir d'une source unique : references/regles-agent.md.

Usage : python build_entrypoints.py
Ne modifier que references/regles-agent.md, puis relancer ce script : les trois fichiers restent identiques.

Pourquoi AGENTS-skill.md et pas AGENTS.md : un projet peut imposer un AGENTS.md unique à sa racine.
Le skill ne doit pas entrer en conflit avec cette règle. Si le skill est utilisé seul dans un projet,
copier AGENTS-skill.md en AGENTS.md (voir README.md).
"""
import os
import sys

from wada import ROOT, utf8_stdout

DESCRIPTION = (
    "Palettes et harmonies de couleurs issues du dictionnaire de Sanzo Wada (348 combinaisons, 159 couleurs, "
    "copie nettoyée par défaut, brut consultable ; CMYK transcrit d'après le livre, non vérifié contre le papier). "
    "À utiliser pour proposer, rechercher ou vérifier des accords de couleurs "
    "(peinture, décoration, design) à partir d'une teinte ou d'un numéro de combinaison."
)

NOTE = ("<!-- Fichier généré par scripts/build_entrypoints.py à partir de references/regles-agent.md. "
        "Ne pas modifier à la main. -->\n\n")

CIBLES = {
    "SKILL.md": "---\nname: sanzo-wada\ndescription: " + DESCRIPTION + "\n---\n\n" + NOTE,
    "AGENTS-skill.md": NOTE,
    "GEMINI.md": NOTE,
}


def main():
    utf8_stdout()
    with open(os.path.join(ROOT, "references", "regles-agent.md"), encoding="utf-8") as f:
        corps = f.read()
    for nom, entete in CIBLES.items():
        with open(os.path.join(ROOT, nom), "w", encoding="utf-8", newline="\n") as f:
            f.write(entete + corps)
        print("écrit :", nom)
    obsolete = os.path.join(ROOT, "AGENTS.md")
    if os.path.exists(obsolete):
        print("ATTENTION : AGENTS.md existe encore dans le skill ; il n'est plus généré. Le supprimer "
              "ou le renommer pour respecter la règle du AGENTS.md unique du projet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
