import logging
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, START, END

# Import agents and services
from app.agents.voice_agent import voice_agent
from app.services.pii_service import pii_service
from app.services.falkor_service import falkor_service
from app.agents.clinical_agent import clinical_agent
from app.agents.coding_agent import coding_agent
from app.agents.compliance_agent import compliance_agent
from app.agents.revenue_agent import revenue_agent
from app.agents.reviewer_agent import reviewer_agent

logger = logging.getLogger(__name__)

# State definition
class AgentState(TypedDict):
    session_id: str
    raw_transcript: str
    sanitized_transcript: str
    pii_entities: List[Dict[str, Any]]
    patient_id: str
    retrieved_knowledge: str
    graph_provenance: Dict[str, Any]
    clinical_notes: Dict[str, Any]
    coding_recommendations: List[Dict[str, Any]]
    compliance_report: Dict[str, Any]
    revenue_report: Dict[str, Any]
    reviewer_report: Dict[str, Any]
    metadata: Dict[str, Any]

# Node functions
async def voice_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: voice_node execution")
    # If transcript is already provided in metadata, use it, else process audio
    raw_transcript = state.get("raw_transcript", "")
    metadata = state.get("metadata", {})
    
    if not raw_transcript:
        audio_data = metadata.get("audio_bytes", b"")
        voice_result = await voice_agent.process_audio(audio_data)
        raw_transcript = voice_result["transcript"]
        metadata["voice_metrics"] = {
            "duration": voice_result["duration_seconds"],
            "noise_db": voice_result["noise_level_db"]
        }
        
    return {"raw_transcript": raw_transcript, "metadata": metadata}

async def sanitization_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: sanitization_node execution")
    raw_text = state.get("raw_transcript", "")
    sanitized_text, pii_list = pii_service.sanitize(raw_text)
    return {"sanitized_transcript": sanitized_text, "pii_entities": pii_list}

async def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Graph retrieval (replaces vector RAG): symptoms from the rules graph + the patient's memory subgraph."""
    logger.info("LangGraph Node: retrieval_node execution")
    text = state.get("sanitized_transcript", "")
    patient_id = state.get("patient_id", "")
    symptoms = falkor_service.extract_symptoms(text)
    memory = falkor_service.get_patient_memory(patient_id) if patient_id else {}
    lines = [f"Symptoms matched in clinical_rules graph: {', '.join(symptoms) or 'none'}."]
    if memory.get("active_medications"):
        lines.append(f"Patient {patient_id} active medications from prior encounters: {', '.join(memory['active_medications'])}.")
    for enc in memory.get("encounters", []):
        lines.append(f"Prior encounter {enc['id']} ({enc['date']}): conditions {enc['conditions']}, medications {enc['medications']}.")
    prov = dict(state.get("graph_provenance", {}))
    prov.update({"patient_id": patient_id, "patient_graph": f"patient_{patient_id}" if patient_id else None,
                 "symptoms": symptoms, "patient_memory": memory,
                 "falkordb": falkor_service.available})
    return {"retrieved_knowledge": "\n".join(lines), "graph_provenance": prov}

async def clinical_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: clinical_node execution")
    notes, alerts = await clinical_agent.generate_documentation(
        state.get("sanitized_transcript", ""), state.get("retrieved_knowledge", ""), state.get("patient_id") or None)
    prov = dict(state.get("graph_provenance", {}))
    prov["contraindications"] = alerts
    return {"clinical_notes": notes, "graph_provenance": prov}

async def coding_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: coding_node execution")
    text = state.get("sanitized_transcript", "")
    soap_notes = state.get("clinical_notes", {}).get("soap_notes", {})
    codes = await coding_agent.recommend_codes(text, soap_notes, state.get("retrieved_knowledge", ""))
    codes, records, symptoms = coding_agent.attach_necessity(codes, text, soap_notes)
    prov = dict(state.get("graph_provenance", {}))
    prov["medical_necessity"] = records
    prov["symptoms"] = sorted(set(prov.get("symptoms", [])) | set(symptoms))
    return {"coding_recommendations": codes, "graph_provenance": prov}

async def compliance_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: compliance_node execution")
    soap_notes = state.get("clinical_notes", {}).get("soap_notes", {})
    codes = state.get("coding_recommendations", [])
    prov = dict(state.get("graph_provenance", {}))
    report = await compliance_agent.audit_compliance(
        soap_notes, codes, prov.get("medical_necessity", []), state.get("metadata", {}).get("department"))
    g = report.pop("_graph", {})
    prov.update({"unbundling": g.get("unbundling", []), "department": g.get("department"),
                 "department_compliance": g.get("department_compliance", [])})
    return {"compliance_report": report, "graph_provenance": prov}

async def revenue_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: revenue_node execution")
    soap_notes = state.get("clinical_notes", {}).get("soap_notes", {})
    codes = state.get("coding_recommendations", [])
    report = await revenue_agent.optimize_revenue(soap_notes, codes)
    return {"revenue_report": report}

async def reviewer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph Node: reviewer_node execution")
    report = await reviewer_agent.review_outputs(
        state.get("clinical_notes", {}), state.get("coding_recommendations", []),
        state.get("compliance_report", {}), state.get("revenue_report", {}))
    return {"reviewer_report": report}

# Build LangGraph workflow
try:
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("voice", voice_node)
    workflow.add_node("sanitizer", sanitization_node)
    workflow.add_node("retriever", retrieval_node)
    workflow.add_node("clinical", clinical_node)
    workflow.add_node("coding", coding_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("revenue", revenue_node)
    workflow.add_node("reviewer", reviewer_node)

    # Register Edges
    workflow.add_edge(START, "voice")
    workflow.add_edge("voice", "sanitizer")
    workflow.add_edge("sanitizer", "retriever")
    workflow.add_edge("retriever", "clinical")
    workflow.add_edge("clinical", "coding")
    workflow.add_edge("coding", "compliance")
    workflow.add_edge("compliance", "revenue")
    workflow.add_edge("revenue", "reviewer")
    workflow.add_edge("reviewer", END)

    app_graph = workflow.compile()
    logger.info("Successfully compiled LangGraph clinical documentation workflow.")
except Exception as e:
    logger.warning(f"Error building LangGraph ({e}). Compiling fallback sequential runner.")
    app_graph = None

async def run_healthcare_agents(session_id: str, raw_transcript: str = "", audio_bytes: bytes = b"",
                                patient_id: str = "", department: str = "") -> Dict[str, Any]:
    """Orchestrates all agents to process a patient-doctor documentation session."""
    initial_state = {
        "session_id": session_id,
        "raw_transcript": raw_transcript,
        "sanitized_transcript": "",
        "pii_entities": [],
        "patient_id": patient_id,
        "graph_provenance": {},
        "retrieved_knowledge": "",
        "clinical_notes": {},
        "coding_recommendations": [],
        "compliance_report": {},
        "revenue_report": {},
        "reviewer_report": {},
        "metadata": {"audio_bytes": audio_bytes, **({"department": department} if department else {})}
    }

    if app_graph:
        try:
            # Execute compiled LangGraph
            final_state = await app_graph.ainvoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"LangGraph runtime error: {e}. Falling back to sequential agent orchestration.")

    # Fallback/Manual Sequential Execution (Ensures 100% reliability)
    state = initial_state.copy()
    
    state.update(await voice_node(state))
    state.update(await sanitization_node(state))
    state.update(await retrieval_node(state))
    state.update(await clinical_node(state))
    state.update(await coding_node(state))
    state.update(await compliance_node(state))
    state.update(await revenue_node(state))
    state.update(await reviewer_node(state))
    
    return state
