import subprocess
import os
from pathlib import Path


def compile_tex_to_pdf(tex_path: str, output_dir: str) -> str:
    """
    Compile un fichier .tex en PDF via Docker (image texlive/texlive:latest).

    Args:
        tex_path (str): Chemin absolu ou relatif vers le fichier .tex
        output_dir (str): Dossier où sera sauvegardé le PDF généré

    Returns:
        str: Chemin absolu du PDF généré

    Raises:
        Exception: si la compilation échoue ou que le PDF n'est pas produit
    """
    tex_file = Path(tex_path).resolve()
    out_dir = Path(output_dir).resolve()

    if not tex_file.is_file():
        raise FileNotFoundError(f"Fichier .tex introuvable : {tex_file}")

    # Créer le dossier de sortie s'il n'existe pas
    out_dir.mkdir(parents=True, exist_ok=True)

    # Lancer la compilation via Docker
    # On monte :
    #   - le dossier contenant le .tex dans /workdir
    #   - le dossier de sortie dans /output
    # On utilise latexmk (gère les compilations multiples)
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{tex_file.parent}:/workdir",
        "-v", f"{out_dir}:/output",
        "texlive/texlive:latest",  # ou aergus/latex selon votre image
        "latexmk", "-pdf", "-interaction=nonstopmode",
        f"/workdir/{tex_file.name}",
        f"-outdir=/output"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erreur LaTeX : {result.stderr}")

    pdf_name = tex_file.stem + ".pdf"
    pdf_path = out_dir / pdf_name
    if not pdf_path.exists():
        raise RuntimeError("La compilation a réussi mais le PDF est introuvable")

    return str(pdf_path)


# --- Exemple d'utilisation dans votre projet PyCharm ---
if __name__ == "__main__":
    # Remplacez ces chemins par les vôtres
    mon_fichier_tex = "/home/drak-aris/PycharmProjects/AgentCERBot/mon_document.tex"
    mon_dossier_pdf = "/home/drak-aris/PycharmProjects/AgentCERBot/pdf_generes"

    try:
        pdf = compile_tex_to_pdf(mon_fichier_tex, mon_dossier_pdf)
        print(f"PDF généré avec succès : {pdf}")
    except Exception as e:
        print(f"Erreur : {e}")