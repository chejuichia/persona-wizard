#!/bin/bash

# Script to download SadTalker models with correct URLs
# Based on the official SadTalker repository

echo "Downloading SadTalker models..."

# Create directories
mkdir -p ~/.sadtalker/checkpoints
mkdir -p ~/.sadtalker/config

# Change to checkpoints directory
cd ~/.sadtalker/checkpoints

echo "Downloading model files..."

# Download the new SadTalker models (v0.0.2-rc)
curl -L -o mapping_00109-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar
curl -L -o mapping_00229-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar
curl -L -o SadTalker_V0.0.2_256.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors
curl -L -o SadTalker_V0.0.2_512.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors

# Download legacy models from the old repository
curl -L -o auido2exp_00300-model.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2exp_00300-model.pth
curl -L -o auido2pose_00140-model.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2pose_00140-model.pth
curl -L -o epoch_20.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/epoch_20.pth
curl -L -o facevid2vid_00189-model.pth.tar https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/facevid2vid_00189-model.pth.tar
curl -L -o wav2lip.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/wav2lip.pth
curl -L -o shape_predictor_68_face_landmarks.dat https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/shape_predictor_68_face_landmarks.dat

# Download BFM (Basel Face Model) - this is a larger file
echo "Downloading BFM model (this may take a while)..."
curl -L -o BFM_Fitting.zip https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/BFM_Fitting.zip
unzip -o BFM_Fitting.zip
rm BFM_Fitting.zip

# Download hub models
echo "Downloading hub models..."
curl -L -o hub.zip https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/hub.zip
unzip -o hub.zip
rm hub.zip

# Change to config directory
cd ~/.sadtalker/config

echo "Downloading config files..."

# Download config files from the main repository
curl -L -o auido2pose.yaml https://raw.githubusercontent.com/OpenTalker/SadTalker/main/src/audio2pose/config/auido2pose.yaml
curl -L -o auido2exp.yaml https://raw.githubusercontent.com/OpenTalker/SadTalker/main/src/audio2exp/config/auido2exp.yaml
curl -L -o facerender_still.yaml https://raw.githubusercontent.com/OpenTalker/SadTalker/main/src/facerender/config/facerender_still.yaml

echo "✅ SadTalker models downloaded successfully!"
echo "Models are located in: ~/.sadtalker/checkpoints"
echo "Config files are located in: ~/.sadtalker/config"

# Verify downloads
echo ""
echo "Verifying downloads..."
ls -la ~/.sadtalker/checkpoints/
echo ""
ls -la ~/.sadtalker/config/
