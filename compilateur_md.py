import pypandoc
from pathlib import Path

# Configuration des chemins
MD_FILE = "template/theme classique.md"
OUTPUT_DOCX = "cer_finished/cer_document.docx"


def convertir_markdown_en_docx_local(fichier_md: str, fichier_sortie: str):
    fichier_md = Path(fichier_md).resolve()
    fichier_sortie = Path(fichier_sortie).resolve()

    # Validations de base
    if not fichier_md.exists():
        raise FileNotFoundError(f"Fichier Markdown introuvable : {fichier_md}")
    if fichier_md.suffix not in [".md", ".markdown"]:
        raise ValueError("L'extension du fichier d'entrée doit être .md ou .markdown")
    if fichier_sortie.suffix != ".docx":
        raise ValueError("L'extension du fichier de sortie doit être .docx")

    # S'assurer que le dossier de sortie existe
    fichier_sortie.parent.mkdir(parents=True, exist_ok=True)

    print(f"🔄 Conversion locale de {fichier_md.name} en Word...")

    # Conversion directe (Pandoc est maintenant trouvé dans le PATH ou le binaire du package)
    pypandoc.convert_file(
        source_file=str(fichier_md),
        to='docx',
        outputfile=str(fichier_sortie)
    )

    print(f"✅ Document Word généré avec succès : {fichier_sortie}")
    return fichier_sortie


if __name__ == "__main__":
    try:
        convertir_markdown_en_docx_local(MD_FILE, OUTPUT_DOCX)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        exit(1)