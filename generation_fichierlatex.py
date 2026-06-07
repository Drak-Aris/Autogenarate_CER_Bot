import os
import json
import re
import requests
from pathlib import Path
from llama_cpp import Llama

# --- CONFIGURATION ---
json_informations = "json/informations.json"

chemin_template = "template/Theme_classique/retour_aller"
json_contenu = "json/resultat_extract.json"
json_recherche = "json/recherche_resultats.json"
json_infos = "json/informations.json"
markdown_source = "etude.md"

dossier_plan_action = Path("template/Theme_classique/plan_d'action")
lien_definition = dossier_plan_action / "definition_motscles.tex"
lien_pistes = dossier_plan_action / "pistes_evaluees.tex"
lien_page_infos = Path("template/Theme_classique/page_informations.tex")
lien_objectifs = Path("template/Theme_classique/objectifs_apprentissage.tex")
lien_liens_ressources = Path("template/Theme_classique/references_outils.tex")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "foundation_model_latex/qwen2.5-coder-3b-instruct-q4_k_m.gguf")
N_CTX = 8192
MAX_TOKENS_GEN = N_CTX - 100

key_ignore = {"mot cles"}


def charger_json(chemin_json: str) -> dict:
    with open(chemin_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def charger_definitions(chemin_json: str) -> list:
    data = charger_json(chemin_json)
    definitions_dict = data.get("definitions", {})
    return [{"terme": terme, "definition": defn} for terme, defn in definitions_dict.items()]


def charger_pistes(chemin_json: str) -> list:
    data = charger_json(chemin_json)
    return data.get("pistes_evaluees", [])


def charger_infos_auteur(chemin_json: str) -> dict:
    data = charger_json(chemin_json)
    return data.get("auteur", data)


def formater_contenu(texte: str) -> str:
    if '\\n' in texte:
        items = [item.strip() for item in texte.split('\\n') if item.strip()]
        if not items:
            return texte
        latex_items = '\n'.join([f'    \\item {item}' for item in items])
        return '\\begin{itemize}\n' + latex_items + '\n\\end{itemize}'
    return texte


def ecrire_fichier_cle(dossier: Path, cle: str, contenu: str):
    chemin_fichier = dossier / f"{cle}.tex"
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"✅ Fichier '{cle}.tex' créé/écrasé.")


def generer_lignes_definitions(definitions: list) -> str:
    lignes = []
    for d in definitions:
        terme = d.get("terme", "")
        definition = d.get("definition", "")
        lignes.append(f"{terme} & {definition} \\\\")
    return '\n'.join(lignes)


def ecrire_definitions(definitions: list):
    contenu = generer_lignes_definitions(definitions)
    dossier_plan_action.mkdir(parents=True, exist_ok=True)
    with open(lien_definition, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"✅ Fichier '{lien_definition.name}' mis à jour avec {len(definitions)} définitions.")


def ecrire_pistes_evaluees(pistes: list):
    dossier_plan_action.mkdir(parents=True, exist_ok=True)
    blocs = []
    for i, piste_data in enumerate(pistes, start=1):
        piste_texte = piste_data.get("piste", "")
        plausible = piste_data.get("plausible", False)
        explication = piste_data.get("explication", "")
        confirmation = "oui" if plausible else "non"
        bloc = (
            f"\\section{{Hypothèse {i}}}\n"
            f"\\textit{{{piste_texte}}}\n\n"
            f"\\textbf{{Confirmation :}} {confirmation}. {explication}\n"
        )
        blocs.append(bloc)
    contenu = "\n".join(blocs)
    with open(lien_pistes, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"✅ Fichier '{lien_pistes.name}' mis à jour avec {len(pistes)} pistes.")


def ecrire_page_informations(infos: dict):
    nom = infos.get("nom", "")
    pilote = infos.get("pilote", "")
    promotion = infos.get("promotion", "")
    date = infos.get("date", "")

    lignes = [
        f"Rédigé par : & {nom} \\\\",
        f"Pilote : & {pilote} \\\\",
        f"Promotion : & {promotion} \\\\",
        f"Date : & {date} \\\\",
    ]
    contenu = "\n".join(lignes)

    lien_page_infos.parent.mkdir(parents=True, exist_ok=True)
    with open(lien_page_infos, 'w', encoding='utf-8') as f:
        f.write(contenu)
    print(f"✅ Fichier '{lien_page_infos.name}' mis à jour avec les informations de l'auteur.")


# ───────────────────── GÉNÉRATION DES OBJECTIFS ─────────────────────
def generer_objectifs_latex(objectifs_str: str) -> str:
    """
    Génère le tableau LaTeX complet des objectifs à partir de la chaîne formatée
    (issue du JSON). La chaîne est de la forme :
    "Compétence\tDétails\nCONNAISSANCE\t• item1\n• item2\n..."
    """
    lignes_data = objectifs_str.strip().split('\n')
    if len(lignes_data) < 2:
        return "% Aucun objectif fourni.\n"

    # Ignorer la première ligne d'en-tête
    lignes_competences = lignes_data[1:]

    # Regrouper les lignes par compétence : une compétence commence par une ligne contenant "\t"
    blocs = []
    competence_courante = None
    items_courant = []

    for ligne in lignes_competences:
        if '\t' in ligne:
            # Nouvelle compétence détectée
            if competence_courante is not None and items_courant:
                # Sauvegarder le bloc précédent
                items_latex = '\n'.join(f'    \\item {item}' for item in items_courant)
                blocs.append(
                    f'\\textbf{{{competence_courante}}} &\n'
                    f'\\begin{{itemize}}[leftmargin=1.1cm,itemsep=0.2em]\n'
                    f'{items_latex}\n'
                    f'\\end{{itemize}}\\\\\n'
                )
            # Extraire la nouvelle compétence et ses premiers items (séparés par \t)
            parts = ligne.split('\t', 1)
            competence_courante = parts[0].strip()
            details = parts[1].strip()
            # Les items sont séparés par des puces • (suivies d'un espace)
            # On nettoie les éventuels résidus
            items_raw = re.split(r'\s*•\s*', details)
            items_courant = [it.strip().rstrip(';') for it in items_raw if it.strip()]
        else:
            # Ligne supplémentaire d'items (commence par •)
            items_raw = re.split(r'\s*•\s*', ligne)
            for it in items_raw:
                it = it.strip().rstrip(';')
                if it:
                    items_courant.append(it)

    # Dernière compétence
    if competence_courante is not None and items_courant:
        items_latex = '\n'.join(f'    \\item {item}' for item in items_courant)
        blocs.append(
            f'\\textbf{{{competence_courante}}} &\n'
            f'\\begin{{itemize}}[leftmargin=1.1cm,itemsep=0.2em]\n'
            f'{items_latex}\n'
            f'\\end{{itemize}}\\\\\n'
        )

    if not blocs:
        return "% Aucune compétence valide trouvée.\n"

    latex = (
        '\\begin{center}\n'
        '\\small\n'
        '\\begin{tabularx}{\\textwidth}{L{3.8cm}Y}\n'
        '\\toprule\n'
        '\\textbf{Compétence} & \\textbf{Détails} \\\\\n'
        '\\midrule\n'
        + '\n'.join(blocs) +
        '\\bottomrule\n'
        '\\end{tabularx}\n'
        '\\end{center}\n'
    )
    return latex


# ───────────────────── GÉNÉRATION DES LIENS/RESSOURCES ─────────────────────
def generer_liens_ressources_latex(liens_str: str, ressources_str: str) -> str:
    latex = ""

    if liens_str.strip():
        items_liens = [l.strip() for l in liens_str.split('\n') if l.strip()]
        items_liens = [re.sub(r'^[·\-•*o\+]\s*', '', it) for it in items_liens]
        items_latex = '\n'.join(f'    \\item \\textit{{{item}}}' for item in items_liens)
        latex += (
            '\\begin{itemize}[leftmargin=1.2cm]\n'
            f'{items_latex}\n'
            '\\end{itemize}\n\n'
        )

    if ressources_str.strip():
        items_ressources = [r.strip() for r in ressources_str.split('\n') if r.strip()]
        items_ressources = [re.sub(r'^[·\-•*o\+]\s*', '', it) for it in items_ressources]
        biblio = []
        for i, item in enumerate(items_ressources, start=1):
            biblio.append(f'\\bibitem{{ref{i}}} {item}')
        latex += (
            '\\begin{thebibliography}{9}\n'
            + '\n'.join(biblio) + '\n'
            '\\end{thebibliography}\n'
        )

    return latex if latex else "% Aucun lien ou ressource.\n"


# ─────────────────────────────────────────────────────────────

def charger_contenu_markdown(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        try:
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise RuntimeError(f"Impossible de télécharger le markdown depuis {source} : {e}")
    else:
        chemin = Path(source)
        if not chemin.is_file():
            raise FileNotFoundError(f"Fichier markdown introuvable : {source}")
        with open(chemin, 'r', encoding='utf-8') as f:
            return f.read()


def extraire_latex(texte: str) -> str:
    pattern = r"```latex\s*(.*?)\s*```"
    match = re.search(pattern, texte, re.DOTALL)
    if match:
        texte = match.group(1).strip()
    for start_cmd in [r"\documentclass", r"\section", r"\begin{frame}"]:
        start = texte.find(start_cmd)
        if start != -1:
            texte = texte[start:]
            break
    end = texte.find(r"\end{document}")
    if end != -1:
        texte = texte[:end] + r"\end{document}"
    return texte.strip()


def generer_latex_depuis_markdown(contenu_markdown: str, llm: Llama) -> str:
    prompt = (
        "Tu es un convertisseur automatique de markdown vers LaTeX. Ta tâche est de transformer "
        "le contenu markdown fourni en un document LaTeX parfaitement structuré, en respectant "
        "scrupuleusement les règles suivantes :\n\n"
        "1. **Fidélité absolue** : tout le texte, les listes, les tableaux, les blocs de code, "
        "les formules, les notes, etc., doivent être reproduits à l'identique, sans rien omettre, "
        "ajouter, reformuler ou interpréter. Aucune information ne doit être inventée.\n\n"
        "2. **Hiérarchie des titres** :\n"
        "   - Un titre markdown de niveau 1 (#) devient \\section{...}\n"
        "   - Un titre de niveau 2 (##) devient \\subsection{...}\n"
        "   - Un titre de niveau 3 (###) devient \\subsubsection{...}\n"
        "   - Les titres en gras (**Titre**) qui ne sont pas précédés d'un # doivent être convertis "
        "en \\textbf{...} et rester dans le paragraphe.\n\n"
        "3. **Listes** :\n"
        "   - Les listes à puces (- ou *) deviennent \\begin{itemize} ... \\end{itemize}\n"
        "   - Les listes numérotées (1. 2. ...) deviennent \\begin{enumerate} ... \\end{enumerate}\n"
        "   - Les items doivent conserver exactement le même texte.\n\n"
        "4. **Tableaux** :\n"
        "   - Convertir les tableaux markdown en environnement {tabular} avec les colonnes appropriées.\n"
        "   - Utiliser \\hline pour les lignes horizontales.\n"
        "   - Le contenu de chaque cellule doit être identique au markdown.\n\n"
        "5. **Blocs de code** :\n"
        "   - Les blocs de code délimités par ``` doivent être placés dans \\begin{verbatim} ... \\end{verbatim}\n"
        "   - Ne pas modifier le contenu du code, y compris les retours à la ligne.\n\n"
        "6. **Formules mathématiques** :\n"
        "   - Les expressions entre $ restent entre $ (mode inline).\n"
        "   - Les expressions entre $$ restent entre $$ (mode display).\n\n"
        "7. **Styles de texte** :\n"
        "   - **gras** -> \\textbf{gras}\n"
        "   - *italique* -> \\textit{italique}\n"
        "   - `code` -> \\texttt{code}\n\n"
        "8. **Interdictions strictes** :\n"
        "   - NE PAS ajouter de \\documentclass, \\usepackage, \\begin{document} ou \\end{document}.\n"
        "   - NE PAS commenter le code (pas de % commentaire).\n"
        "   - NE PAS ajouter de texte supplémentaire avant ou après le code LaTeX.\n"
        "   - Le résultat doit commencer directement par \\section{...} ou \\subsection{...} si le markdown commence par un titre.\n"
        "   - Si le markdown commence par du texte sans titre, commencer par ce texte.\n\n"
        "Voici le contenu markdown à convertir :\n\n"
        f"{contenu_markdown}\n\n"
        "Retourne UNIQUEMENT le code LaTeX résultant, sans aucun autre caractère."
    )

    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes LaTeX code."},
        {"role": "user", "content": prompt}
    ]
    prompt_str = ""
    for msg in messages:
        prompt_str += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
    prompt_str += "<|im_start|>assistant\n"

    output = llm.create_completion(
        prompt=prompt_str,
        max_tokens=MAX_TOKENS_GEN,
        temperature=0.2,
        stop=["<|im_end|>", "<|im_start|>"],
        echo=False
    )
    raw_text = output['choices'][0]['text']
    latex_genere = extraire_latex(raw_text)

    if not latex_genere:
        raise ValueError("Le LLM n'a pas retourné de code LaTeX valide.")
    return latex_genere


def main():
    if not os.path.isfile(json_contenu):
        raise FileNotFoundError(f"Fichier JSON introuvable : {json_contenu}")

    donnees = charger_json(json_contenu)
    print(f"Clés trouvées dans le JSON principal : {list(donnees.keys())}")

    dossier = Path(chemin_template)
    dossier.mkdir(parents=True, exist_ok=True)

    # --- 4. Mise à jour de la page d'informations (auteur) ---
    if os.path.isfile(json_infos):
        try:
            infos = charger_infos_auteur(json_infos)
            if infos:
                ecrire_page_informations(infos)
            else:
                print("⚠️  Aucune information d'auteur trouvée dans le JSON.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de la page d'informations : {e}")
    else:
        print(f"⚠️  Fichier JSON d'informations '{json_infos}' introuvable, page non modifiée.")

    # --- 5. Mise à jour des objectifs ---
    if os.path.isfile(json_infos):
        try:
            data = charger_json(json_infos)
            objectifs_str = data.get("objectifs", "")
            if objectifs_str:
                latex_objectifs = generer_objectifs_latex(objectifs_str)
                lien_objectifs.parent.mkdir(parents=True, exist_ok=True)
                with open(lien_objectifs, 'w', encoding='utf-8') as f:
                    f.write(latex_objectifs)
                print(f"✅ Fichier '{lien_objectifs.name}' généré avec les objectifs.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des objectifs : {e}")

    # --- 6. Mise à jour des liens et ressources ---
    if os.path.isfile(json_infos):
        try:
            data = charger_json(json_infos)
            liens_str = data.get("liens", "")
            ressources_str = data.get("ressources", "")
            if liens_str or ressources_str:
                latex_lr = generer_liens_ressources_latex(liens_str, ressources_str)
                lien_liens_ressources.parent.mkdir(parents=True, exist_ok=True)
                with open(lien_liens_ressources, 'w', encoding='utf-8') as f:
                    f.write(latex_lr)
                print(f"✅ Fichier '{lien_liens_ressources.name}' généré avec liens et ressources.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des liens/ressources : {e}")

    # --- 7. Mise à jour du titre dans retour_aller/titre.tex ---
    if os.path.isfile(json_infos):
        try:
            data = charger_json(json_infos)
            titre_str = data.get("titre", "")
            if titre_str:
                ecrire_fichier_cle(dossier, "titre", titre_str)
                print(f"✅ Fichier 'titre.tex' mis à jour avec le titre.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du titre : {e}")

    print(f"\n✅ Traitement terminé.")


if __name__ == "__main__":
    main()