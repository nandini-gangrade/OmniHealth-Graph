from fastapi import APIRouter, Depends, Query
from typing import List
from app.core.security import get_current_user_payload
from app.services.falkor_service import falkor_service, safe_patient_id

router = APIRouter(prefix="/graph", tags=["FalkorDB Graph"])


@router.get("/status")
async def graph_status():
    return falkor_service.status()


@router.get("/necessity")
async def necessity(symptoms: List[str] = Query(...), cpt: str = Query(...), payload: dict = Depends(get_current_user_payload)):
    return falkor_service.verify_medical_necessity(symptoms, cpt)


@router.get("/patient/{patient_id}")
async def patient_memory(patient_id: str, payload: dict = Depends(get_current_user_payload)):
    return falkor_service.get_patient_memory(safe_patient_id(patient_id))


@router.get("/department/{dept_name}")
async def department(dept_name: str, payload: dict = Depends(get_current_user_payload)):
    return falkor_service.get_department_compliance(dept_name)
