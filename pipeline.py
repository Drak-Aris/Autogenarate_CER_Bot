from pathlib import Path
from processing_aller.extract_content import ()
import re


if __name__ == "__main__":
    chemin_fichier = Path("test_doc").resolve()/"Proist Aller.docx"
    prosit_aller = extract_content_aller(chemin_fichier)

    print(prosit_aller)