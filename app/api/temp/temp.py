import os
import io
import boto3
from typing import Literal
from botocore.config import Config
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

router = APIRouter()

TIGRIS_ENDPOINT = os.environ.get("TIGRIS_STORAGE_ENDPOINT")
TIGRIS_ACCESS_KEY = os.environ.get("TIGRIS_STORAGE_ACCESS_KEY_ID")
TIGRIS_SECRET_KEY = os.environ.get("TIGRIS_STORAGE_SECRET_ACCESS_KEY")
BUCKET_NAME = "system-prompts"

def upload_to_tigris(prompt_name: str, file_obj: io.BytesIO):
    """Handles the Boto3 S3 client connection and upload."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=TIGRIS_ENDPOINT,
        aws_access_key_id=TIGRIS_ACCESS_KEY,
        aws_secret_access_key=TIGRIS_SECRET_KEY,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    
    # Uploads the file object to the specified bucket with the prompt_name as the key
    s3_client.upload_fileobj(
        Fileobj=file_obj,
        Bucket=BUCKET_NAME,
        Key=f"{prompt_name}.txt",
        ExtraArgs={
            "ContentType": "text/plain",
            "CacheControl": "no-cache, no-store, must-revalidate"
        }
    )

@router.post("/api/upload-prompt")
async def upload_prompt(
    prompt: UploadFile = File(...),
    prompt_name: Literal[
        "qna", "study_mode", "lesson_mode", "coder", "voice_general", "voice_lesson"
    ] = Form(...),
):
    # Validate file extension
    if not prompt.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed.")

    try:
        # Read the file content into a BytesIO stream
        file_content = await prompt.read()
        file_stream = io.BytesIO(file_content)
        
        # Trigger the upload function
        upload_to_tigris(prompt_name, file_stream)
        
        return {
            "status": "success", 
            "message": f"Successfully uploaded {prompt_name}.txt to {BUCKET_NAME}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")