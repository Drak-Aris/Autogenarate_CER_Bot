import os
import json
import re
import requests
from pathlib import Path
import pypandoc

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

coeurs_logiques = os.cpu_count() or 4  # 4 par défaut si la détection échoue
coeurs_physiques = max(1, coeurs_logiques // 2)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "foundation_model_latex/qwen2.5-coder-3b-instruct-q4_k_m.gguf")
N_CTX = 16384
MAX_TOKENS_GEN = N_CTX - 1000

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
    lignes_data = objectifs_str.strip().split('\n')
    if len(lignes_data) < 2:
        return "% Aucun objectif fourni.\n"

    lignes_competences = lignes_data[1:]
    blocs = []
    competence_courante = None
    items_courant = []

    for ligne in lignes_competences:
        if '\t' in ligne:
            if competence_courante is not None and items_courant:
                items_latex = '\n'.join(f'    \\item {item}' for item in items_courant)
                blocs.append(
                    f'\\textbf{{{competence_courante}}} &\n'
                    f'\\begin{{itemize}}[leftmargin=1.1cm,itemsep=0.2em]\n'
                    f'{items_latex}\n'
                    f'\\end{{itemize}}\\\\\n'
                )
            parts = ligne.split('\t', 1)
            competence_courante = parts[0].strip()
            details = parts[1].strip()
            items_raw = re.split(r'\s*•\s*', details)
            items_courant = [it.strip().rstrip(';') for it in items_raw if it.strip()]
        else:
            items_raw = re.split(r'\s*•\s*', ligne)
            for it in items_raw:
                it = it.strip().rstrip(';')
                if it:
                    items_courant.append(it)

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


def traitement_markdown_tables(md_text: str) -> str:
    """
    Intercepte les tableaux Markdown et les convertit en LaTeX personnalisé (tab-list).
    """
    pattern = re.compile(r'((?:^\|.*\|\s*?\n)+)', re.MULTILINE)

    def remplacer_tableau(match):
        lignes = match.group(1).strip().split('\n')
        if len(lignes) < 3:
            return match.group(0)

        def nettoyer_cellules(ligne):
            ligne = ligne.strip()
            if ligne.startswith('|'): ligne = ligne[1:]
            if ligne.endswith('|'): ligne = ligne[:-1]
            return [c.strip().replace('**', '') for c in ligne.split('|')]

        entetes = nettoyer_cellules(lignes[0])
        nb_cols = len(entetes)

        format_cols = '|' + '|'.join(['C'] * nb_cols) + '|'
        latex = f"\n\n\\begin{{tab-list}}{{{format_cols}}}\n\\hline\n"

        latex_entetes = " & ".join([f"\\textbf{{{c}}}" for c in entetes])
        latex += f"{latex_entetes} \\\\\n\\hline\n"

        for ligne in lignes[2:]:
            cellules = nettoyer_cellules(ligne)
            while len(cellules) < nb_cols:
                cellules.append("")

            cellules_formattees = []
            for c in cellules:
                c = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', c)
                c = re.sub(r'\*(.*?)\*', r'\\textit{\1}', c)
                cellules_formattees.append(c)

            latex += " & ".join(cellules_formattees[:nb_cols]) + " \\\\\n\\hline\n"

        latex += "\\end{tab-list}\n\n"
        return latex

    return pattern.sub(remplacer_tableau, md_text)


def nettoyer_latex_final(latex_text: str) -> str:
    """Nettoie en profondeur les résidus de Pandoc et corrige la syntaxe."""
    # 1. Capture \texorpdfstring{Contenu}{Alternative} de manière robuste avec accolades imbriquées
    # Permet de cibler \texorpdfstring{\textbf{Texte}}{Texte} sans casser l'expression
    latex_text = re.sub(r'\\texorpdfstring\{((?:[^{}]|\{[^{}]*\})+)\}\{(?:[^{}]|\{[^{}]*\})+\}', r'\1', latex_text)

    # 2. Supprime proprement tous les \label{...} générés par Pandoc
    latex_text = re.sub(r'\\label\{.*?\}', '', latex_text)

    return latex_text


def convertir_markdown_vers_latex(contenu_markdown: str) -> str:
    """
    Pipeline de conversion robuste : Pré-traitement -> Pandoc -> Post-traitement.
    """
    try:
        # Étape 1 : Intercepter et formater les tableaux Markdown
        md_modifie = traitement_markdown_tables(contenu_markdown)

        # Étape 2 : Conversion via Pandoc
        latex_genere = pypandoc.convert_text(
            md_modifie,
            'latex',
            format='md'
        )

        # Étape 3 : Nettoyage des chaînes hexadécimales et texorpdfstring
        latex_propre = nettoyer_latex_final(latex_genere)

        return latex_propre
    except Exception as e:
        print(f"Erreur lors de la conversion : {e}")
        return ""


def decouper_markdown(contenu: str) -> list:
    sections_brutes = re.split(r'(?=\n---|(?:\n|^)### )', contenu)
    sections = [sec.strip() for sec in sections_brutes if sec.strip()]
    return sections


def main():
    if not os.path.isfile(json_contenu):
        raise FileNotFoundError(f"Fichier JSON introuvable : {json_contenu}")

    donnees = charger_json(json_contenu)
    print(f"Clés trouvées dans le JSON principal : {list(donnees.keys())}")

    dossier = Path(chemin_template)
    dossier.mkdir(parents=True, exist_ok=True)

    # --- 1. Traitement des clés du JSON ---
    for cle, texte in donnees.items():
        if cle in key_ignore:
            print(f"⏭️  Clé ignorée : '{cle}'")
            continue
        if not isinstance(texte, str):
            print(f"⚠️  La valeur pour la clé '{cle}' n'est pas une chaîne, ignorée.")
            continue
        contenu_formate = formater_contenu(texte)
        ecrire_fichier_cle(dossier, cle, contenu_formate)

    # --- 2. Mise à jour de etudes.tex ---
    if os.path.isfile(markdown_source):
        try:
            md_content = charger_contenu_markdown(markdown_source)
            dossier_plan_action.mkdir(parents=True, exist_ok=True)

            print("Conversion du Markdown en LaTeX (Méthode par règles strictes)...")
            contenu_complet_latex = convertir_markdown_vers_latex(md_content)

            chemin_etude = dossier_plan_action / "etudes.tex"
            with open(chemin_etude, 'w', encoding='utf-8') as f:
                f.write(contenu_complet_latex)

            print(f"✅ Fichier '{chemin_etude.name}' généré avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de l'étude : {e}")
    else:
        print(f"⚠️  Fichier markdown '{markdown_source}' introuvable, étude non modifiée.")

    # --- 3. Définitions et pistes ---
    if os.path.isfile(json_recherche):
        try:
            definitions = charger_definitions(json_recherche)
            if definitions:
                ecrire_definitions(definitions)
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des définitions : {e}")
        try:
            pistes = charger_pistes(json_recherche)
            if pistes:
                ecrire_pistes_evaluees(pistes)
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des pistes : {e}")

    # --- 4. Page d'informations ---
    if os.path.isfile(json_infos):
        try:
            infos = charger_infos_auteur(json_infos)
            if infos:
                ecrire_page_informations(infos)
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de la page d'informations : {e}")

    # --- 5. Objectifs ---
    if os.path.isfile(json_infos):
        try:
            data = charger_json(json_infos)
            objectifs_str = data.get("objectifs", "")
            if objectifs_str:
                latex_objectifs = generer_objectifs_latex(objectifs_str)
                lien_objectifs.parent.mkdir(parents=True, exist_ok=True)
                with open(lien_objectifs, 'w', encoding='utf-8') as f:
                    f.write(latex_objectifs)
                print(f"✅ Fichier '{lien_objectifs.name}' généré.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des objectifs : {e}")

    # --- 6. Liens et ressources ---
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
                print(f"✅ Fichier '{lien_liens_ressources.name}' généré.")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des liens/ressources : {e}")

    # --- 7. Titre ---
    if os.path.isfile(json_infos):
        try:
            data = charger_json(json_infos)
            titre_str = data.get("titre", "")
            if titre_str:
                ecrire_fichier_cle(dossier, "titre", titre_str)
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du titre : {e}")

    print(f"\n✅ Traitement terminé.")


if __name__ == "__main__":
    main()