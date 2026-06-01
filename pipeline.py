import os
import json
from llama_cpp import Llama
from extract_content import extraire_sections_avec_llama
from web_research import extraire_sections_utiles, run_research_pipeline

chemin_aller_prosit = "files_test/PROSIT ALLER N°01.docx" #TODO fichiers test model a retirer pour faire intervenir l'interface web

model_path = os.path.join(os.path.dirname(__file__), "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")

max_token = 2500
creativite = 0.1

try:
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_threads=4,
        verbose=False
    )
    print("Modèle IA chargé avec succès.")
except Exception as e:
    print(f"Erreur lors du chargement du modèle : {e}")

if __name__ == "__main__":
    contenue_extrait = extraire_sections_avec_llama(chemin_aller_prosit, llm,max_token, creativite)

    if contenue_extrait is None:
        raise ValueError("L'extraction a échoué : mainExtraction() a retourné None.")

    sections = extraire_sections_utiles(contenue_extrait)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle introuvable : {model_path}")

    print("...")
    print("Lancement du pipeline de recherche...")
    resultats_recherche = run_research_pipeline(sections, llm)

    with open("recherche_resultats.json", "w", encoding="utf-8") as f: #TODO faire retirer
        json.dump(resultats_recherche, f, ensure_ascii=False, indent=2)
    print("✅ Fin du pipeline de recherche...")