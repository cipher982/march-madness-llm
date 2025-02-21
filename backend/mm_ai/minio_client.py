"""Minio client configuration."""

import os

import dotenv
from minio import Minio

dotenv.load_dotenv()

# Create Minio client
client = Minio(
    str(os.getenv("MINIO_ENDPOINT")),
    access_key=str(os.getenv("MINIO_ACCESS_KEY")),
    secret_key=str(os.getenv("MINIO_SECRET_KEY")),
    secure=bool(os.getenv("MINIO_SECURE")),
)

LOGOS_BUCKET = str(os.getenv("MINIO_BUCKET"))
