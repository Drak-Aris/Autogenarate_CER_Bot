from pathlib import Path
from docling.document_converter import DocumentConverter

def extract_text(chemin_fichier: Path) -> str:
    converter = DocumentConverter()
    result = converter.convert(chemin_fichier)

    return result.document.export_to_markdown()

if __name__ == "__main__":
    lien = "../test_doc/Proist Aller.docx"
    texte_extrait = extract_text(lien)
    print(texte_extrait)