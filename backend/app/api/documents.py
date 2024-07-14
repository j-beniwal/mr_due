from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from ..services.auth_service import get_user_from_token
from ..models.user import User
from ..db.mongodb import database
from bson import ObjectId
import os
from datetime import datetime
from typing import List

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UPLOAD_DIRECTORY = "uploads"

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    doc_type: str = Form(...),
    token: str = Depends(oauth2_scheme)
):
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if doc_type not in ['checklist', 'evidence']:
        raise HTTPException(status_code=400, detail="Invalid document type")

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    uploaded_files = []
    for file in files:
        file_location = f"{UPLOAD_DIRECTORY}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        document = {
            "filename": file.filename,
            "path": file_location,
            "upload_date": datetime.utcnow(),
            "user_id": user.id,
            "type": doc_type
        }
        
        result = await database.documents.insert_one(document)
        
        await database.users.update_one(
            {"_id": user.id},
            {"$push": {"documents": result.inserted_id}}
        )

        uploaded_files.append({"filename": file.filename, "document_id": str(result.inserted_id)})

    return {
        "message": f"{len(uploaded_files)} {doc_type} files uploaded successfully",
        "files": uploaded_files
    }

@router.post("/generate-checklist")
async def generate_checklist(compliance_name: str, token: str = Depends(oauth2_scheme)):
    print(compliance_name)
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    compliance = await database.compliances.find_one({"name": compliance_name})
    if not compliance:
        raise HTTPException(status_code=404, detail="Compliance not found")
    
    return {
        "message": f"Checklist generated for {compliance_name}",
        "checklist": compliance["checklist"]
    }