import os
from pathlib import Path
from docx import Document
import pdfplumber
from Model_loading import charger_modele_et_tokenizer
import json

model_path = "Qwen2.5-7B-Instruct"#referencer le modele

chemin_aller_prosit = "Files_test/PROSIT ALLER N°01.docx"
max_tokens = 2048
temperature = 0.1


def extraire_texte_docx(chemin_fichier: str) -> str:
    doc = Document(chemin_fichier)
    texte_complet = []
    for paragraphe in doc.paragraphs:
        texte_complet.append(paragraphe.text)
    return "\n".join(texte_complet)


def extraire_texte_pdf(chemin_fichier: str) -> str:
    texte_complet = []
    with pdfplumber.open(chemin_fichier) as pdf:
        for page in pdf.pages:
            texte_page = page.extract_text()
            if texte_page:
                texte_complet.append(texte_page)
    return "\n".join(texte_complet)


def extraire_sections_avec_modele(texte_brut: str,charger , model, device) -> dict:
    prompt = f"""Tu es un assistant spécialisé dans l'analyse de documents.
À partir du texte suivant, extrais les informations correspondant aux sections listées ci-dessous.
Pour chaque section, restitue le contenu tel qu'il apparaît dans le texte, sans commentaire supplémentaire.
Si une section est absente, mets une chaîne vide.

Sections à extraire :
- titres_mot_cles
- contexte
- besoins
- contraintes
- problematiques
- generalisation
- pistes_de_solution
- plan_action

Retourne UNIQUEMENT un objet JSON valide avec ces clés et leurs contenus textuels.
Ne mets pas de texte autour du JSON.

Texte :
{texte_brut}
"""
    tokenizer, model, device = charger_modele_et_tokenizer(model_path)
    # Application du template de chat de Qwen
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer([text], return_tensors="pt").to(device)

    # Génération
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    # On enlève les tokens de la question
    output_ids = generated_ids[0][inputs['input_ids'].shape[1]:]
    reponse = tokenizer.decode(output_ids, skip_special_tokens=True).strip()

    # Nettoyage des éventuelles balises markdown ```json ... ```
    if reponse.startswith("```json"):
        reponse = reponse[7:]
    if reponse.endswith("```"):
        reponse = reponse[:-3]
    try:
        return json.loads(reponse.strip())
    except json.JSONDecodeError:
        print("Erreur : la réponse du modèle n'est pas un JSON valide.")
        print("Réponse brute :", reponse)
        return {}


def main():
    chemin = chemin_aller_prosit
    if not os.path.exists(chemin):
        print(f"Erreur : le fichier '{chemin}' n'existe pas.")
        return

    extension = Path(chemin).suffix.lower()
    if extension == ".docx":
        texte = extraire_texte_docx(chemin)
    elif extension == ".pdf":
        texte = extraire_texte_pdf(chemin)
    else:
        print(f"Type non supporté : '{extension}'. Utilisez .docx ou .pdf.")
        return

    print("=== TEXTE BRUT EXTRAIT ===\n")
    print(texte)

    if not os.path.exists(model_path):
        print(f"\nErreur : le dossier du modèle '{model_path}' est introuvable.")
        return

    # Chargement du modèle
    try:
        tokenizer, model, device = charger_modele_et_tokenizer(model_path)
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        return

    print("\n=== EXTRACTION DES SECTIONS PAR LE MODÈLE LOCAL ===")
    sections = extraire_sections_avec_modele(texte, tokenizer, model, device)

    if sections:
        print("\n=== SECTIONS EXTRAITES ===\n")
        for cle, valeur in sections.items():
            print(f"--- {cle} ---")
            print(valeur if valeur else "(vide)")
            print()
    else:
        print("Aucune section n'a pu être extraite.")


if __name__ == "__main__":
    main()