import os
import json
import re
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from llama_cpp import Llama

load_dotenv()


def extraire_sections_utiles(data: dict) -> dict:
    cles_requises = ["mot cles", "pistes de solution", "plan action", "generalisation"]
    return {cle: data[cle] for cle in cles_requises if cle in data}


def check_serper_remote_access() -> bool:
    try:
        resp = requests.get(os.getenv("serper_flag_url"), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        access = data.get("access", False)
        if isinstance(access, str):
            return access.lower() == "true"
        return bool(access)
    except Exception as e:
        print(f"⚠️ Problème lors de la connexion serper {e}")
        print("Par mesure de sécurité, l'accès à Serper est bloqué.")
        return False


if not check_serper_remote_access():
    raise RuntimeError(
        "🔒 L'accès à Serper est actuellement désactivé par l'administrateur. "
        "Pour le réactiver, contacter l'administrateur. "
    )

serper_api = os.getenv("serper_api_key")
if not serper_api:
    raise ValueError("La clé API de serper rencontre un problème.")

max_result = 6
search = GoogleSerperAPIWrapper(serper_api_key=serper_api, k=max_result)


def llm_synthese(prompt: str, llm: Llama, max_tokens:int, creativite:float) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=creativite,
        stream=False
    )
    return response['choices'][0]['message']['content'].strip()

#TODO ici
def safe_search_run(query: str, max_retries: int = 4) -> str:
    base_delay = 1.0

    for tentative in range(max_retries):
        try:
            if tentative == 0:
                time.sleep(random.uniform(0.1, 0.3))
            return search.run(query)
        except Exception as e:
            erreur_str = str(e)
            if "429" in erreur_str or "Too Many Requests" in erreur_str:
                delai = (base_delay * (1.5 ** tentative)) + random.uniform(0.1, 0.5)
                time.sleep(delai)
            else:
                return f"Erreur de recherche : {erreur_str}"

    return "Erreur : Requête abandonnée (429)."

#TODO ici
def executer_recherches_en_parallele(liste_requetes: list) -> dict:
    resultats_previsuels = {}
    if not liste_requetes:
        return resultats_previsuels

    print(f"🚀 Lancement de {len(liste_requetes)} requêtes web en parallèle...")

    # ⚡ OPTIMISATION 2 : On monte à 5 instances simultanées
    with ThreadPoolExecutor(max_workers=5) as executor:
        futur_a_requete = {executor.submit(safe_search_run, q): q for q in liste_requetes}

        for futur in as_completed(futur_a_requete):
            requete = futur_a_requete[futur]
            try:
                resultats_previsuels[requete] = futur.result()
            except Exception as e:
                resultats_previsuels[requete] = f"Aucun résultat. Error:{e}"

    return resultats_previsuels


def rechercher_definitions(mots_cles: list, llm: Llama, generalisation: str, resultats_recherche: dict, max_tokens, creativite) -> dict:
    definitions = {}
    for mot in mots_cles:
        query_key = f"définition {mot} {generalisation}"
        raw_results = resultats_recherche.get(query_key, "")

        prompt_synthese = f"""
Résultats web : {raw_results}
Donne une définition claire et très concise (2 phrases max) du terme "{mot}" dans le contexte : {generalisation}.
"""
        definitions[mot] = llm_synthese(prompt_synthese, llm, max_tokens, creativite)
    return definitions


def rechercher_pistes_solutions(pistes: list, llm: Llama, generalisation: str, resultats_recherche: dict, max_tokens, creativite) -> list:
    evaluations = []
    for piste in pistes:
        raw_results = resultats_recherche.get(piste, "")

        prompt_eval = f"""
Contexte: {generalisation}. Piste: "{piste}".
Résultats web: {raw_results}
Cette piste est-elle plausible ? Réponds UNIQUEMENT avec ce JSON strict :
{{"plausible": true, "explication": "2 phrases max d'explication"}}
"""
        reponse = llm_synthese(prompt_eval, llm,  max_tokens, creativite)

        reponse_nettoyee = reponse.strip().strip('`').replace('json\n', '')
        try:
            eval_json = json.loads(reponse_nettoyee)
            evaluations.append({
                "piste": piste,
                "plausible": bool(eval_json.get("plausible")),
                "explication": eval_json.get("explication", "")
            })
        except json.JSONDecodeError:
            plausible_match = re.search(r'"plausible"\s*:\s*(true|false)', reponse_nettoyee, re.IGNORECASE)
            is_plausible = plausible_match.group(1).lower() == 'true' if plausible_match else None
            evaluations.append({"piste": piste, "plausible": is_plausible, "explication": "Analyse texte effectuée."})
    return evaluations


# ─────────────────────────────────────────────────────────────────
# ⚡ MODIFICATION : PLUS D'APPEL LLM ICI, RETOUR BRUT DU RÉSULTAT SERPER
# ─────────────────────────────────────────────────────────────────
def rechercher_plan_action(plan: list, generalisation: str, resultats_recherche: dict) -> dict:
    plan_detail = {}

    for point in plan:
        # 1. Définition des clés exactes (qui correspondront aux requêtes lancées)
        q_explication = f"{point} {generalisation} explication concept"
        q_exemple = f"{point} {generalisation} exemple concret application"
        q_avantages = f"{point} {generalisation} avantages inconvénients"

        # 2. Récupération des résultats bruts pour chaque aspect
        raw_explication = resultats_recherche.get(q_explication, "Pas de données d'explication.")
        raw_exemple = resultats_recherche.get(q_exemple, "Pas de données d'exemple.")
        raw_avantages = resultats_recherche.get(q_avantages, "Pas de données sur les avantages/inconvénients.")

        # 3. Assemblage propre et structuré pour faciliter la lecture du LLM plus tard
        contenu_assemble = (
            f"--- EXPLICATION ET CONCEPTS ---\n{raw_explication}\n\n"
            f"--- EXEMPLES CONCRETS ---\n{raw_exemple}\n\n"
            f"--- AVANTAGES ET INCONVÉNIENTS ---\n{raw_avantages}"
        )

        # 4. Sauvegarde du bloc assemblé
        plan_detail[point] = contenu_assemble

    return plan_detail


def run_research_pipeline(sections: dict, llm: Llama,  max_tokens, creativite) -> dict:
    def nettoie(chaine):
        return chaine.replace('\\n', '\n')

    mots_cles = [m.strip() for m in nettoie(sections.get('mot cles', '')).split('\n') if m.strip()]
    pistes = [p.strip() for p in nettoie(sections.get('pistes de solution', '')).split('\n') if p.strip()]
    plan = [p.strip() for p in nettoie(sections.get('plan action', '')).split('\n') if p.strip()]
    generalisation = sections.get('generalisation', '')

    toutes_les_requetes = []

    # Préparation des requêtes allégées
    for mot in mots_cles:
        toutes_les_requetes.append(f"définition {mot} {generalisation}")
    for piste in pistes:
        toutes_les_requetes.append(piste)
    for point in plan:
        toutes_les_requetes.extend([
            f"{point} {generalisation} explication concept",
            f"{point} {generalisation} exemple concret application",
            f"{point} {generalisation} avantages inconvénients"
        ])

    dictionnaire_resultats_web = executer_recherches_en_parallele(toutes_les_requetes)

    resultats = {}

    print("🧠 Génération des définitions via l'IA...")
    resultats['definitions'] = rechercher_definitions(mots_cles, llm, generalisation, dictionnaire_resultats_web, max_tokens, creativite)

    print("🧠 Évaluation des pistes de solution via l'IA...")
    resultats['pistes_evaluees'] = rechercher_pistes_solutions(pistes, llm, generalisation, dictionnaire_resultats_web,  max_tokens, creativite)

    # L'appel reste inchangé pour préserver la structure globale du pipeline
    print("📦 Collecte brute du plan d'action (Raccourci sans LLM activé)...")
    resultats['plan_detail'] = rechercher_plan_action(plan, generalisation, dictionnaire_resultats_web)

    os.makedirs("../json", exist_ok=True)
    with open("../json/recherche_resultats.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print("✅ Fin du pipeline de recherche avec succès.")
    return resultats