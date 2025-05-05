"""Конфиг для GFPGAN backend."""

import os

GFPGAN_DOCKER_IMAGE = os.getenv("GFPGAN_DOCKER_IMAGE", "mygfpgan:latest")
GFPGAN_WEIGHTS_PATH = "/opt/aisha_bot/models/GFPGAN/weights/GFPGANv1.4.pth"
GFPGAN_DEFAULT_UPSCALE = 2
GFPGAN_DEFAULT_ONLY_CENTER_FACE = False
GFPGAN_DEFAULT_EXT = "jpg"
GFPGAN_DEFAULT_AUTO = False
GFPGAN_SCRIPT_PATH = os.getenv("GFPGAN_SCRIPT_PATH", "/workspace/inference_gfpgan.py")
