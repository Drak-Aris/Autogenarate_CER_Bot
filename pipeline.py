import os
from llama_cpp import Llama
from processing_aller.extract_content import extraire_sections_avec_llama
from processing_aller.web_research import extraire_sections_utiles, run_research_pipeline

#TODO Retirer les packages non utilises et utilisation de fast api pour communication avec le site web
chemin_aller_prosit = "files_test/Prosit aller 5 .docx" #TODO fichiers test model a retirer pour faire intervenir l'interface web, l'uploade de fichier

model_path = os.path.join(os.path.dirname(__file__), "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")

max_tokens = 2500
creativite = 0.1

coeurs_logiques = os.cpu_count() or 4  # 4 par défaut si la détection échoue
coeurs_physiques = max(1, coeurs_logiques // 2)

try:
    llm = Llama(
        model_path=model_path,
        n_ctx=8192,
        n_threads=coeurs_physiques,
        verbose=False
    )
    print("Modèle IA chargé avec succès.")
except Exception as e:
    print(f"Erreur lors du chargement du modèle : {e}")

if __name__ == "__main__":

    contenue_extrait = extraire_sections_avec_llama(chemin_aller_prosit, llm,max_tokens, creativite)

    if contenue_extrait is None:
        raise ValueError("L'extraction a échoué, document ERROR.")

    sections = extraire_sections_utiles(contenue_extrait)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle introuvable : {model_path}")


    print("...")
    print("Lancement du pipeline de recherche...")
    resultats_recherche = run_research_pipeline(sections, llm,  max_tokens, creativite)

"""
    # 3. Génération du document final à partir du plan détaillé
    plan_detail = resultats_recherche.get('plan_detail', {})

    if plan_detail:
        print("Début de la génération du plan d'action...")
        document_md = generer_document_final(plan_detail, sections, llm)
        with open("etude.md", "w", encoding="utf-8") as f:
            f.write(document_md)
        print("📝 Plan d'action generer")
    else:
        print("❌ Aucun plan détaillé trouvé, impossible de générer le document.")
"""