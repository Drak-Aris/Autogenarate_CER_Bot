import pdfplumber
import docx
from pathlib import Path

def extraire_texte_docx(chemin_fichier: str) -> str:
    doc = docx.Document(chemin_fichier)
    texte = ""
    for para in doc.paragraphs:
        texte += para.text + "\n"
    return texte

def extraire_texte_pdf(chemin_fichier: str) -> str:
    with pdfplumber.open(chemin_fichier)as pdf_file:
        texte = ""
        for page in pdf_file.pages:
            texte += page.extract_text() + "\n"
    return texte

if __name__ == "__main__":
    chemin_fichier = "files_test/Prosit aller 5 .docx"
    extension = Path(chemin_fichier).suffix.lower()

    if extension == ".docx":
        texte_extrait = extraire_texte_docx(chemin_fichier)
    elif extension == ".pdf":
        texte_extrait = extraire_texte_pdf(chemin_fichier)
    else:
        raise ValueError("Format de fichier non supporté. Utilisez .docx ou .pdf")

    print(texte_extrait)