import subprocess
import shutil
from pathlib import Path
#todo nettoyer et corriger

TEX_FILE = "/home/drak-aris/PycharmProjects/Autogenarate_CER_Bot/template_latex/document.tex"
OUTPUT_DIR = "/home/drak-aris/PycharmProjects/Autogenarate_CER_Bot/sortie"

def compiler_latex(fichier_tex: str, dossier_sortie: str):
    fichier_tex = Path(fichier_tex).resolve()
    if not fichier_tex.exists():
        raise FileNotFoundError(f"Fichier introuvable : {fichier_tex}")
    if fichier_tex.suffix != ".tex":
        raise ValueError("L'extension du fichier doit être .tex")

    # Dossier de travail = dossier contenant le .tex
    dossier_travail = fichier_tex.parent
    nom_fichier = fichier_tex.name

    # Création du dossier de sortie si nécessaire
    dossier_sortie = Path(dossier_sortie).resolve()
    dossier_sortie.mkdir(parents=True, exist_ok=True)

    # Commande Docker : monter le dossier de travail et lancer pdflatex
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{dossier_travail}:/workdir",
        "-w", "/workdir",
        "aergus/latex",
        "pdflatex", "-interaction=nonstopmode", nom_fichier
    ]

    print(f"Compilation de {nom_fichier} avec l'image aergus/latex...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # Affiche la sortie pour diagnostiquer les erreurs LaTeX
        print("--- Sortie de pdflatex ---")
        print(result.stdout)
        print("--- Erreurs ---")
        print(result.stderr)
        raise RuntimeError("Échec de la compilation LaTeX. Voir les messages ci-dessus.")

    # Le PDF est produit dans le dossier de travail, on le déplace vers la sortie
    pdf_nom = fichier_tex.stem + ".pdf"
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