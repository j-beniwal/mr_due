from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from ..services.auth_service import get_user_from_token
from ..services.inference_service import inference_service
import app.services.checklist_creator as checklist_creator
import app.services.create_reason as create_reason
from ..models.user import User
from ..db.mongodb import database

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/evaluate")
async def evaluate_compliance(token: str = Depends(oauth2_scheme)):
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Fetch user's documents
    user_docs = await database.documents.find({"user_id": user.id}).to_list(length=None)
    
    checklist_files = [doc['path'] for doc in user_docs if doc.get('type') == 'checklist']
    evidence_files = [doc['path'] for doc in user_docs if doc.get('type') == 'evidence']
    print("checklist_files", checklist_files)
    print("evidence_files", evidence_files)
    
    if not checklist_files:
        raise HTTPException(status_code=400, detail="No checklist documents found")
    
    if not evidence_files:
        raise HTTPException(status_code=400, detail="No evidence documents found")
    
    # # Process documents
    # print("Processing documents...")
    # inference_service.process_documents(checklist_files, evidence_files)
    
    # # Generate checklist JSON
    # checklist = inference_service.generate_checklist_json()
    
    # # Evaluate compliance
    # evaluation_result = inference_service.evaluate_compliance(checklist)
    
    
    print("getting compliance checklist ")
    compliance_checklist = checklist_creator.get_compliance_checklist()
    
    # Create a reason for each checklist item
    updated_compliance_checklist = create_reason.get_compliance_updates(compliance_checklist)
    
    return updated_compliance_checklist