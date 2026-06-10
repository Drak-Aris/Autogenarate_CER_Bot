import random
from llama_cpp import Llama
import os

def extraire_sections_utiles(data: dict) -> dict:
    cles_requises = ["generalisation"]
    return {cle: data[cle] for cle in cles_requises if cle in data}

def compter_tokens(texte: str, llm: Llama) -> int:
    return len(llm.tokenize(texte.encode("utf-8")))

def llm_synthese(prompt: str, max_tokens: int, temperature: float, top_p: float, llm: Llama) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=False
    )
    return response['choices'][0]['message']['content'].strip()

def resumer_sections(plan_detail: dict, llm: Llama, temperature: float, top_p: float) -> dict:#TODO Search
    resumes = {}
    for titre, contenu in plan_detail.items():
        contenu_nettoye = contenu.replace('**', '').replace('```', '').strip()
        if compter_tokens(contenu_nettoye, llm) > 600:
            contenu_nettoye = contenu_nettoye[:1200] + "..."

        prompt_resume = (
            "Résume le Texte ci-dessous en 3 à 4 phrases maximum (environ 100 tokens). Ne garde que l'idée principale, les concepts clés et une ou deux phrases d'explication.\n\n"
            f"Texte :\n{contenu_nettoye}"
        )
        resume = llm_synthese(prompt_resume, max_tokens=120, temperature=temperature,top_p=top_p, llm=llm)
        resumes[titre] = resume
        print(f"Résumé pour '{titre}'")
    return resumes

def generer_document_final(plan_detail: dict, sections:dict, llm: Llama) -> dict:#TODO Search
    temp = round(random.uniform(0.2, 0.6), 2)
    top_p = 0.8
    print(f"🎲 Température utilisée : {temp} (top_p={top_p})")

    print("Phase 1 : résumé des sections...")
    resumes = resumer_sections(plan_detail, llm, temperature=temp, top_p=top_p)

    parties = [f"## {titre}\n{resume}" for titre, resume in resumes.items()]
    bloc_resumes = "\n\n".join(parties)

    generalisation = sections.get('generalisation', '')

    prompt_final = (
        f"Tu es un rédacteur scientifique. À partir des notes résumées ci-dessous, rédige un document complet, structuré et harmonisé sur: {generalisation}. Le document doit être très détaillé et occuper environ 5000 tokens.\n\n"
        "Structure obligatoire :\n"
        "- Introduction générale\n"
        "- Pour chaque section des notes : définition, concepts clés, exemples (en pseudo-code si pertinent), tableau comparatif (obligatoire pour chaque thème si pertinent), points d'attention.\n"
        "- Transitions fluides entre les sections\n"
        "Utilise toutes les informations fournies, enrichis-les avec tes connaissances, et développe chaque point pour atteindre la longueur demandée.\n"
        "IMPORTANT : Ne termine PAS le document par une mention du nombre de tokens, ni par 'Total des tokens', ni par aucune autre note technique. La dernière phrase doit faire partie de la conclusion.\n\n"
        f"Notes (résumés) :\n{bloc_resumes}."
    )

    tokens_prompt = compter_tokens(prompt_final, llm)
    max_tokens = 8192 - tokens_prompt - 50
    if max_tokens < 500:
        max_tokens = 500
        print("⚠️  Espace insuffisant, limitation à 500 tokens.")
    else:
        print("Génération du plan d'action...")

    document_final = llm_synthese(prompt_final, max_tokens=max_tokens,temperature=temp, top_p=top_p, llm=llm)

    print(f"Plan d'action complet généré : {compter_tokens(document_final, llm)} tokens")
    return document_final

model_path = os.path.join(os.path.dirname(__file__), "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")

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

if __name__ == '__main__':
    import json  # Assurez-vous d'importer json si ce n'est pas déjà fait

    # Charger le fichier JSON contenant plan_detail et generalisation
    with open("../json/recherche_resultats.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    plan_detail = data.get("plan_detail")
    sections = extraire_sections_utiles(data)

    if plan_detail:
        print("Début de la génération du plan d'action...")
        document_md = generer_document_final(plan_detail, sections, llm)
        with open("etude.md", "w", encoding="utf-8") as f:
            f.write(document_md)
        print("📝 Plan d'action généré")
    else:
        print("❌ Aucun plan détaillé trouvé, impossible de générer le document.")