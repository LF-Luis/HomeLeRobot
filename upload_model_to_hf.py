import sys
from pathlib import Path

from huggingface_hub import upload_folder


"""
Uploads a model checkpoint folder (with experiment_cfg, config.json, safetensors, etc.)
to a HF model repo. Keeps layout identical to GR00T N1.5 repo: https://huggingface.co/nvidia/GR00T-N1.5-3B/tree/main

Usage, first time:
python upload_model_to_hf.py /home/ubuntu/model_ft_output/checkpoint-2000 dll-hackathon-102025/gr00t_n1.5-toothpick-test

Usage, new checkpoint:
python upload_model_to_hf.py /home/ubuntu/model_ft_output/checkpoint-2000 dll-hackathon-102025/gr00t_n1.5-toothpick-test ckpt-2000
"""

def upload_checkpoint(checkpoint_path: str, repo_id: str, revision: str = "main"):
    ckpt = Path(checkpoint_path)
    if not ckpt.exists():
        raise ValueError(f"Checkpoint path not found: {ckpt}")
    # Make sure required files exist
    required_files = ["config.json", "model.safetensors.index.json"]
    for f in required_files:
        if not (ckpt / f).exists():
            print(f"Warning: missing {f} in {ckpt}")
    # Remove unnecessary training artifacts
    ignored = ["optimizer.pt", "scheduler.pt", "trainer_state.json", "rng_state_*.pth", "runs"]
    for pat in ignored:
        for f in ckpt.glob(pat):
            print(f"Skipping training artifact: {f.name}")
    print(f"Uploading {ckpt} to {repo_id} ({revision})")
    upload_folder(
        folder_path=str(ckpt),
        repo_id=repo_id,
        repo_type="model",
        revision=revision,
        commit_message=f"Upload {ckpt.name}",
        ignore_patterns=ignored,
    )
    print("Upload complete.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_hf.py <checkpoint_path> <repo_id> [revision]")
        sys.exit(1)

    checkpoint_path = sys.argv[1]
    repo_id = sys.argv[2]
    revision = sys.argv[3] if len(sys.argv) > 3 else "main"

    upload_checkpoint(checkpoint_path, repo_id, revision)
