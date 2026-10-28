from pathlib import Path
from docling.document_converter import DocumentConverter
import unicodedata, re

def extract_text(chemin_fichier: Path) -> str:
    converter = DocumentConverter()
    result = converter.convert(chemin_fichier)

    return result.document.export_to_markdown()

def normalize(text: str) -> str:
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"(?:^|(?<=\s))(?:\d+|[IVX]+)\.\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?:^|(?<=\s))\d+\.\s*", "", text)
    text = text.lower()
    return text.strip()

def aller_content (content:str) -> dict:
    sections = {k: [] for k in [
        "mots-cles", "contexte", "besoins", "problematique",
        "contraintes", "generalisation", "pistes de solution", "plan d'action"
    ]}

    current = None
    for line in content.splitlines():
        if not line.strip():
            continue

        if line.lstrip().startswith("#"):
            inside = line.replace("#", " ").strip()
            n = normalize(inside)

            match = next((k for k in sections if k in n), None)
            if match:
                current = match
            elif current:
                sections[current].append(inside)
            continue

        if current:
            sections[current].append(line.strip())

    sections = {k: "|| ".join(s.rstrip(",").strip() for s in v) for k, v in sections.items()}

    return sections


if __name__ == "__main__":
    '''
    lien = "../test_doc/Proist Aller.docx"
    texte_extrait = extract_text(lien)
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(texte_extrait)
    '''
    with open("test.txt", "r", encoding="utf-8") as f:
     test = f.read()
    sections = aller_content(test)
    print(sections["plan d'action"])