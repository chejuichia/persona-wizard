#!/bin/bash

# Download SadTalker models using curl instead of wget
mkdir -p ./backend/models/sadtalker/checkpoints
mkdir -p ./backend/models/sadtalker/gfpgan/weights
mkdir -p ./backend/models/sadtalker/config

echo "Downloading SadTalker models..."

# Download main models
curl -L -o ./backend/models/sadtalker/checkpoints/mapping_00109-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar
curl -L -o ./backend/models/sadtalker/checkpoints/mapping_00229-model.pth.tar https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar
curl -L -o ./backend/models/sadtalker/checkpoints/SadTalker_V0.0.2_256.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors
curl -L -o ./backend/models/sadtalker/checkpoints/SadTalker_V0.0.2_512.safetensors https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors

# Download additional required models
curl -L -o ./backend/models/sadtalker/checkpoints/auido2exp_00300-model.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2exp_00300-model.pth
curl -L -o ./backend/models/sadtalker/checkpoints/auido2pose_00140-model.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/auido2pose_00140-model.pth
curl -L -o ./backend/models/sadtalker/checkpoints/epoch_20.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/epoch_20.pth
curl -L -o ./backend/models/sadtalker/checkpoints/facevid2vid_00189-model.pth.tar https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/facevid2vid_00189-model.pth.tar
curl -L -o ./backend/models/sadtalker/checkpoints/shape_predictor_68_face_landmarks.dat https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/shape_predictor_68_face_landmarks.dat
curl -L -o ./backend/models/sadtalker/checkpoints/wav2lip.pth https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/wav2lip.pth

# Download hub models
curl -L -o ./backend/models/sadtalker/checkpoints/hub.zip https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/hub.zip
cd ./backend/models/sadtalker/checkpoints && unzip -o hub.zip && rm hub.zip && cd ../../..

# Download BFM models
curl -L -o ./backend/models/sadtalker/checkpoints/BFM_Fitting.zip https://github.com/Winfredy/SadTalker/releases/download/v0.0.2/BFM_Fitting.zip
cd ./backend/models/sadtalker/checkpoints && unzip -o BFM_Fitting.zip && rm BFM_Fitting.zip && cd ../../..

# Download GFPGAN weights
curl -L -o ./backend/models/sadtalker/gfpgan/weights/alignment_WFLW_4HG.pth https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth
curl -L -o ./backend/models/sadtalker/gfpgan/weights/detection_Resnet50_Final.pth https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth
curl -L -o ./backend/models/sadtalker/gfpgan/weights/GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
curl -L -o ./backend/models/sadtalker/gfpgan/weights/parsing_parsenet.pth https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth

# Copy similarity file
cp sadtalker_reference/src/config/similarity_Lm3D_all.mat ./backend/models/sadtalker/config/

echo "Model download completed!"
