import subprocess
import os
from pathlib import Path

def compile_latex_with_docker(tex_file_path, output_directory):
    """
    Compile un fichier .tex en utilisant une image Docker LaTeX.
    - tex_file_path : chemin absolu vers le fichier .tex (ex: "/home/.../monfichier.tex")
    - output_directory : dossier où sera placé le PDF (ex: "/home/.../output/")
    Retourne (succès: bool, message: str, chemin_pdf: str|None)
    """
    tex_file_path = Path(tex_file_path).resolve()
    output_dir = Path(output_directory).resolve()

    if not tex_file_path.exists():
        return False, f"Fichier .tex introuvable : {tex_file_path}", None

    # Créer le dossier de sortie s'il n'existe pas
    output_dir.mkdir(parents=True, exist_ok=True)

    # Commande Docker : on utilise latexmk pour gérer les multi-compilations
    # Montage : dossier source -> /workdir, dossier sortie -> /output
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{tex_file_path.parent}:/workdir",
        "-v", f"{output_dir}:/output",
        "texlive/texlive:latest",   # ou aergus/latex, selon votre image
        "latexmk", "-pdf", "-interaction=nonstopmode",
        f"/workdir/{tex_file_path.name}",
        f"-outdir=/output"
    ]

    # Exécution
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        pdf_file = output_dir / tex_file_path.with_suffix(".pdf").name
        if pdf_file.exists():
            return True, "Compilation réussie", str(pdf_file)
        else:
            return False, "Le PDF n'a pas été généré", None
    else:
        return False, f"Erreur LaTeX : {result.stderr}", None