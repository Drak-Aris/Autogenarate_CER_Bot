import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from llama_cpp import Llama
#TODO revoir serieusement le rtour sur au niveau des etudes approfondis mais si non les definition correct
# Chargement des variables d'environnement depuis .env
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not SERPER_API_KEY:
    raise ValueError("La clé SERPER_API_KEY est requise. Ajoutez-la dans un fichier .env : SERPER_API_KEY=votre_clé")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")
MAX_RESEARCH_RESULTS = 3
MAX_SYNTHESE_TOKENS = 512
TEMPERATURE = 0.1

search = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY, k=MAX_RESEARCH_RESULTS)


# ------------------------------
# 3. Fonction générique d'appel au LLM local
# ------------------------------
def llm_synthese(prompt: str, llm: Llama) -> str:
    """Envoie un prompt au modèle local et retourne la réponse nettoyée."""
    messages = [{"role": "user", "content": prompt}]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=MAX_SYNTHESE_TOKENS,
        temperature=TEMPERATURE,
        stream=False
    )
    return response['choices'][0]['message']['content'].strip()


# ------------------------------
# 4. Module : Définitions des mots clés
# ------------------------------
def rechercher_definitions(mots_cles: list, llm: Llama) -> dict:
    """
    Pour chaque mot clé, lance une recherche Google et synthétise une définition.
    Retourne un dict {mot_clé: définition}
    """
    definitions = {}
    for mot in mots_cles:
        print(f"🔍 Recherche définition pour : {mot}")
        # Étape 1 : recherche
        raw_results = search.run(f"définition {mot} algorithmique informatique")

        # Étape 2 : synthèse par le LLM
        prompt_synthese = f"""
À partir des résultats de recherche suivants, donne une définition claire et concise du terme "{mot}" dans le contexte de l'algorithmique.
Ne garde que la définition, sans commentaire.

Résultats de recherche :
{raw_results}
"""
        definition = llm_synthese(prompt_synthese, llm)
        definitions[mot] = definition
    return definitions


# ------------------------------
# 5. Module : Évaluation des pistes de solution
# ------------------------------
def rechercher_pistes_solutions(pistes: list, llm: Llama) -> list:
    """
    Pour chaque piste, cherche des informations sur sa faisabilité.
    Retourne une liste de dicts [{'piste': ..., 'plausible': bool, 'explication': ...}]
    """
    evaluations = []
    for piste in pistes:
        print(f"🔍 Évaluation de la piste : {piste}")
        raw_results = search.run(f"{piste} faisabilité algorithmique avantages inconvénients")

        prompt_eval = f"""
Tu es un expert en algorithmique. Analyse la piste de solution suivante : "{piste}".
En te basant sur les résultats de recherche ci-dessous, détermine si cette piste est plausible (oui/non) et explique pourquoi en 2-3 phrases.
Réponds UNIQUEMENT avec un JSON valide : {{"plausible": true/false, "explication": "..."}}

Résultats de recherche :
{raw_results}
"""
        reponse = llm_synthese(prompt_eval, llm)
        # Nettoyage éventuel de blocs de code JSON
        if reponse.startswith("```json"):
            reponse = reponse[7:]
        if reponse.endswith("```"):
            reponse = reponse[:-3]
        try:
            eval_json = json.loads(reponse)
            evaluations.append({
                "piste": piste,
                "plausible": eval_json["plausible"],
                "explication": eval_json["explication"]
            })
        except json.JSONDecodeError:
            evaluations.append({
                "piste": piste,
                "plausible": None,
                "explication": f"Erreur d'analyse : {reponse[:200]}"
            })
    return evaluations


# ------------------------------
# 6. Module : Approfondissement du plan d'action
# ------------------------------
def rechercher_plan_action(plan: list, llm: Llama) -> dict:
    """
    Pour chaque point du plan, effectue une recherche approfondie et synthétise le contenu.
    Retourne un dict {point: contenu_structuré}
    """
    plan_detail = {}
    for point in plan:
        print(f"🔍 Approfondissement du point : {point}")
        # Recherche avec une requête plus large
        raw_results = search.run(f"{point} algorithmique explications exemples")

        prompt_synthese = f"""
Tu es un assistant pédagogique. Rédige une section détaillée sur le sujet "{point}" en t'appuyant UNIQUEMENT sur les résultats de recherche ci-dessous.
Structure la réponse avec :
- Une définition/description
- Si pertinent, des sous‑points (ex. méthodes, cas d'usage)
- Des exemples simples
- Si possible, un petit tableau récapitulatif (format markdown accepté)
Sois complet mais concis.

Résultats de recherche :
{raw_results}
"""
        contenu = llm_synthese(prompt_synthese, llm)
        plan_detail[point] = contenu
    return plan_detail


# ------------------------------
# 7. Pipeline principal
# ------------------------------
def run_research_pipeline(sections: dict, llm: Llama) -> dict:
    """
    sections : dict issu de l'extraction précédente, contenant les clés :
        'mot cles', 'pistes de solution', 'plan action'
    Retourne un dictionnaire global avec les trois parties enrichies.
    """
    # Nettoyage des listes
    mots_cles = [m.strip() for m in sections.get('mot cles', '').split('\n') if m.strip()]
    pistes = [p.strip() for p in sections.get('pistes de solution', '').split('\n') if p.strip()]
    plan = [p.strip() for p in sections.get('plan action', '').split('\n') if p.strip()]

    resultats = {}

    if mots_cles:
        resultats['definitions'] = rechercher_definitions(mots_cles, llm)
    else:
        resultats['definitions'] = {}

    if pistes:
        resultats['pistes_evaluees'] = rechercher_pistes_solutions(pistes, llm)
    else:
        resultats['pistes_evaluees'] = []

    if plan:
        resultats['plan_detail'] = rechercher_plan_action(plan, llm)
    else:
        resultats['plan_detail'] = {}

    return resultats


# ------------------------------
# 8. Exemple d'intégration dans votre script existant
# ------------------------------
if __name__ == "__main__":
    # --- Reprise du code d'extraction (simulé ici) ---
    # Supposons que vous ayez déjà le dictionnaire 'sections' obtenu via extraire_sections_avec_llama()
    sections_exemple = {
        "mot cles": "complexité temporelle\ncomplexité spatiale\nnotation asymptotique",
        "pistes de solution": "utiliser des algorithmes de tri avancés\nparalléliser les calculs",
        "plan action": "Étudier la complexité temporelle\nÉtudier la complexité spatiale\nÉtudier les notations asymptotiques"
    }

    # Chargement du modèle
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")
    llm = Llama(model_path=MODEL_PATH, n_ctx=4096, n_threads=4, verbose=False)

    # Lancement du pipeline de recherche
    print("🚀 Lancement du pipeline de recherche...")
    resultats_recherche = run_research_pipeline(sections_exemple, llm)

    # Sauvegarde des résultats
    with open("recherche_resultats.json", "w", encoding="utf-8") as f:
        json.dump(resultats_recherche, f, ensure_ascii=False, indent=2)
    print("✅ Résultats sauvegardés dans recherche_resultats.json")

    # Affichage partiel
    print("\n--- Définitions ---")
    for mot, def_ in resultats_recherche.get('definitions', {}).items():
        print(f"{mot} : {def_[:150]}...")