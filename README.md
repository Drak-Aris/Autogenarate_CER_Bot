ameliore moi ce readme
# Autogenerate CER Bot

Bot de génération automatique de documents **CER** (Cahier d'Étude et de Recherche) à partir de templates Word (`.docx`) et de données structurées (JSON).

## Fonctionnalités

- Remplissage automatique de champs (ex. `{{titre}}`, `{{auteur}}`, `{{date}}`)
- Support des sections dynamiques (introduction, méthodologie, résultats, bibliographie, etc.)
- Génération au format **DOCX** ou **PDF**
- Ajout automatique d’en-tête et pied de page
- Mode batch possible (extension CSV prévue)

## Prérequis

- Python 3.8 ou supérieur
- [Microsoft Word] ou [LibreOffice] (optionnel pour l’édition du template)



# Pipeline de recherche documentaire avec LLM local et LangChain

Cette partie du projet illustre la mise en place d'un pipeline d'enrichissement de contenu utilisant un **modèle de langage local** (quantifié, sans GPU) et la **recherche Google via LangChain** (Serper).  
Le système extrait les sections clés d'un document (mots-clés, pistes de solution, plan d'action), puis interroge le web pour obtenir des définitions précises, valider des hypothèses et approfondir chaque point du plan.  
L'ensemble fonctionne sur une machine modeste (8 Go de RAM, CPU uniquement).

---

## 📦 Technologies utilisées

- **[Python 3.10+](https://www.python.org/)** : langage principal.
- **[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)** : inférence de modèles au format GGUF sur CPU.
- **[LangChain (community)](https://python.langchain.com/)** : intégration de l'outil de recherche Google Serper (`GoogleSerperAPIWrapper`).
- **[Serper.dev](https://serper.dev)** : API de recherche Google (plan gratuit, 1 000 requêtes/mois).
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** : gestion des variables d’environnement et de la clé API.
- **[Requests](https://docs.python-requests.org/)** : vérification distante du flag de contrôle d’accès.
- **Modèle local** : `chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf` (format GGUF, quantification 4 bits Q4_K_M, ~2 Go de RAM).

---

## 🧠 Techniques et concepts clés

### 1. Exécution 100% locale et économe
- Le modèle tourne sur CPU grâce à `llama-cpp-python`, sans GPU.
- La quantification **Q4_K_M** réduit drastiquement la mémoire nécessaire (~2 Go pour 2,4 milliards de paramètres).
- La fenêtre de contexte (`n_ctx`) est limitée à **4096 tokens** pour tenir dans la RAM disponible.

### 2. Extraction structurée des sections
- Un premier appel au LLM local (prompt spécialisé) transforme le texte brut d’un document en un **objet JSON** contenant les sections : `mot cles`, `contexte`, `besoins`, `contraintes`, `problematiques`, `generalisation`, `pistes de solution`, `plan action`.
- Le prompt impose un formatage strict et place chaque élément d’une liste sur une ligne séparée (échappement `\n` dans la chaîne JSON).

### 3. Pipeline modulaire de recherche web
Le flux principal (`run_research_pipeline`) orchestre trois étapes distinctes, toutes partageant la même instance du LLM local :

| Module | Objectif | Détail technique |
|--------|----------|------------------|
| `rechercher_definitions` | Obtenir une définition claire pour chaque mot-clé | Recherche Google + synthèse concise (200 tokens max) |
| `rechercher_pistes_solutions` | Évaluer la plausibilité de chaque piste de solution | Recherche Google + réponse JSON structurée `{plausible, explication}` (300 tokens max) |
| `rechercher_plan_action` | Approfondir chaque point du plan | 3 requêtes complémentaires par point, résultats tronqués pour ne pas saturer le contexte, puis synthèse détaillée (2200 tokens max) |

### 4. Gestion fine de la fenêtre de contexte (4096 tokens)
- Les résultats bruts de Google sont **tronqués à 1000–1200 caractères** avant d’être injectés dans le prompt.
- La synthèse du plan d’action utilise un `max_tokens` élevé (2200) mais le prompt d’entrée reste sous 1800 tokens, garantissant un total sous 4096 tokens.
- Aucun historique n’est conservé entre les appels (pas de mémoire), chaque appel au LLM est indépendant.

### 5. Optimisation du prompt de synthèse
- Les prompts de génération sont conçus pour exiger une structure claire : définition, concepts clés, exemples concrets, tableaux comparatifs, points d’attention.
- La “généralisation” du document est injectée dans chaque requête de recherche pour améliorer la pertinence des résultats.

### 6. Contrôle d’accès à distance (gratuit)
- Un fichier JSON hébergé sur un **Gist GitHub secret** (URL brute) détermine si l’API Serper peut être utilisée.
- La fonction `check_serper_remote_access()` lit le champ `access` du fichier à distance. Si le flag est `false`, le programme s’arrête immédiatement.
- Cette méthode permet à l’administrateur de bloquer/débloquer les recherches web sans modifier le code, sans toucher à la clé Serper, et sans frais supplémentaires.

### 7. Robustesse des échanges avec le LLM local
- Nettoyage automatique des blocs de code Markdown (` ```json `) dans les réponses.
- Gestion des erreurs de parsing JSON avec un fallback explicite.
- Remplacement des doubles antislashs (`\\n`) en vrais sauts de ligne pour le découpage des listes.

---

## ⚙️ Configuration minimale

- **RAM** : 8 Go (le modèle consomme ~2 Go, le reste pour le système et les traitements).
- **Stockage** : quelques Mo pour le modèle GGUF.
- **Connexion Internet** : indispensable pour les appels à l’API Serper.
- **Clé API Serper** : gratuite, à placer dans un fichier `.env` (`SERPER_API_KEY=...`).
- **Gist de contrôle** : optionnel, URL du flag stockée dans `serper_flag_url` du `.env`.

---

## 🚀 Exemple d’utilisation

```python
# Chargement du modèle
llm = Llama(model_path="chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf", n_ctx=4096)

# Extraction des sections depuis un document
sections = extraire_sections_avec_llama(texte, llm)

# Recherche et enrichissement
resultats = run_research_pipeline(sections, llm)

# resultats contient les définitions, les évaluations de pistes et le plan détaillé
Les résultats sont sauvegardés dans recherche_resultats.json pour une utilisation ultérieure (par exemple, génération d’un document LaTeX).
```
📁 Structure des fichiers concernés
web_research.py : pipeline de recherche et fonctions principales.

Extract_content.py : extraction du JSON à partir du document brut.

.env : clés et configuration (non versionné).

foundation_model/ : dossier contenant le fichier .gguf.


















# 📘 Extraction de Sections Structurées avec un LLM Local

Ce projet extrait automatiquement les sections clés (mots clés, contexte, besoins, contraintes, problématique, généralisation, pistes de solution, plan d’action) d’un document Word ou PDF en utilisant un modèle de langage (LLM) exécuté localement sur CPU.

Il est conçu pour fonctionner sur des machines à ressources limitées (Intel Core i7 12e génération, 8 Go de RAM) grâce à la quantification GGUF et à `llama-cpp-python`.

---

## 🎯 Objectifs

- Extraire le texte brut de fichiers `.docx` et `.pdf`.
- Analyser ce texte avec un LLM pour en isoler des sections prédéfinies.
- Obtenir une réponse JSON structurée et directement exploitable.
- Garantir une exécution fluide sur CPU, sans GPU, avec une RAM limitée.

---

## ⚙️ Architecture Globale
Fichier (.docx / .pdf)
│
▼
Extraction texte brut (python-docx / pdfplumber)
│
▼
Prompt structuré + LLM local (llama-cpp-python)
│
▼
Streaming de la réponse JSON
│
▼
Post-traitement (nettoyage, parsing JSON, correction des sauts de ligne)
│
▼
Dictionnaire Python des sections extraites

text

---

## 📚 Librairies Principales

| Librairie | Version | Usage |
|-----------|---------|-------|
| `python-docx` | ≥ 1.1.0 | Extraction de texte depuis des fichiers `.docx` |
| `pdfplumber` | ≥ 0.10.0 | Extraction fiable du texte des PDF |
| `llama-cpp-python` | ≥ 0.2.50 | Inférence locale sur CPU avec modèles GGUF |
| `huggingface_hub` | ≥ 0.20.0 | Téléchargement de modèles GGUF pré-quantifiés |

---

## 🧠 Modèle de Langage

**Modèle retenu** : [Chocolatine-2-4B-Instruct-DPO-v2.1](https://huggingface.co/jpacifico/Chocolatine-2-4B-Instruct-DPO-v2.1)  
*Fine-tune du modèle Qwen3-2.5B, optimisé pour l’instruction et le dialogue.*

**Format utilisé** : **GGUF 4-bit quantifié (Q4_K_M)**  
- Taille du fichier : ~1.6 Go  
- Empreinte RAM à l’inférence : < 2 Go  
- Exécution fluide sur CPU Intel i7 12e génération / 8 Go de RAM sans swap.

**Chargement du modèle** :
```python
from llama_cpp import Llama

llm = Llama(
    model_path="chocolatine-2-4b-instruct-dpo-v2.1-q4_k_m.gguf",
    n_ctx=4096,        # taille du contexte limitée pour économiser la RAM
    n_threads=4,       # parallélisation sur CPU
    verbose=False
)









## Installation

```bash
git clone https://github.com/votre-org/autogenerate_cer_bot.git
cd autogenerate_cer_bot
pip install -r requirements.txt