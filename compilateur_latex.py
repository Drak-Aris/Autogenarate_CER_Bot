import subprocess
import shutil
from pathlib import Path
#todo nettoyer et corriger
#TODO Corriger le faite que a la generation la table de matiere ne ressort pas.

TEX_FILE = "template/Theme_classique/main.tex"
OUTPUT_DIR = "cer_finished"

def compiler_latex(fichier_tex: str, dossier_sortie: str):
    fichier_tex = Path(fichier_tex).resolve()
    if not fichier_tex.exists():
        raise FileNotFoundError(f"Fichier introuvable : {fichier_tex}")
    if fichier_tex.suffix != ".tex":
        raise ValueError("L'extension du fichier doit être .tex")

    dossier_travail = fichier_tex.parent
    nom_fichier = fichier_tex.name

    dossier_sortie = Path(dossier_sortie).resolve()
    dossier_sortie.mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "-e", "LANG=C.UTF-8",            # sortie UTF-8
        "-v", f"{dossier_travail}:/workdir",
        "-w", "/workdir",
        "aergus/latex",
        "pdflatex", "-interaction=nonstopmode", nom_fichier
    ]

    print(f"Compilation de {nom_fichier} avec l'image aergus/latex...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'                # sécurité anti-octet bizarre
    )

    if result.returncode != 0:
        print("--- Sortie de pdflatex ---")
        print(result.stdout)
        print("--- Erreurs ---")
        print(result.stderr)
        raise RuntimeError("Échec de la compilation LaTeX.")

    # Le PDF est produit dans le dossier de travail, on le déplace vers la CER_finished
    pdf_nom = "CER.pdf"
    pdf_source = dossier_travail / pdf_nom
    pdf_dest = dossier_sortie / pdf_nom

    # Si la destination existe déjà, on la remplace
    if pdf_dest.exists():
        pdf_dest.unlink()

    shutil.move(str(pdf_source), str(pdf_dest))
    print(f"✅ PDF généré avec succès : {pdf_dest}")
    return pdf_dest


if __name__ == "__main__":
    try:
        compiler_latex(TEX_FILE, OUTPUT_DIR)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        exit(1)