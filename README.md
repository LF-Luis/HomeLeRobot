# Repo Name

`https://docs.google.com/document/d/1WJGbU4o9SW0a0QvtKFXR3vv9AS1Db5fBztyG6jGkbsY`
`https://huggingface.co/dll-hackathon-102025`

## Setup
- [Configure Motors](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning)
- [Teleop](https://huggingface.co/docs/lerobot/getting_started_real_world_robot#teleoperate)
- [Record dataset](https://huggingface.co/docs/lerobot/getting_started_real_world_robot#record-a-dataset)
```bash
# Install LeRobot: https://huggingface.co/docs/lerobot/installation
# Find your port (one arm at a time)
# E.g. you'll get
#    Leader:   '/dev/tty.usbmodem5AAF2879201'
#    Follower: '/dev/tty.usbmodem5A7C1186671'
python lerobot/find_port.py
# Setup motors (follower and leader)
python -m lerobot.setup_motors \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671
# Setup motors (follower and leader)
python -m lerobot.calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower
# Teleop with no cameras
python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader

# For our specific LeRobot calibration, our calibration file is in 
# the repo's `assets` dir. 
# cp -r assets/calibration ~/.cache/huggingface/lerobot/

# Find your camera
# Try on cam at a time, your iphone and mac will appear first showing 30 fps, the wrist and front cams will appear once you plug them in
lerobot-find-cameras opencv
# Teleop with camera
python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 1920, height: 1080, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30} }" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader \
    --display_data=true

# Log in to HF
huggingface-cli login --token ${HUGGINGFACE_TOKEN} --add-to-git-credential
# Record data to HF
# Press Right Arrow (→): Early stop the current episode or reset time and move to the next.
# Press Left Arrow (←): Cancel the current episode and re-record it.
# Press Escape (ESC): Immediately stop the session, encode videos, and upload the dataset.
python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 1920, height: 1080, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30} }" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader \
    --display_data=true \
    --dataset.repo_id=dll-hackathon-102025/oct_17_6pm \
    --dataset.num_episodes=2 \
    --dataset.single_task="Put orange slice in glass"
```

## Fine-Tuning
If you don't have one, create a W&B account ahead of time to view live training metrics.  

Below are reproducible steps to fine-tune GR00T on a Lambda VM (I used an 1xA100 40 GB).

```bash
# Setup Lambda machine
bash hack_code/ai_vm_setup.sh
# Activate env
conda activate gr00t
# Fast download datasets (NOTE: Use "single" or "dual" cam setup)
python /home/ubuntu/hack_code/get_hf_data.py \
    --datasets dll-hackathon-102025/drew-01 \
               dll-hackathon-102025/luis-02 \
    --base_dir /home/ubuntu/train_dataset/ \
    --cam single
# Finetune single-cam setup
python scripts/gr00t_finetune.py \
    --dataset-path /home/ubuntu/train_dataset/drew-01 \
    --dataset-path /home/ubuntu/train_dataset/luis-02 \
    --num-gpus 1 \
    --output-dir /home/ubuntu/model_ft_output \
    --max-steps 10000 \
    --data-config so100 \
    --video-backend torchvision_av
# Finetune dual-cam setup
python scripts/gr00t_finetune.py \
    --dataset-path /home/ubuntu/train_dataset/drew-01 \
    --dataset-path /home/ubuntu/train_dataset/luis-02 \
    --num-gpus 1 \
    --output-dir /home/ubuntu/model_ft_output \
    --max-steps 10000 \
    --data-config so100_dualcam \
    --video-backend torchvision_av

# Eval checkpoint with an evaluation set (do not use this dataset in training)
python scripts/eval_policy.py --plot \
    --model_path /home/ubuntu/model_ft_output/checkpoint-4000 \
    --dataset-path /home/ubuntu/train_dataset/oct_19_430pm \
    --embodiment-tag new_embodiment \
    --data-config so100_dualcam \
    --video-backend torchvision_av \
    --modality-keys single_arm gripper \
    --save_plot_path "/home/ubuntu/plots/ckp_4000.png"
```

## Upload model to HF
Upload model checkpoint to HF, matching GR00T N1.5 format so that we can easily use model with other GR00T scripts.  
```bash
conda activate gr00t
hf auth login
python upload_model_to_hf.py /home/ubuntu/model_ft_output/checkpoint-2000 dll-hackathon-102025/gr00t_n1.5-toothpick-test ckpt-2000

# To upload all checkpoints for debugging:
python upload_model_to_hf.py /home/ubuntu/model_ft_output dll-hackathon-102025/gr00t_n1.5-pickup-orange-test
```

## LeRobot in Isaac Sim
- Dockerfile TODOs
    [ ] pip install source/isaaclab_rl
        - `/isaac-sim/python.sh -m pip install -e source/isaaclab_rl`
        [ ] WARN: Added it in Dockerfile but didn't seem to install
    [x] map /isaac-sim/python.sh to python and python3 in runtime env
    - Figure out if ./isaaclab.sh --install is needed or what minimal version of it works for us
        - Bug: https://github.com/isaac-sim/IsaacLab/issues/3037
            - Fix: Comment this out: https://github.com/isaac-sim/IsaacLab/blob/90b79bb2d44feb8d833f260f2bf37da3487180ba/isaaclab.sh#L279-L295
            - Run: `./isaaclab.sh --install`
    [ ] Add Isaac Sim/Lab cache to compose file
    [ ] For real env, try to match intrinsic/extrinsic of 2nd cam in so100_dualcam
        - May not be possible, and we most likely are at a disadvantage bc of the wrist cam that comes with LeRobot

### Container -- First Time Setup
First time setup, and anytime you need to rebuild:
```bash
xhost +local:root
docker compose -f docker-compose.lerobot_isaac.yml build
docker compose -f docker-compose.lerobot_isaac.yml up -d
docker exec -it lerobot_isaac_dev /bin/bash
# FIXME: Add to Dockerfile:
# FIXME: Get away from building inside of LightwheelAI/leisaac and build in our own src/ dir
git clone https://github.com/LightwheelAI/leisaac.git
cd leisaac
/isaac-sim/python.sh -m pip install -e source/leisaac
/isaac-sim/python.sh -m pip install -e "source/leisaac[gr00t]"  # FIXME: Add to Dockerfile
cd /workspace/IsaacLab
/isaac-sim/python.sh -m pip install -e source/isaaclab_rl
# If you get errors running these pip installs that's fine, there's some bug there
```

### Container -- Common flow
```bash
# Allow full access to GUI
xhost +local:root
# Start container
docker compose -f docker-compose.lerobot_isaac.yml up -d
# Open interactive shell to container
docker exec -it lerobot_isaac_dev /bin/bash
# Tear down container
docker compose -f docker-compose.lerobot_isaac.yml down
```

### Running Teleop (keyboard or using Leader Arm)
First download assets:
```bash
# FIXME: Add to Dockerfile:
# https://github.com/LightwheelAI/leisaac/releases/tag/v0.1.0
wget https://github.com/LightwheelAI/leisaac/releases/download/v0.1.0/so101_follower.usd
wget https://github.com/LightwheelAI/leisaac/releases/download/v0.1.0/kitchen_with_orange.zip
```
Place them under `leisaac` repo like so:
```bash
leisaac/assets/
├── robots/
│   └── so101_follower.usd
└── scenes/
    └── kitchen_with_orange/
        ├── scene.usd
        ├── assets
        └── objects/
            ├── Orange001
            ├── Orange002
            ├── Orange003
            └── Plate
```

Keyboard teleop:
```bash
# On a good GPU, with plenty of CPU cores:
/isaac-sim/python.sh scripts/environments/teleoperation/teleop_se3_agent.py \
    --task=LeIsaac-SO101-PickOrange-v0 \
    --teleop_device=keyboard \
    --num_envs=1 \
    --device=cuda \
    --enable_cameras \
    --dataset_file=./datasets/dataset.hdf5

# Temp workaround for a T4:
/isaac-sim/python.sh scripts/environments/teleoperation/teleop_se3_agent.py \
    --task=LeIsaac-SO101-PickOrange-v0 \
    --teleop_device=keyboard \
    --num_envs=1 \
    --device=cuda \
    --enable_cameras \
    --record \
    --dataset_file=./datasets/dataset.hdf5
    -- \
    --/rtx/reflections/enabled=false \
    --/rtx/indirectDiffuse/enabled=false \
    --/rtx/ambientOcclusion/enabled=false \
    --/app/asyncRendering=false
```

Other helpful scripts:
```bash
/isaac-sim/python.sh scripts/environments/list_envs.py
```

## GR00T N1.5
Setup:
```bash
docker compose -f docker-compose.gr00t_n1_5.yml build
docker compose -f docker-compose.gr00t_n1_5.yml up -d
docker exec -it gr00t_dev /bin/bash
```

## LeRobot in Isaac + GR00T N1.5 Model-Inference Service
Run GR00T N1.5 model inference:
https://github.com/NVIDIA/Isaac-GR00T?tab=readme-ov-file#4-evaluation
```text
> EmbodimentTag.GR1: Designed for humanoid robots with dexterous hands using absolute joint space control
> EmbodimentTag.OXE_DROID: Optimized for single arm robots using delta end-effector (EEF) control
> EmbodimentTag.AGIBOT_GENIE1: Built for humanoid robots with grippers using absolute joint space control
```
```bash
# https://github.com/NVIDIA/Isaac-GR00T?tab=readme-ov-file#4-evaluation
docker exec -it gr00t_dev /bin/bash
python scripts/inference_service.py --server \
    --model-path nvidia/GR00T-N1.5-3B \
    --embodiment-tag oxe_droid \
    --data-config oxe_droid \
    --port 5555
```
Note: When running in real SO robot we'll use `--data-config so100`

- Run LeIsaac being driven by model inference service:
```bash
# On a good GPU, with plenty of CPU cores:
/isaac-sim/python.sh scripts/evaluation/policy_inference.py \
    --task=LeIsaac-SO101-PickOrange-v0 \
    --eval_rounds=10 \
    --policy_type=gr00tn1.5 \
    --policy_host=localhost \
    --policy_port=5555 \
    --policy_timeout_ms=5000 \
    --policy_action_horizon=16 \
    --policy_language_instruction="Pick up the orange and place it on the plate" \
    --device=cuda \
    --enable_cameras

# If your machine struggles run this instead
/isaac-sim/python.sh scripts/evaluation/policy_inference.py \
    --task=LeIsaac-SO101-PickOrange-v0 \
    --eval_rounds=10 \
    --policy_type=gr00tn1.5 \
    --policy_host=localhost \
    --policy_port=5555 \
    --policy_timeout_ms=5000 \
    --policy_action_horizon=16 \
    --policy_language_instruction="Pick up the orange and place it on the plate" \
    --device=cuda \
    --enable_cameras
    -- \
    --/rtx/reflections/enabled=false \
    --/rtx/indirectDiffuse/enabled=false \
    --/rtx/ambientOcclusion/enabled=false \
    --/app/asyncRendering=false
```


<details>
<summary><strong>Resources/References</strong></summary>

- [GR00T-N1.5-3B HF](https://huggingface.co/nvidia/GR00T-N1.5-3B)
- [Post-Training Isaac GR00T N1.5 for LeRobot SO-101 Arm](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning)
- [HF LeRobot SO-101 Docs](https://huggingface.co/docs/lerobot/so101)
- [LeIsaac GH](https://github.com/LightwheelAI/leisaac/tree/main)

</details>