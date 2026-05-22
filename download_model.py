import os
from huggingface_hub import snapshot_download

script_dir = os.path.dirname(os.path.abspath(__file__))

local_storage = os.path.join(script_dir, "foundation_model_latex")

print(f"Téléchargement du modele vers : {local_storage}")
snapshot_download(
    repo_id="Maites/Qwen2.5-Coder-3B-Instruct-Q4_K_M-GGUF",
    local_dir=local_storage,
    local_dir_use_symlinks=False,
)
print("Téléchargement terminer !")