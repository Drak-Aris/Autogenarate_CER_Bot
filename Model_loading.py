import os

model_path = "foundation_modele"

def charger_modele_et_tokenizer(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Dossier modèle introuvable : {model_path}")

    print("Chargement du tokenizer et du modèle Qwen2.5-7B-Instruct...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    # Choix du périphérique
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Périphérique utilisé : {device}")

    # Chargement optimisé : float16 sur GPU, float32 sur CPU (très lent !)
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch_dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )
    if device == "cpu":
        model = model.to(device)
    model.eval()
    return tokenizer, model, device