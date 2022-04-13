import base64
from io import BytesIO
from fastapi import APIRouter, File, Form, Security, UploadFile
from PIL import Image
import uuid
from ..auth import get_api_key
from ..db import client
from ..env import env

router = APIRouter(prefix="/images", dependencies=[Security(get_api_key)])


@router.post("/upload")
async def upload_image(
    image: UploadFile = File(...),
    team_number: str = Form(...),
):
    try:
        pil_image = Image.open(image.file)
        pil_image = pil_image.convert("RGB")
    except:
        return {"error": "Invalid image"}
    img_buffer = BytesIO()
    pil_image.save(img_buffer, format="JPEG")
    byte_data = img_buffer.getvalue()
    base64_str = base64.b64encode(byte_data)
    img_id = str(uuid.uuid4())
    client[env.DB_NAME]["images"].insert_one(
        {"image": base64_str.decode("utf-8"), "id": img_id}
    )
    return {"img_id": img_id}
