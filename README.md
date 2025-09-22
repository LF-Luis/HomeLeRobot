# Repo Name

## LeRobot in Isaac Sim
- Dockerfile TODOs
    - pip install source/isaaclab_rl
        - `/isaac-sim/python.sh -m pip install -e source/isaaclab_rl`
    - map /isaac-sim/python.sh to python and python3 in runtime env
    - Figure out if ./isaaclab.sh --install is needed or what minimal version of it works for us
        - Bug: https://github.com/isaac-sim/IsaacLab/issues/3037
            - Fix: Comment this out: https://github.com/isaac-sim/IsaacLab/blob/90b79bb2d44feb8d833f260f2bf37da3487180ba/isaaclab.sh#L279-L295
            - Run: `./isaaclab.sh --install`

### Container -- First Time Setup
First time setup, and anytime you need to rebuild:
```bash
xhost +local:root
docker compose -f docker-compose.lerobot_isaac.yml build
docker compose -f docker-compose.lerobot_isaac.yml up -d
docker exec -it lerobot_isaac_dev /bin/bash
# FIXME: Get away from building inside of LightwheelAI/leisaac and build in our own src/ dir
git clone https://github.com/LightwheelAI/leisaac.git
cd leisaac
/isaac-sim/python.sh -m pip install -e source/leisaac
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

## Setup GR00T N1.5 Local Model-Inference Service

**NOTE: I have not tried these steps yet:**
- Create docker container using Dockerfile from here: https://github.com/NVIDIA/Isaac-GR00T
- Run GR00T N1.5 model inference:
    ```bash
    python scripts/inference_service.py --server \
        --model-path nvidia/GR00T-N1.5-3B \
        --embodiment-tag oxe_droid \
        --data-config so100 \
        --port 5555
    ```
- Run LeIsaac being driven by model inference service:
    ```bash
    python scripts/evaluation/policy_inference.py \
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
    ```
