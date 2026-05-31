import os
import json
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from llama_cpp import Llama
load_dotenv()
import requests
from extract_content import extraire_sections_avec_llama

chemin_aller_prosit = "files_test/PROSIT ALLER N°01.docx" #TODO fichiers test model a retirer pour faire intervenir l'interface web


def extraire_sections_utiles(data: dict) -> dict:
    cles_requises = ["mot cles", "pistes de solution", "plan action", "generalisation"]
    return {cle: data[cle] for cle in cles_requises if cle in data}

def check_serper_remote_access() -> bool:
    try:
        resp = requests.get(os.getenv("serper_flag_url"), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        access = data.get("access", False)  # valeur par défaut sécurisée
        # Normalisation : si c'est une chaîne, on convertit
        if isinstance(access, str):
            return access.lower() == "true"
        return bool(access)
    except Exception as e:
        print(f"⚠️ Probleme lors de la connexion serper {e}")
        print("Par mesure de sécurité, l'accès à Serper est bloqué.")
        return False


if not check_serper_remote_access():
    raise RuntimeError(
        "🔒 L'accès à Serper est actuellement désactivé par l'administrateur. "
        "Pour le réactiver, contacter et supplier l'administrateur. "
    )


#TODO revoir serieusement le rtour sur au niveau des etudes approfondis mais si non les definition correct


serper_api = os.getenv("serper_api_key")
if not serper_api:
    raise ValueError("La clé API de serper rencontre un probleme.")

model_path = os.path.join(os.path.dirname(__file__), "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")

max_result = 7
max_token = 2500
creativite = 0.1

search = GoogleSerperAPIWrapper(serper_api_key=serper_api, k=max_result)


def llm_synthese(prompt: str, llm: Llama) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_token,
        temperature=creativite,
        stream=False
    )
    return response['choices'][0]['message']['content'].strip()


def rechercher_definitions(mots_cles: list, llm: Llama, generalisation) -> dict:
    definitions = {}
    for mot in mots_cles:
        print(f"🔍 Recherche définition pour : {mot}")
        raw_results = search.run(f"définition {mot}: ")

        prompt_synthese = f"""
À partir des résultats de recherche suivants, donne une définition claire et concise du terme "{mot}" dans le contexte suivant: {generalisation}.
Ne garde que la définition, sans commentaire.

Résultats de recherche :
{raw_results}
"""
        definition = llm_synthese(prompt_synthese, llm)
        definitions[mot] = definition
    return definitions

#TODO Verifier cette partie
def rechercher_pistes_solutions(pistes: list, llm: Llama, generalisation: str) -> list:
    evaluations = []
    for piste in pistes:
        print(f"🔍 Évaluation de la piste de solution : {piste}")
        raw_results = search.run(f"{piste}")

        prompt_eval = f"""
Tu es un expert dans ce contexte {generalisation}. Analyse la piste de solution suivante : "{piste}".
En te basant sur les résultats de recherche ci-dessous, détermine si cette piste est plausible (oui/non) et explique pourquoi en 2-4 phrases.
Réponds UNIQUEMENT avec un JSON valide : {{"plausible": true/false, "explication": "..."}}

Résultats de recherche :
{raw_results}
"""
        #TODO Verifier ceci pour le json
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


# CORRECTION : ajout du paramètre generalisation + correction de l'appel à llm_synthese
def rechercher_plan_action(plan: list, llm: Llama, generalisation: str) -> dict:
    plan_detail = {}

    for point in plan:
        print(f"🔍 Approfondissement du point : {point}")
        queries = [
            f"{point} {generalisation} explications",
            f"{point} exemple concret",
            f"{point} avantages inconvénients"
        ]
        all_raw = ""
        for q in queries:
            try:
                raw = search.run(q)
                all_raw += f"\n--- Résultats pour '{q}' ---\n{raw}"
            except Exception as e:
                print(f"Erreur recherche {q}: {e}")

        # Prompt exigeant et structuré, intégrant la généralisation
        prompt_synthese = f"""
Tu es un expert dans ce domaine : {generalisation}. À partir des informations suivantes, rédige une section très détaillée sur le sujet "{point}".
Utilise TOUS les résultats pour enrichir ta réponse.
Structure obligatoire :
- Définition précise
- Concepts clés (liste)
- Exemples avec pseudo-code ou calculs
- Tableau comparatif si possible (format markdown)
- Points d'attention ou erreurs fréquentes
Longueur : environ 500 mots.

Résultats de recherche :
{all_raw}
"""
        contenu = llm_synthese(prompt_synthese, llm)
        plan_detail[point] = contenu
    return plan_detail


# ------------------------------
# 7. Pipeline principal
# ------------------------------
def run_research_pipeline(sections: dict, llm: Llama) -> dict:
    def nettoie(chaine):
        return chaine.replace('\\n', '\n')

    # Application sur les trois champs textuels
    mots_cles = [m.strip() for m in nettoie(sections.get('mot cles', '')).split('\n') if m.strip()]
    pistes = [p.strip() for p in nettoie(sections.get('pistes de solution', '')).split('\n') if p.strip()]
    plan = [p.strip() for p in nettoie(sections.get('plan action', '')).split('\n') if p.strip()]
    generalisation = sections.get('generalisation', '')

    resultats = {}

    if mots_cles:
        resultats['definitions'] = rechercher_definitions(mots_cles, llm, generalisation)
    else:
        resultats['definitions'] = {}

    if pistes:
        resultats['pistes_evaluees'] = rechercher_pistes_solutions(pistes, llm, generalisation)
    else:
        resultats['pistes_evaluees'] = []

    if plan:
        resultats['plan_detail'] = rechercher_plan_action(plan, llm, generalisation)
    else:
        resultats['plan_detail'] = {}

    return resultats

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




# ------------------------------
# 8. Exemple d'intégration dans votre script existant
# ------------------------------
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