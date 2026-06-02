import os
import json
from pathlib import Path

#TODO Revoir et corriger le code
#TODO modulariser max le latex

# --- CONFIGURATION ---
chemin_template = "template_latex/Themes/Theme_classique/retour_aller"
json_contenue = "json/resultat_extract.json"

# Clés à ignorer
key_ignore = {"mots cles"}


def charger_json(chemin_json: str) -> dict:
    """Charge le fichier JSON sans modification."""
    with open(chemin_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def formater_contenu(texte: str) -> str:
    """
    Retourne le contenu formaté pour LaTeX :
    - Si le texte contient '\\n', on génère un environnement itemize.
    - Sinon, on retourne le texte brut.
    """
    if '\\n' in texte:
        items = [item.strip() for item in texte.split('\\n') if item.strip()]
        if not items:
            return texte
        latex_items = '\n'.join([f'    \\item {item}' for item in items])
        return '\\begin{itemize}\n' + latex_items + '\n\\end{itemize}'
    return texte


def ecrire_fichier_cle(dossier: Path, cle: str, contenu: str):
    """Écrit le contenu dans le fichier <clé>.tex du dossier (écrasement total)."""
    chemin_fichier = dossier / f"{cle}.tex"
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"✅ Fichier '{cle}.tex' mis à jour.")


def main():
    if not os.path.isfile(json_contenue):
        raise FileNotFoundError(f"Fichier JSON introuvable : {json_contenue}")

    donnees = charger_json(json_contenue)
    print(f"Clés trouvées dans le JSON : {list(donnees.keys())}")

    dossier = Path(chemin_template)
    # Créer le dossier si nécessaire
    dossier.mkdir(parents=True, exist_ok=True)

    for cle, texte in donnees.items():
        if cle in key_ignore:
            print(f"⏭️  Clé ignorée : '{cle}'")
            continue

        if not isinstance(texte, str):
            print(f"⚠️  La valeur pour la clé '{cle}' n'est pas une chaîne, ignorée.")
            continue

        # Formater le contenu selon la présence ou non de \\n
        contenu_formate = formater_contenu(texte)
        ecrire_fichier_cle(dossier, cle, contenu_formate)

    print(f"\n✅ Tous les fichiers du dossier '{chemin_template}' ont été régénérés.")


if __name__ == "__main__":
    main()