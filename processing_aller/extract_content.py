import json
import re
from pathlib import Path
from docx import Document
import pdfplumber
from llama_cpp import Llama
import os


# TODO Implementer la logique sachant qu'on upload un fichier et plus un lien que l'on met

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


def extraire_sections_avec_llama(chemin_aller_prosit: str, llm: Llama, max_tokens, temperature) -> dict:
    extension = Path(chemin_aller_prosit).suffix.lower()
    if extension == ".docx":
        texte = extraire_texte_docx(chemin_aller_prosit)
    elif extension == ".pdf":
        texte = extraire_texte_pdf(chemin_aller_prosit)
    else:
        print(f"Type non supporté : '{extension}'. Utilisez un .docx ou .pdf.")
        return {}

    prompt = f"""Tu es un assistant spécialisé dans l'analyse de documents structurés.
    Le texte ci-dessous est découpé en sections introduites par des titres (ex: "Mots clés", "Contexte", "Besoins", "Contraintes", "Problématique", "Généralisation", etc.).
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
       **Important** : La section "plan action" ne doit PAS contenir la ligne "Définition des mots clés" (ou toute variante comme "Définir les mots clés", "Définition des termes"). Cette tâche est déjà couverte par la section "mot cles". Ne mets que les actions suivantes.
    5. N'ajoute aucun commentaire avant ou après le JSON.
    6. Pour les sections qui contiennent une liste d'éléments (comme des mots-clés, des besoins, des pistes de solution), écris chaque élément sur une ligne distincte dans la chaîne JSON.
    place chaque élément sur une ligne distincte. Dans une chaîne JSON, un saut de ligne s'écrit\\n(un seul antislash suivi de la lettre n).

    Texte :
    {texte}
    """

    messages = [{"role": "user", "content": prompt}]

    print("Début de l'extraction des informations du prosit aller...")
    response = llm.create_chat_completion(
        messages=messages, #TODO control warning
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
    print("\nFin de l'extraction des informations du prosit aller...")

    reponse = full_text.strip()

    if reponse.startswith("```json"):
        reponse = reponse[7:]
    if reponse.endswith("```"):
        reponse = reponse[:-3]

    try:
        sections = json.loads(reponse.strip())
    except json.JSONDecodeError:
        print("Erreur : la réponse du modèle n'est pas un JSON valide.")
        print("Réponse brute :", reponse)
        return {}

    champs_listes = ["mot cles", "besoins", "pistes de solution", "plan action", "contraintes", "problematiques"]

    for champ in champs_listes:
        if champ in sections and sections[champ]:
            contenu = sections[champ]
            if r"\n" not in contenu and "\n" not in contenu:
                contenu = re.sub(r"(\?+)\s*", r"\1\n", contenu)

                contenu = re.sub(r"[;；]+", "\n", contenu)
                contenu = re.sub(r"\s*[•·\-–—]\s*", "\n", contenu)

                contenu = re.sub(r"([a-zà-ÿ])\s+([A-ZÀ-Ÿ])", r"\1\n\2", contenu)

                contenu = re.sub(r"(?<!\d)(\d+)\.\s+", r"\n\1. ", contenu)

                contenu = re.sub(r"\n\s*\n+", "\n", contenu)
                contenu = re.sub(r" *\n *", "\n", contenu)
                contenu = contenu.strip()

                sections[champ] = contenu

    dossier_sortie = Path(os.path.dirname(__file__), "../json")
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    chemin_sortie = dossier_sortie / "resultat_extract.json"

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

    return sections