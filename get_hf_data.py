from pathlib import Path
import argparse, os, multiprocessing, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from huggingface_hub import snapshot_download

"""
Hardcoded script meant to work in a Lambda (or other bare-metal) GPU,
in dir /home/ubuntu, with groot repo in /home/ubuntu/Isaac-GR00T.

This script will quickly download multiple datasets and add the correct *modality.json file to them.
"""

SO100_single_cam_cfg = "/home/ubuntu/Isaac-GR00T/examples/SO-100/so100__modality.json"
SO100_dual_cam_cfg = "/home/ubuntu/Isaac-GR00T/examples/SO-100/so100_dualcam__modality.json"

def download_dataset(repo_id, base_dir):
    out_dir = Path(base_dir) / repo_id.split("/")[-1]
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=repo_id, repo_type="dataset", local_dir=str(out_dir))
    return repo_id, out_dir

def copy_modality_config(dataset_dir, cam_type):
    meta_dir = Path(dataset_dir) / "meta"
    config_file = SO100_single_cam_cfg if cam_type == "single" else SO100_dual_cam_cfg
    shutil.copy2(config_file, meta_dir / "modality.json")

def main():
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

    p = argparse.ArgumentParser()
    p.add_argument("--datasets", nargs="+", required=True)
    p.add_argument("--base_dir", required=True)
    p.add_argument("--cam", choices=["single", "dual"], required=True)
    args = p.parse_args()

    base_dir = Path(args.base_dir); base_dir.mkdir(parents=True, exist_ok=True)
    workers = min(len(args.datasets), multiprocessing.cpu_count())
    print(f"Downloading {len(args.datasets)} dataset(s) with {workers} threads...")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(download_dataset, ds, base_dir) for ds in args.datasets]
        for f in as_completed(futures):
            repo_id, out_dir = f.result()
            copy_modality_config(out_dir, args.cam)
            print(f"DONE: {repo_id} -> {out_dir}")

if __name__ == "__main__":
    main()
