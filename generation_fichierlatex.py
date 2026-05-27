import sys
import os
import re
from llama_cpp import Llama

# --- CONFIGURATION ---
MODEL_PATH = "/home/drak-aris/PycharmProjects/Autogenarate_CER_Bot/foundation_model_latex/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
OUTPUT_FILE = "template_latex/document.tex"
TEMPERATURE = 0.2
MAX_TOKENS = 2048

# --- PROMPT D'INITIALISATION ---
prompt_initial = (
    "Génère un document LaTeX complet qui présente les principaux paradigmes de l'algorithmique. "
    "Le document doit contenir :\n"
    "- Une page de titre avec le titre 'Paradigmes de l'Algorithmique'\n"
    "- Une introduction\n"
    "- Une section détaillée sur la programmation dynamique\n"
    "- Une section sur le paradigme diviser pour régner\n"
    "- Une conclusion\n"
    "Utilise les packages classiques (amsmath, graphicx, hyperref). "
    "Ne produis que le code LaTeX, sans aucun commentaire avant ou après. "
    "Commence directement par \\documentclass."
)

def extract_latex(text: str) -> str:
    """
    Nettoie la CER_finished du modèle pour ne garder que le code LaTeX.
    Supprime les éventuels délimiteurs ```latex ... ``` et le texte hors code.
    """
    # Supprime les blocs de code Markdown : ```latex ... ```
    pattern = r"```latex\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Si la CER_finished contient \documentclass, garde à partir de là
    start = text.find(r"\documentclass")
    if start != -1:
        text = text[start:]

    # Supprime tout ce qui suit \end{document}
    end = text.find(r"\end{document}")
    if end != -1:
        text = text[:end] + r"\end{document}"

    return text.strip()

def main():
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(f"Fichier modèle introuvable : {MODEL_PATH}")

    print("Chargement du modèle...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=4,
        verbose=False
    )
    print("Modèle chargé. Génération en cours...\n")

    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes LaTeX code."},
        {"role": "user", "content": prompt_initial}
    ]
    prompt_str = ""
    for msg in messages:
        prompt_str += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
    prompt_str += "<|im_start|>assistant\n"

    output = llm.create_completion(
        prompt=prompt_str,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        stop=["<|im_end|>", "<|im_start|>"],
        echo=False
    )

    raw_text = output['choices'][0]['text']
    latex_code = extract_latex(raw_text)

    if not latex_code:
        raise ValueError("Impossible d'extraire du code LaTeX valide de la réponse du modèle.")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(latex_code)

    print(f"✅ Fichier LaTeX nettoyé et sauvegardé : {OUTPUT_FILE}")
    print("--- Aperçu des premières lignes ---")
    print('\n'.join(latex_code.split('\n')[:15]))

if __name__ == "__main__":
    main()