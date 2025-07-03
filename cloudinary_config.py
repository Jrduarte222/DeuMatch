# cloudinary_config.py
import cloudinary
import os

cloudinary.config(
    cloud_name="dqlonp7kf",
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)
