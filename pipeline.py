from pathlib import Path
from processing_aller.extract_content import ()
import re

def extract_content_aller(lien: Path) -> dict:
    extension = Path(lien).suffix.lower()

    if extension == ".docx":
        texte_extrait = extraire_texte_docx(lien)
    elif extension == ".pdf":
        texte_extrait = extraire_texte_pdf(lien)
    else:
        raise ValueError("Format de fichier non supporté. Utilisez .docx ou .pdf")

    resultat = {
        "mots-cles": [],
        "contexte": [],
        "besoins": [],
        "problematique": [],
        "contraintes": [],
        "generalisation": [],
        "pistes de solution": [],
        "plan d'action": []
    }

    section_actuelle = None

    for ligne in texte_extrait.splitlines():
        ligne_brute = ligne.strip()
        if not ligne_brute:
            continue

        ligne_net = normaliser(ligne_brute)
        section_trouvee = detecter_section(ligne_net)

        if section_trouvee:
            section_actuelle = section_trouvee
        elif section_actuelle:
            if re.match(r'^[0-9]+\.\s+', ligne_brute) and detecter_section(
                    normaliser(re.sub(r'^[0-9]+\.\s+', '', ligne_brute))):
                continue
            resultat[section_actuelle].append(ligne_brute)

    mots_cles_bruts = " ".join(resultat["mots-cles"])
    mots_separes = re.split(r',|\n', mots_cles_bruts)
    resultat["mots-cles"] = [mc.strip(" .") for mc in mots_separes if mc.strip(" .")]

    return resultat

if __name__ == "__main__":
    chemin_fichier = Path("test_doc").resolve()/"Proist Aller.docx"
    prosit_aller = extract_content_aller(chemin_fichier)

    print(prosit_aller)