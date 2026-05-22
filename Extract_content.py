import os
import json
from pathlib import Path
from docx import Document
import pdfplumber
from llama_cpp import Llama

script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir,"foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")

chemin_aller_prosit = "files_test/Prosit aller 1 algorithmique.docx" #fichiers test model

max_tokens = 2048
temperature = 0.1

def extraire_texte_docx(chemin_fichier: str) -> str:
    doc = Document(chemin_fichier)
    return "\n".join([p.text for p in doc.paragraphs])

def extraire_texte_pdf(chemin_fichier: str) -> str:
    texte_complet = []
    with pdfplumber.open(chemin_fichier) as pdf:
        for page in pdf.pages:
            texte_page = page.extract_text()
            if texte_page:
                texte_complet.append(texte_page)
    return "\n".join(texte_complet)

#TODO faire une etude du modele et des tokens et voir une amelioration possible sans influencer les performances pc
def extraire_sections_avec_llama(texte_brut: str, llm: Llama) -> dict: #TODO etude approfondie de cette partie
    prompt = f"""Tu es un assistant spécialisé dans l'analyse de documents structurés.
    Le texte ci-dessous est découpé en sections introduites par des titres (ex: "Mots clés", "Contexte", "Besoins", "Contraintes", Problématique, "Généralisation", etc.).
    Pour chaque titre, le contenu de la section est tout le texte qui suit le titre jusqu'au prochain titre ou jusqu'à la fin du document.

    Ta mission :
    1. Repère chaque section en utilisant les titres exacts comme ils sont écrits dans le texte.
    2. Extrais UNIQUEMENT le contenu qui appartient à cette section, sans inclure le titre lui-même ni le contenu des sections suivantes.
    3. Si une section n'a aucun contenu (titre suivi directement par un autre titre ou par rien), la valeur correspondante doit être une chaîne vide "".
    4. Retourne UNIQUEMENT un objet JSON valide avec les clés suivantes (dans cet ordre) et leur contenu textuel :
       - mot cles
       - contexte
       - besoins
       - contraintes
       - problematiques
       - generalisation
       - pistes de solution
       - plan action
    5. N'ajoute aucun commentaire avant ou après le JSON.

    Texte :
    {texte_brut}
    """
    messages = [{"role": "user", "content": prompt}]

    print("\n--- Début de la génération (streaming) ---")
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )

    full_text = ""
    for chunk in response:
        content = chunk['choices'][0]['delta'].get('content', '')
        if content:
            print(content, end='', flush=True)
            full_text += content
    print("\n--- Fin de la génération ---")

    reponse = full_text.strip()

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
    if not os.path.exists(chemin_aller_prosit):
        print(f"Erreur : le fichier '{chemin_aller_prosit}' n'existe pas.")
        return

    extension = Path(chemin_aller_prosit).suffix.lower()
    if extension == ".docx":
        texte = extraire_texte_docx(chemin_aller_prosit)
    elif extension == ".pdf":
        texte = extraire_texte_pdf(chemin_aller_prosit)
    else:
        print(f"Type non supporté : '{extension}'. Utilisez .docx ou .pdf.")
        return

    print("=== TEXTE BRUT EXTRAIT ===\n")
    print(texte)

    if not os.path.exists(model_path):
        print(f"\nErreur : le modèle GGUF '{model_path}' est introuvable. Téléchargez-le d'abord.")
        return

    # Chargement du modèle (rapide, ~2 Go RAM)
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            verbose=False
        )
        print("Modèle GGUF chargé avec succès.")
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        return

    print("\n=== EXTRACTION DES SECTIONS PAR LE MODÈLE LOCAL ===")
    sections = extraire_sections_avec_llama(texte, llm)

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