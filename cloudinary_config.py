# cloudinary_config.py
import cloudinary
import os

cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
api_key = os.environ.get("CLOUDINARY_API_KEY")
api_secret = os.environ.get("CLOUDINARY_API_SECRET")

if not all([cloud_name, api_key, api_secret]):
    raise EnvironmentError("Variáveis do Cloudinary não estão definidas no ambiente.")

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret
)
