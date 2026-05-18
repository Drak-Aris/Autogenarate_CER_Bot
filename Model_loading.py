import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def charger_modele_et_tokenizer(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Dossier modèle introuvable : {model_path}")

    print("Chargement du tokenizer et du modèle Qwen2.5-7B-Instruct...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    if torch.cuda.is_available():
        # ----- MODE GPU -----
        device = "cuda"
        print(f"Périphérique utilisé : {device}")
        torch_dtype = torch.float16
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
            device_map="auto",       # répartit automatiquement sur les GPU disponibles
            trust_remote_code=True
        )
    else:
        # ----- MODE CPU (fallback) -----
        device = "cpu"
        print(f"Périphérique utilisé : {device} (GPU non détecté)")
        torch_dtype = torch.float32  # obligatoire sur CPU
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
            device_map={"": device},    # tout est mis sur le CPU
            low_cpu_mem_usage=True,     # réduit le pic mémoire au chargement
            trust_remote_code=True
        )

    model.eval()
    print("Modèle chargé avec succès.")
    return tokenizer, model, device