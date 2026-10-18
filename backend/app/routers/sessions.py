from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketDisconnect
from app.core.database import get_db
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.models.session import ClinicalSession, SessionCreate, SessionUpdate, SOAPNotes
from app.core.security import get_current_user_payload, encrypt_data, decrypt_data, RoleChecker
from app.agents.graph import run_healthcare_agents
from app.services.falkor_service import falkor_service, resolve_patient_id
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Clinical Sessions"])

def get_session_repository(db = Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)

def get_user_repository(db = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

# Audit log helper
async def create_audit_trail(db, user_payload: dict, action: str, resource_id: str, details: str):
    audit_data = {
        "user_id": user_payload.get("sub", "system"),
        "user_name": user_payload.get("name", "Dr. Sarah Elizabeth, MD"),
        "role": user_payload.get("role", "doctor"),
        "action": action,
        "resource_id": resource_id,
        "details": details,
        "ip_address": "127.0.0.1",
        "timestamp": datetime.utcnow()
    }
    await db["audit_logs"].insert_one(audit_data)

@router.get("", response_model=List[ClinicalSession])
async def list_sessions(
    session_repo: SessionRepository = Depends(get_session_repository),
    payload: dict = Depends(get_current_user_payload)
):
    sessions = await session_repo.get_all_sessions_sorted()
    
    # Decrypt transcripts for presentation to authorized user
    decrypted_sessions = []
    for s in sessions:
        s["raw_transcript"] = decrypt_data(s.get("raw_transcript", ""))
        s["sanitized_transcript"] = decrypt_data(s.get("sanitized_transcript", ""))
        decrypted_sessions.append(ClinicalSession(**s))
        
    return decrypted_sessions

@router.post("/create", response_model=ClinicalSession)
async def create_session(
    session_in: SessionCreate,
    session_repo: SessionRepository = Depends(get_session_repository),
    db = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    session_dict = session_in.model_dump()
    session_id = f"sess_{int(datetime.utcnow().timestamp())}"
    session_dict["_id"] = session_id
    session_dict["raw_transcript"] = ""
    session_dict["sanitized_transcript"] = ""
    session_dict["created_at"] = datetime.utcnow()
    session_dict["updated_at"] = datetime.utcnow()
    
    created = await session_repo.create(session_dict)
    
    await create_audit_trail(
        db=db,
        user_payload=payload,
        action="SESSION_CREATED",
        resource_id=session_id,
        details=f"Created clinical documentation session for patient: {session_in.patient_name}"
    )
    
    return ClinicalSession(**created)

@router.get("/{session_id}", response_model=ClinicalSession)
async def get_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repository),
    payload: dict = Depends(get_current_user_payload)
):
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Clinical session not found")
        
    # Decrypt sensitive fields
    session["raw_transcript"] = decrypt_data(session.get("raw_transcript", ""))
    session["sanitized_transcript"] = decrypt_data(session.get("sanitized_transcript", ""))
    return ClinicalSession(**session)

@router.post("/{session_id}/process", response_model=ClinicalSession)
async def process_session(
    session_id: str,
    payload_data: Dict[str, str], # {"raw_transcript": "..."}
    session_repo: SessionRepository = Depends(get_session_repository),
    db = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    raw_transcript = payload_data.get("raw_transcript", "")
    
    # Execute LangGraph Multi-Agent execution
    # This runs Voice, Sanitizer, Retrieval, Clinical, Coding, Compliance, Revenue, and Reviewer
    patient_id = resolve_patient_id(session.get("patient_name", ""), session.get("patient_dob", ""), session.get("metadata"))
    agent_outputs = await run_healthcare_agents(
        session_id=session_id, raw_transcript=raw_transcript, patient_id=patient_id,
        department=(session.get("metadata") or {}).get("department", ""))
    
    # Encrypt transcripts before writing to database (PHI protection)
    encrypted_raw = encrypt_data(agent_outputs["raw_transcript"])
    encrypted_sanitized = encrypt_data(agent_outputs["sanitized_transcript"])
    
    update_data = {
        "status": "completed",
        "raw_transcript": encrypted_raw,
        "sanitized_transcript": encrypted_sanitized,
        "pii_entities": agent_outputs.get("pii_entities", []),
        "patient_id": patient_id,
        "graph_provenance": agent_outputs.get("graph_provenance", {}),
        "clinical_notes": agent_outputs.get("clinical_notes", {}),
        "coding_recommendations": agent_outputs.get("coding_recommendations", []),
        "compliance_report": agent_outputs.get("compliance_report", {}),
        "revenue_report": agent_outputs.get("revenue_report", {}),
        "reviewer_report": agent_outputs.get("reviewer_report", {}),
        "updated_at": datetime.utcnow()
    }
    
    updated = await session_repo.update(session_id, update_data)
    
    await create_audit_trail(
        db=db,
        user_payload=payload,
        action="SESSION_PROCESSED_BY_AGENTS",
        resource_id=session_id,
        details="Multi-Agent LangGraph workflow executed successfully. PII masked and encrypted."
    )
    
    # Return decrypted version
    updated["raw_transcript"] = raw_transcript
    updated["sanitized_transcript"] = agent_outputs["sanitized_transcript"]
    return ClinicalSession(**updated)

@router.put("/{session_id}/notes", response_model=ClinicalSession)
async def update_clinical_notes(
    session_id: str,
    notes_in: Dict[str, Any], # Contains manual changes to clinical_notes and coding_recommendations
    session_repo: SessionRepository = Depends(get_session_repository),
    db = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    # HUMAN-IN-THE-LOOP route
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    update_data = {
        "clinical_notes": notes_in.get("clinical_notes", session.get("clinical_notes")),
        "coding_recommendations": notes_in.get("coding_recommendations", session.get("coding_recommendations")),
        "updated_at": datetime.utcnow()
    }
    
    updated = await session_repo.update(session_id, update_data)
    
    await create_audit_trail(
        db=db,
        user_payload=payload,
        action="HUMAN_IN_THE_LOOP_EDIT",
        resource_id=session_id,
        details="Manual override of EHR SOAP Notes/Codes executed by Doctor."
    )
    
    updated["raw_transcript"] = decrypt_data(updated.get("raw_transcript", ""))
    updated["sanitized_transcript"] = decrypt_data(updated.get("sanitized_transcript", ""))
    return ClinicalSession(**updated)

@router.put("/{session_id}/approve", response_model=ClinicalSession)
async def approve_session(
    session_id: str,
    reviewer_notes: Dict[str, str], # {"notes": "..."}
    session_repo: SessionRepository = Depends(get_session_repository),
    db = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Human validation with graph provenance: unresolved contraindications need explicit acknowledgement
    provenance = session.get("graph_provenance", {}) or {}
    alerts = provenance.get("contraindications", [])
    if alerts and reviewer_notes.get("acknowledge_alerts") != "true":
        raise HTTPException(
            status_code=409,
            detail=f"{len(alerts)} cross-session contraindication alert(s) must be acknowledged before approval.",
        )

    # Update reviewer status to approved
    current_reviewer_report = session.get("reviewer_report", {})
    current_reviewer_report["approved_by"] = payload.get("sub", "reviewer")
    current_reviewer_report["approved_at"] = datetime.utcnow()
    current_reviewer_report["reviewer_notes"] = reviewer_notes.get("notes", "Approved by expert clinical reviewer.")
    
    # Commit the validated encounter to the patient's isolated FalkorDB memory graph (Track 02)
    try:
        codes = session.get("coding_recommendations", []) or []
        conditions = "; ".join(f"{c.get('description')} ({c.get('code')})" for c in codes if c.get("system") == "ICD-10")
        meds = [" ".join(str(x) for x in (m.get("name"), m.get("dosage")) if x)
                for m in (session.get("clinical_notes", {}) or {}).get("medication_summary", []) if m.get("name")]
        pid = session.get("patient_id") or resolve_patient_id(session.get("patient_name", ""), session.get("patient_dob", ""), session.get("metadata"))
        falkor_service.record_encounter(pid, session_id, conditions, meds, patient_name=session.get("patient_name", ""))
        provenance["memory_committed"] = True
    except Exception as e:
        logger.error(f"Could not commit encounter memory to FalkorDB: {e}")
        provenance["memory_committed"] = False

    update_data = {
        "status": "reviewed",
        "reviewer_report": current_reviewer_report,
        "graph_provenance": provenance,
        "updated_at": datetime.utcnow()
    }
    
    updated = await session_repo.update(session_id, update_data)
    
    await create_audit_trail(
        db=db,
        user_payload=payload,
        action="SESSION_APPROVED",
        resource_id=session_id,
        details=f"EHR Documentation and billing codes approved by clinician. Status updated to reviewed."
    )
    
    updated["raw_transcript"] = decrypt_data(updated.get("raw_transcript", ""))
    updated["sanitized_transcript"] = decrypt_data(updated.get("sanitized_transcript", ""))
    return ClinicalSession(**updated)

@router.post("/{session_id}/upload-document", response_model=ClinicalSession)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    session_repo: SessionRepository = Depends(get_session_repository),
    db = Depends(get_db),
    payload: dict = Depends(get_current_user_payload)
):
    # MULTIMODAL integration (Lab reports, images, clinical file scans)
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Parse file contents (mocking extraction)
    filename = file.filename
    content_type = file.content_type
    
    # Simulated OCR extraction text
    simulated_ocr_text = f"Uploaded Lab Report ({filename}): Patient hemoglobin HbA1c is 6.4%, fasting blood glucose is 126 mg/dL. Standard blood count values are within normal limits."
    
    # Append content to transcript
    current_transcript = decrypt_data(session.get("raw_transcript", ""))
    appended_transcript = f"{current_transcript}\n\n[System - Multimodal Document uploaded: {filename}]\n{simulated_ocr_text}"
    
    update_data = {
        "raw_transcript": encrypt_data(appended_transcript),
        "updated_at": datetime.utcnow()
    }
    
    updated = await session_repo.update(session_id, update_data)
    
    await create_audit_trail(
        db=db,
        user_payload=payload,
        action="MULTIMODAL_DOCUMENT_UPLOADED",
        resource_id=session_id,
        details=f"Uploaded report {filename} ({content_type}). Text parsed and appended to consultation stream."
    )
    
    updated["raw_transcript"] = appended_transcript
    updated["sanitized_transcript"] = decrypt_data(updated.get("sanitized_transcript", ""))
    return ClinicalSession(**updated)

# WebSockets endpoint for Voice Assistant real-time streaming
@router.websocket("/{session_id}/voice")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
    db = Depends(get_db)
):
    await websocket.accept()
    logger.info(f"WebSocket voice session opened: {session_id}")
    
    # Simulate Whisper STT incremental text emission
    simulated_utterances = [
        "Doctor: Hello, Mr. Doe. How has your cough been since last week?",
        "Patient: Honestly doctor, it hasn't improved much. It is still very dry and annoying.",
        "Doctor: Any chest congestion or difficulty breathing when you walk?",
        "Patient: Yes, when I walk up stairs, my chest feels heavy and tight, and I can hear myself wheezing.",
        "Doctor: Let me check your chest. Yes, there's some mild wheezing in the lower lobes. Let's do an EKG today."
    ]
    
    try:
        # Loop to handle incoming WebSocket audio frames (in bytes) and send back structured real-time speech-to-text
        utterance_idx = 0
        while True:
            # Receive audio chunk (or text message)
            data = await websocket.receive()
            
            # Simple simulation: every time data is received, output the next clinical speaker segment
            if utterance_idx < len(simulated_utterances):
                # Send text transcript stream with speaker metadata back to client
                response_payload = {
                    "text": simulated_utterances[utterance_idx],
                    "speaker": "Doctor" if "Doctor:" in simulated_utterances[utterance_idx] else "Patient",
                    "final": True,
                    "noise_db": -45.0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(response_payload))
                utterance_idx += 1
            else:
                await websocket.send_text(json.dumps({
                    "text": "[Continuous stream active - speak into microphone]",
                    "speaker": "System",
                    "final": False
                }))
            
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket voice session disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket stream error: {e}")
