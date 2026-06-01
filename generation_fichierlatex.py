import os
import json
import re
from pathlib import Path

# --- CONFIGURATION ---
chemin_template = "template_latex/Themes/Theme_classique/retour_aller"
json_contenue = "json/resultat_extract.json"


def charger_json(chemin_json: str) -> dict:
    with open(chemin_json, 'r', encoding='utf-8') as f:
        texte = f.read()
    texte_nettoye = texte.replace('\\n', ' ')
    data = json.loads(texte_nettoye)
    return data


def remplacer_texte_section(contenu: str, cle: str, nouveau_texte: str) -> str:
    pattern = re.compile(
        r'(\\section\{[^}]*' + re.escape(cle) + r'[^}]*\}\s*)'
        r'(.*?)'
        r'(?=\\section|$)',
        re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(contenu)
    if match:
        avant = match.group(1)          # la ligne \section{...}
        # On remplace uniquement la partie texte, on garde la commande et on ajoute le nouveau texte
        remplacement = avant + "\n" + nouveau_texte.strip() + "\n"
        contenu = contenu[:match.start()] + remplacement + contenu[match.end():]
        return contenu
    else:
        # Aucune section trouvée : on lève une exception ou on retourne le contenu inchangé
        raise ValueError(f"Aucune \\section contenant '{cle}' trouvée dans le contenu.")


def traiter_fichier(chemin_fichier: str, cle: str, nouveau_texte: str):
    """Modifie le fichier LaTeX en remplaçant le texte sous la section correspondant à la clé."""
    chemin = Path(chemin_fichier)
    with open(chemin, 'r', encoding='utf-8') as f:
        contenu = f.read()

    try:
        contenu_modifie = remplacer_texte_section(contenu, cle, nouveau_texte)
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(contenu_modifie)
        print(f"✅ Clé '{cle}' : texte remplacé dans {chemin.name}")
    except ValueError as e:
        print(f"⚠️  {e} → Texte ajouté à la fin du fichier.")
        # Fallback : ajout à la fin
        with open(chemin, 'a', encoding='utf-8') as f:
            f.write("\n" + nouveau_texte.strip() + "\n")


def main():
    if not os.path.isfile(FICHIER_JSON):
        raise FileNotFoundError(f"Fichier JSON introuvable : {FICHIER_JSON}")

    donnees = charger_json(FICHIER_JSON)
    print(f"Clés trouvées dans le JSON : {list(donnees.keys())}")

    dossier = Path(DOSSIER_TEMPLATES)
    for cle, texte in donnees.items():
        nom_fichier = f"{cle}.tex"
        chemin_fichier = dossier / nom_fichier
        if not chemin_fichier.is_file():
            print(f"⚠️  Fichier introuvable pour la clé '{cle}' : {chemin_fichier}")
            continue
        traiter_fichier(str(chemin_fichier), cle, texte)

    print(f"\n✅ Tous les fichiers du dossier '{DOSSIER_TEMPLATES}' ont été mis à jour.")


if __name__ == "__main__":
    main()