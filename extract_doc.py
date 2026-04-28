import os
import re
import subprocess
from pathlib import Path

heading_title = [
    "mots cles",
    "contexte",
    "besoins",
    "problematiques",
    "contraintes",
    "generalisation",
    "pistes de solutions",
    "plan d'action"
]

title_mapping = {
    "mots cles": "mots cles",
    "mot cles": "mots cles",
    "mot cle": "mots cles",

    "contexte": "contexte",

    "besoins": "besoins",
    "besoin": "besoins",

    "problematiques": "problematiques",
    "problematique": "problematiques",

    "contraintes": "contraintes",
    "contrainte": "contraintes",

    "generalisation": "generalisation",

    "pistes de solutions": "pistes de solutions",
    "pistes de solution": "pistes de solutions",

    "plan d'action": "plan d'action",
    "plan d action": "plan d'action",
    "plan daction": "plan d'action"
}

def normalization(text):
    text = text.lower().strip()
    text = re.sub(r'[éè]', 'e', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^\w\s\'-]', '', text)
    return text

def clean_heading(line):
    line = line.strip()
    line = re.sub(r'^[\d\.\-•\(\)]+\s*', '', line)
    line = re.sub(r'^[IVXLCDM]+\.\s*', '', line)
    return line.strip()

def get_raw_text(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            raise Exception("python-docx not installed. Please install it: pip install python-docx")
        except Exception as e:
            raise Exception(f"Error reading .docx: {e}")
    elif ext == '.doc':
        try:
            result = subprocess.run(['catdoc', file_path], capture_output=True, text=True, check=True)
            return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            raise Exception("catdoc not available. Please install it: sudo apt install catdoc")
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def parse_text_sections(text):
    lines = text.splitlines()
    sections = {h: [] for h in heading_title}
    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        cleaned = clean_heading(stripped)
        normalized_cleaned = normalization(cleaned)

        matched = False
        for variant, std_key in title_mapping.items():
            norm_variant = normalization(variant)
            if normalized_cleaned == norm_variant:
                current_section = std_key
                matched = True
                break

        if matched:
            continue

        if current_section:
            sections[current_section].append(stripped)

    return sections

def extract_sections(file_path):
    raw_text = get_raw_text(file_path)
    return parse_text_sections(raw_text)

def main():
    file_path = ""

    if not os.path.isfile(file_path):
        print(f"Error: file '{file_path}' does not exist.")
        return

    try:
        sections = extract_sections(file_path)
    except Exception as e:
        print(f"\nErreur lors de l'extraction des sections : {e}")
        return

    print("\n" + "=" * 60)
    print("RÉSULTAT DE L'EXTRACTION DES SECTIONS")
    print("=" * 60)
    for heading in heading_title:
        content = sections.get(heading, [])
        print(f"\n--- {heading.upper()} ---")
        if not content:
            print("(aucun contenu trouvé)")
        else:
            for line in content:
                print(line)
    print("\n" + "=" * 60)