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

## Installation

```bash
git clone https://github.com/votre-org/autogenerate_cer_bot.git
cd autogenerate_cer_bot
pip install -r requirements.txt