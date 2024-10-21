import torch
from PIL import Image

from conch.open_clip_custom import create_model_from_pretrained

model, preprocess = create_model_from_pretrained('conch_ViT-B-16', "hf_hub:MahmoodLab/conch", hf_auth_token="<your_user_access_token>")

image = Image.open("path/to/image.jpg")
image = preprocess(image).unsqueeze(0)
with torch.inference_mode():
    image_embs = model.encode_image(image, proj_contrast=False, normalize=False)
