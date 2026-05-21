import os
from huggingface_hub import snapshot_download

script_dir = os.path.dirname(os.path.abspath(__file__))

local_storage = os.path.join(script_dir, "foundation_model")

print(f"Téléchargement du modele vers : {local_storage}")
snapshot_download(
    repo_id="jpacifico/Chocolatine-2-4B-Instruct-DPO-v2.1-Q4_K_M-GGUF",
    local_dir=local_storage,
    local_dir_use_symlinks=False,
)

print("Téléchargement terminer !")