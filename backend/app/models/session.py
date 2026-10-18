from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SOAPNotes(BaseModel):
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""

class FHIRResource(BaseModel):
    resource_type: str = "Bundle"
    fhir_json: Dict[str, Any] = {}

class ClinicalDocumentation(BaseModel):
    soap_notes: SOAPNotes = Field(default_factory=SOAPNotes)
    progress_notes: str = ""
    visit_summary: str = ""
    discharge_summary: str = ""
    medication_summary: List[Dict[str, Any]] = Field(default_factory=list)
    treatment_plan: str = ""
    fhir_output: FHIRResource = Field(default_factory=FHIRResource)

class CodeRecommendation(BaseModel):
    code: str
    system: str  # 'ICD-10', 'CPT', 'HCPCS'
    description: str
    confidence: float
    supporting_evidence: str
    reimbursement_estimate: float = 0.0
    necessity_verified: Optional[bool] = None   # set by FalkorDB traversal
    trace_path: List[str] = Field(default_factory=list)  # nodes(path) provenance

class ComplianceReport(BaseModel):
    missing_documentation: List[str] = Field(default_factory=list)
    medical_necessity_checked: bool = True
    coding_completeness_score: float = 100.0  # 0 to 100
    cms_compliance_status: str = "Compliant"
    documentation_gaps: List[str] = Field(default_factory=list)

class RevenueReport(BaseModel):
    revenue_leakage_identified: List[str] = Field(default_factory=list)
    rejected_claim_probability: float = 0.0  # percentage 0 to 100
    missing_billable_procedures: List[str] = Field(default_factory=list)
    revenue_score: float = 100.0
    estimated_reimbursement: float = 0.0

class ReviewerReport(BaseModel):
    aggregate_confidence: float = 100.0
    hallucination_detected: bool = False
    hallucination_details: str = ""
    validated_citations: List[Dict[str, Any]] = Field(default_factory=list)
    reviewer_notes: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class RagasEvaluation(BaseModel):
    faithfulness: float = 1.0
    answer_relevancy: float = 1.0
    context_precision: float = 1.0
    context_recall: float = 1.0
    answer_correctness: float = 1.0

class LangfuseMetadata(BaseModel):
    trace_id: str = ""
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    execution_status: str = "success"

class SessionBase(BaseModel):
    patient_name: str
    patient_dob: str
    doctor_id: str
    doctor_name: str
    status: str = "active"  # "active", "completed", "reviewed"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    status: Optional[str] = None
    raw_transcript: Optional[str] = None
    sanitized_transcript: Optional[str] = None
    clinical_notes: Optional[ClinicalDocumentation] = None
    coding_recommendations: Optional[List[CodeRecommendation]] = None
    compliance_report: Optional[ComplianceReport] = None
    revenue_report: Optional[RevenueReport] = None
    reviewer_report: Optional[ReviewerReport] = None
    rag_evaluation: Optional[RagasEvaluation] = None
    langfuse_metadata: Optional[LangfuseMetadata] = None

class ClinicalSession(SessionBase):
    id: str = Field(alias="_id")
    raw_transcript: str = ""
    sanitized_transcript: str = ""
    pii_entities: List[Dict[str, Any]] = Field(default_factory=list)
    patient_id: str = ""
    graph_provenance: Dict[str, Any] = Field(default_factory=dict)
    clinical_notes: ClinicalDocumentation = Field(default_factory=ClinicalDocumentation)
    coding_recommendations: List[CodeRecommendation] = Field(default_factory=list)
    compliance_report: ComplianceReport = Field(default_factory=ComplianceReport)
    revenue_report: RevenueReport = Field(default_factory=RevenueReport)
    reviewer_report: ReviewerReport = Field(default_factory=ReviewerReport)
    rag_evaluation: RagasEvaluation = Field(default_factory=RagasEvaluation)
    langfuse_metadata: LangfuseMetadata = Field(default_factory=LangfuseMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
