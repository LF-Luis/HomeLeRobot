# Alfred (Automated Liquor Finishing Robotic Enhancement Device)

## Start here
You can find all of our datasets and model checkpoints and follow along with this tutorial in our Hugging Face repo: [https://huggingface.co/dll-hackathon-102025](https://huggingface.co/dll-hackathon-102025)

## Setup the SO-101 leader and follower arms
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
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }" \
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
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader \
    --display_data=true \
    --dataset.repo_id=dll-hackathon-102025/oct_17_6pm \
    --dataset.num_episodes=2 \
    --dataset.single_task="Put orange slice in glass"
```

## SO-101 data collection via teleoperation
```bash
# Test teleoperation and visualize camera feeds in Rerun before recording datasets.
python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader \
    --display_data=true

# Record 50 episodes (10 at a time is easier). 
python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem5AAF2879201 \
    --teleop.id=alfred_leader \
    --display_data=true \
    --dataset.repo_id=dll-hackathon-102025/oct_25_1200pm \
    --dataset.num_episodes=10 \
    --dataset.single_task="put orange slice in glass" \

```

### Tips for data collection
- **Single vs. Dual Camera**: Single camera expects a webcam (front) and dual camera expects both webcam (front) and wrist camera (wrist). You can't do single camera config with only wrist camera.
- **Camera Resolution**: Scripts work best with 640x480 resolution for both webcam and wrist camera due to resizing and downsampling hardcoding.
- **Wrist Camera**: Make sure when an episode starts, the wrist camera can see the object in the scene. We think it heavily relies on the wrist camera to know what to do next.
- **Episode Management**: 
  - Left Arrow (←): Discard and re-record the current episode if something went wrong
  - Right Arrow (→): Finish current episode and prepare for the next one
  - ESC: Stop recording session and begin encoding/uploading
- **Best Practices**:
  - Record 10 episodes at a time to make the process more manageable
  - Maintain consistent camera angles and lighting across episodes
  - Ensure the scene is reset to the initial state before starting each new episode
  - Vary the starting positions and background props slightly to improve model generalization

## Fine-tuning Nvidia's GR00T N1.5 on 50 episodes of data.
If you don't have one, create a W&B account ahead of time to view live training metrics.  

Below are reproducible steps to fine-tune GR00T on a Lambda VM (We used an 1xA100 40 GB).

```bash
# Setup Lambda machine
bash hack_code/ai_vm_setup.sh
# Activate env
conda activate gr00t
# Fast download datasets (NOTE: Use "single" or "dual" cam setup)
python /home/ubuntu/hack_code/get_hf_data.py \
    --datasets dll-hackathon-102025/oct_25_1200pm \
               dll-hackathon-102025/oct_25_1210pm \
               dll-hackathon-102025/oct_25_1215pm \
               dll-hackathon-102025/oct_25_1225pm \
    --base_dir /home/ubuntu/train_dataset/ \
    --cam dual

# Finetune dual-cam setup
python scripts/gr00t_finetune.py \
    --dataset-path /home/ubuntu/train_dataset/oct_25_1200pm \
    --dataset-path /home/ubuntu/train_dataset/oct_25_1210pm \
    --dataset-path /home/ubuntu/train_dataset/oct_25_1215pm \
    --dataset-path /home/ubuntu/train_dataset/oct_25_1225pm \
    --num-gpus 1 \
    --output-dir /home/ubuntu/model_ft_output \
    --max-steps 10000 \
    --data-config so100_dualcam \
    --video-backend torchvision_av

# Eval checkpoint with an evaluation set (do not use this dataset in training)
python scripts/eval_policy.py --plot \
    --model_path /home/ubuntu/model_ft_output/checkpoint-10000 \
    --dataset-path /home/ubuntu/train_dataset/oct_19_430pm \
    --embodiment-tag new_embodiment \
    --data-config so100_dualcam \
    --video-backend torchvision_av \
    --modality-keys single_arm gripper \
    --save_plot_path "/home/ubuntu/plots/ckp_4000.png"

# Upload model checkpoint to HF, matching GR00T N1.5 format so that we can easily use model with other GR00T scripts.  
conda activate gr00t
hf auth login
python upload_model_to_hf.py /home/ubuntu/model_ft_output/checkpoint-10000 dll-hackathon-102025/gr00t_n1.5-toothpick-test ckpt-10000

# To upload all checkpoints for debugging:
python upload_model_to_hf.py /home/ubuntu/model_ft_output dll-hackathon-102025/gr00t_n1.5-pickup-orange-test
```

### Tips for Fine-tuning
- **Best Practices**:
  - We fine-tuned up to 10,000 steps for our checkpoint because we followed Nvidia's successful example and it seems to work for us.

## Running fine-tuned model on SO-101 arms
```bash
# Optional: Set up Lambda VM. If you have a local PC you can skip these steps.
# Setup Lambda machine
bash hack_code/ai_vm_setup.sh
# Activate env
conda activate gr00t

# Download model checkpoing from Hugging Face.
huggingface-cli download \
    dll-hackathon-102025/gr00t_n1.5-oct-25-ft-orange \
    --include "checkpoint-10000/*" \
    --local-dir ./checkpoints/gr00t_n1.5-oct-25-ft-orange

# Kick off policy server.
cd Isaac-GR00T/
python scripts/inference_service.py \
    --model_path /home/ubuntu/Isaac-GR00T/checkpoints/gr00t_n1.5-oct-25-ft-orange/checkpoint-10000 \
    --server \
    --data_config so100_dualcam \
    --embodiment_tag new_embodiment \
    --port 5555 \
    --host 0.0.0.0
    --denoising-steps 4

# Optional: If you're running a Lambda VM, you need to open a new window that forwards commands from your local inference to policy server running on Lambda.
ssh -i lisa-nvidia-hackathon.pem ubuntu@[your-lambda-ip-here]

# Run inference
cd Isaac-GR00T/examples/SO-100
conda activate gr00t
python eval_lerobot.py \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem5A7C1186671 \
    --robot.id=alfred_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 0, width: 640,  height: 480, fps: 30} }" \
    --policy_host=localhost \
    --policy_port=5555 \
    --lang_instruction="put orange slice in glass" \

```
## Results
One old-fashioned, coming right up!

<details>
<summary><strong>Resources/References</strong></summary>

- [GR00T-N1.5-3B HF](https://huggingface.co/nvidia/GR00T-N1.5-3B)
- [Post-Training Isaac GR00T N1.5 for LeRobot SO-101 Arm](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning)
- [HF LeRobot SO-101 Docs](https://huggingface.co/docs/lerobot/so101)
- [LeIsaac GH](https://github.com/LightwheelAI/leisaac/tree/main)

</details>