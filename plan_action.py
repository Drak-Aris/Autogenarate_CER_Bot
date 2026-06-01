import json
import os
import random
from llama_cpp import Llama
#TODO reviser et revoir tout le code

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__),
                          "foundation_model/chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf")
RESULTS_FILE = "/json/recherche_resultats.json"
OUTPUT_FILE = "document_final.md"

CONTEXT_SIZE = 4096
MAX_TOKENS_PER_SUMMARY = 120      # chaque résumé de section
TARGET_FINAL_TOKENS = 3500        # longueur souhaitée du document final

# Plages de température (ajustez selon vos préférences)
TEMPERATURE_MIN = 0.2
TEMPERATURE_MAX = 0.6
TOP_P = 0.9                       # nucleus sampling pour plus de variété

# -------------------------------------------------------------------
# Chargement du modèle (une seule fois)
# -------------------------------------------------------------------
try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=CONTEXT_SIZE,
        n_threads=4,
        verbose=False
    )
    print("✅ Modèle chargé avec succès.")
except Exception as e:
    print(f"❌ Erreur lors du chargement du modèle : {e}")
    exit(1)

# -------------------------------------------------------------------
# Fonction utilitaire : nombre de tokens d'un texte
# -------------------------------------------------------------------
def compter_tokens(texte: str) -> int:
    return len(llm.tokenize(texte.encode("utf-8")))

# -------------------------------------------------------------------
# Appel au LLM avec créativité paramétrable
# -------------------------------------------------------------------
def llm_synthese(prompt: str, max_tokens: int = 256, temperature: float = 0.2, top_p: float = 0.9) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=False
    )
    return response['choices'][0]['message']['content'].strip()

# -------------------------------------------------------------------
# Phase 1 : résumé de chaque section du plan d'action
# -------------------------------------------------------------------
def resumer_sections(plan_detail: dict, temperature: float, top_p: float) -> dict:
    """
    Pour chaque point du plan d'action, génère un résumé très concis.
    Retourne un dictionnaire {titre: résumé}.
    """
    resumes = {}
    for titre, contenu in plan_detail.items():
        contenu_nettoye = contenu.replace('**', '').replace('```', '').strip()
        # Tronquer le contenu si trop long
        if compter_tokens(contenu_nettoye) > 600:
            contenu_nettoye = contenu_nettoye[:1200] + "..."

        prompt_resume = (
            "Résume le texte suivant en 3 à 4 phrases maximum (environ 100 tokens). "
            "Ne garde que l'idée principale, les concepts clés et une ou deux phrases d'explication.\n\n"
            f"Texte :\n{contenu_nettoye}"
        )
        resume = llm_synthese(prompt_resume, max_tokens=MAX_TOKENS_PER_SUMMARY,
                              temperature=temperature, top_p=top_p)
        resumes[titre] = resume
        print(f"   ✓ Résumé pour '{titre}' : {compter_tokens(resume)} tokens")

    return resumes

# -------------------------------------------------------------------
# Phase 2 : assemblage et génération du document final
# -------------------------------------------------------------------
def generer_document_final(plan_detail: dict) -> str:
    # 🎲 Générer des paramètres de créativité aléatoires pour cette exécution
    temp = round(random.uniform(TEMPERATURE_MIN, TEMPERATURE_MAX), 2)
    print(f"🎲 Température utilisée : {temp} (top_p={TOP_P})")

    # 1. Résumer chaque section avec ces paramètres
    print("📝 Phase 1 : résumé des sections...")
    resumes = resumer_sections(plan_detail, temperature=temp, top_p=TOP_P)

    # 2. Construire un bloc condensé
    parties = [f"## {titre}\n{resume}" for titre, resume in resumes.items()]
    bloc_resumes = "\n\n".join(parties)
    tokens_bloc = compter_tokens(bloc_resumes)
    print(f"📊 Tokens du bloc résumé : {tokens_bloc}")

    # 3. Préparer le prompt final
    prompt_final = (
        "Tu es un rédacteur scientifique. À partir des notes résumées ci-dessous, "
        "rédige un document complet, structuré et harmonisé sur les fondements de la "
        "pensée algorithmique. Le document doit être très détaillé et occuper environ "
        f"{TARGET_FINAL_TOKENS} tokens.\n\n"
        "Structure attendue :\n"
        "- Introduction générale\n"
        "- Pour chaque section : définition, concepts clés, exemples (en pseudo-code si pertinent), "
        "tableau comparatif si possible, points d'attention.\n"
        "- Transitions fluides entre les sections\n"
        "- Conclusion synthétique et ouverture\n\n"
        "Utilise toutes les informations fournies, enrichis-les avec tes connaissances, "
        "et développe chaque point pour atteindre la longueur demandée.\n\n"
        f"Notes (résumés) :\n{bloc_resumes}"
    )

    # 4. Calculer l'espace restant pour la réponse
    tokens_prompt = compter_tokens(prompt_final)
    max_tokens = min(TARGET_FINAL_TOKENS, CONTEXT_SIZE - tokens_prompt - 50)
    print(f"📏 Tokens du prompt final : {tokens_prompt} → max_tokens alloués : {max_tokens}")

    if max_tokens < 500:
        print("⚠️  Espace insuffisant pour un document long, réduction à 500 tokens.")
        max_tokens = 500

    # 5. Génération du document final (mêmes paramètres de créativité)
    print("📄 Génération du document final...")
    document = llm_synthese(prompt_final, max_tokens=max_tokens,
                            temperature=temp, top_p=TOP_P)
    print(f"✅ Document généré : {compter_tokens(document)} tokens")
    return document

# -------------------------------------------------------------------
# Point d'entrée
# -------------------------------------------------------------------
if __name__ == '__main__':
    # Charger le fichier JSON des résultats
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            resultats = json.load(f)
        plan_detail = resultats.get('plan_detail', {})
        if not plan_detail:
            print("❌ Aucun plan d'action trouvé dans le fichier JSON.")
            exit(1)
    except FileNotFoundError:
        print(f"❌ Fichier introuvable : {RESULTS_FILE}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON : {e}")
        exit(1)

    # Générer le document final
    document_final = generer_document_final(plan_detail)

    # Sauvegarde
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(document_final)
    print(f"💾 Document sauvegardé dans {OUTPUT_FILE}")