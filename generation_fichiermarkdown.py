import os
import json
import requests
from pathlib import Path

# --- CONFIGURATION ---
# Liste de tes fichiers JSON
CHEMINS_JSON = [
    "json/resultat_extract_1.json",
    "json/resultat_extract_2.json"
]
DOSSIER_SORTIE = Path("output")
FICHIER_SORTIE = DOSSIER_SORTIE / "Cahier_Etudes_Recherches.md"

# Configuration du modèle local (ex: Ollama)
API_URL = "http://localhost:11434/api/generate"
MODELE_LLM = "qwen2.5-coder-3b-instruct-q4_k_m"

# Paramètre de contexte : 8192 devrait passer sur 8Go RAM pour un modèle 3B
# Si ça rame trop, redescends à 4096.
OPTIONS_LLM = {
    "num_ctx": 8192,
    "temperature": 0.3  # Température basse pour de la rédaction structurée
}

# --- PARTIES STATIQUES DU MARKDOWN ---
# On stocke ici ce qui ne nécessite pas l'intervention de l'IA pour économiser le contexte

ENTETE_MARKDOWN = """# Cahier d’Études et de Recherches
## Les Gardiens du Temps et de la Complexité

<p align="center">
  <img src="images/Logo_institut.jpeg" alt="Logo Institut" width="250"/>
</p>

<p align="center">
  <img src="images/Images_doc.png" alt="Illustration Document" width="400"/>
</p>

---

| | |
| :--- | :--- |
| **Rédigé par :** | FOTUE ARIS |
| **Pilote :** | Mr Bruce JOUGUEM YOUMBI |
| **Promotion :** | X2028 |
| **Date :** | 06/04/2026 |

<br>

<p align="center">
  <strong>Institut de Formation</strong> — <em>06/04/2026</em>
</p>

---

## Table des matières
1. Analyse des besoins
2. Plan d'action
3. Réalisation du plan d'action
4. Validation des hypothèses
5. Conclusion et retour sur les objectifs
6. Bilan critique du travail effectué
7. Références et outils

---
"""

SECTION_2_STATIQUE = """
# 2. Plan d'action

Le plan d'action retenu a consisté à :

- Étudier les formes de raisonnement algorithmique
- Étudier les bases de la logique
- Étudier les opérations sur les ensembles
- Étudier les relations entre les ensembles
- Étudier les combinatoires et les probabilités algorithmiques

---
"""


def charger_jsons(chemins: list) -> dict:
    """Charge et fusionne le contenu de plusieurs fichiers JSON."""
    donnees_globales = {}
    for chemin in chemins:
        if os.path.isfile(chemin):
            with open(chemin, 'r', encoding='utf-8') as f:
                try:
                    donnees = json.load(f)
                    # Fusionner les dictionnaires
                    donnees_globales.update(donnees)
                    print(f"✅ Fichier chargé : {chemin}")
                except json.JSONDecodeError:
                    print(f"⚠️ Erreur de lecture JSON dans : {chemin}")
        else:
            print(f"⚠️ Fichier introuvable : {chemin}")
    return donnees_globales


def generer_contenu_llm(donnees_json: dict) -> str:
    """Envoie un prompt optimisé au LLM local pour générer le reste du document."""

    # Conversion du JSON en chaîne formatée pour le prompt
    contexte_json = json.dumps(donnees_json, indent=2, ensure_ascii=False)

    prompt = f"""Tu es un expert en rédaction de documentation technique et académique.
À partir des données JSON fournies ci-dessous, tu dois rédiger les sections 1, 3, 4, 5, 6 et 7 d'un "Cahier d’Études et de Recherches". 

ATTENTION : Ne rédige PAS l'en-tête, ni la table des matières, ni la section "2. Plan d'action". Ces parties sont déjà gérées.
Rédige directement à partir de "# 1. Analyse des besoins".

Respecte scrupuleusement le format Markdown, utilise des tableaux si nécessaire, et garde un ton professionnel, clair et structuré.

Voici les données brutes (JSON) sur lesquelles te baser :
{contexte_json}

Commence ta réponse directement par "# 1. Analyse des besoins".
"""

    payload = {
        "model": MODELE_LLM,
        "prompt": prompt,
        "stream": False,
        "options": OPTIONS_LLM
    }

    print("🚀 Envoi de la requête au LLM (cela peut prendre un moment)...")
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        resultat = response.json()
        return resultat.get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion à l'API locale : {e}")
        return ""


def assembler_document(contenu_llm: str):
    """Assemble les parties statiques et la partie générée par le LLM, puis sauvegarde."""
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    # On sépare le contenu généré par l'IA juste avant la section 3 pour insérer la section 2
    parties = contenu_llm.split("# 3. Réalisation du plan d'action")

    if len(parties) >= 2:
        # Reconstitution : En-tête + Section 1 (IA) + Section 2 (Statique) + Section 3 à 7 (IA)
        document_final = (
                ENTETE_MARKDOWN + "\n" +
                parties[0].strip() + "\n\n" +
                SECTION_2_STATIQUE + "\n" +
                "# 3. Réalisation du plan d'action" + parties[1]
        )
    else:
        # Fallback si le modèle n'a pas respecté le titre exact
        print(
            "⚠️ Le modèle n'a pas généré le titre exact '# 3. Réalisation du plan d'action'. Concaténation simple effectuée.")
        document_final = ENTETE_MARKDOWN + "\n" + SECTION_2_STATIQUE + "\n" + contenu_llm

    with open(FICHIER_SORTIE, 'w', encoding='utf-8') as f:
        f.write(document_final)

    print(f"\n✅ Document final généré avec succès : {FICHIER_SORTIE}")


def main():
    donnees = charger_jsons(CHEMINS_JSON)
    if not donnees:
        print("❌ Aucune donnée JSON chargée. Arrêt du script.")
        return

    contenu_ia = generer_contenu_llm(donnees)

    if contenu_ia:
        assembler_document(contenu_ia)
    else:
        print("❌ Échec de la génération par le LLM.")


if __name__ == "__main__":
    main()