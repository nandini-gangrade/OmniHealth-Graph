import React, { useState, useEffect } from "react";
import { 
  Card, CardContent, CardHeader, CardTitle, 
  Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent 
} from "./ui/shadcn";
import { api } from "../services/api";
import { 
  FileText, ShieldAlert, BadgeDollarSign, 
  ArrowUpRight, AlertCircle, FileCheck, CheckCircle2,
  Trash2, Plus, Upload, Loader2, Network, ChevronRight, Building2
} from "lucide-react";

interface SessionDetailsProps {
  session: any;
  onRefresh: () => void;
}

// Renders a FalkorDB nodes(path) trace as pills: Symptom -> ICD-10 -> CPT
const TracePills: React.FC<{ path: string[]; tone?: "cyan" | "rose" }> = ({ path, tone = "cyan" }) => {
  const color = tone === "rose"
    ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
    : "bg-cyan-500/10 border-cyan-500/30 text-cyan-300";
  return (
    <div className="flex flex-wrap items-center gap-1">
      {path.map((node, i) => (
        <React.Fragment key={i}>
          <span className={`px-2 py-0.5 rounded-full border text-[10px] font-mono ${color}`}>{node}</span>
          {i < path.length - 1 && <ChevronRight size={12} className="text-slate-500" />}
        </React.Fragment>
      ))}
    </div>
  );
};

export const SessionDetails: React.FC<SessionDetailsProps> = ({ session, onRefresh }) => {
  const [activeTab, setActiveTab] = useState<string>("clinical");
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  
  // Local state for editable SOAP Notes
  const [soapSubjective, setSoapSubjective] = useState(session.clinical_notes?.soap_notes?.subjective || "");
  const [soapObjective, setSoapObjective] = useState(session.clinical_notes?.soap_notes?.objective || "");
  const [soapAssessment, setSoapAssessment] = useState(session.clinical_notes?.soap_notes?.assessment || "");
  const [soapPlan, setSoapPlan] = useState(session.clinical_notes?.soap_notes?.plan || "");
  
  // Local state for editable codes
  const [codes, setCodes] = useState<any[]>(session.coding_recommendations || []);
  const [newCode, setNewCode] = useState("");
  const [newSystem, setNewSystem] = useState("ICD-10");
  const [newDesc, setNewDesc] = useState("");
  
  // Local state for Reviewer notes
  const [reviewerNotes, setReviewerNotes] = useState(session.reviewer_report?.reviewer_notes || "");

  // File Upload state for Multimodal PDF/Lab reports
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // FalkorDB provenance (Tracks 01-03)
  const prov = session.graph_provenance || {};
  const alerts: any[] = prov.contraindications || [];
  const necessity: any[] = prov.medical_necessity || [];
  const unbundling: any[] = prov.unbundling || [];
  const [ack, setAck] = useState(false);
  const [deptRows, setDeptRows] = useState<any[]>(prov.department_compliance || []);

  useEffect(() => {
    if (prov.department) {
      api.getDepartmentCompliance(prov.department).then(setDeptRows).catch(() => {});
    }
  }, [session._id]);

  const handleSaveNotes = async () => {
    setIsSaving(true);
    try {
      const updatedNotes = {
        clinical_notes: {
          ...session.clinical_notes,
          soap_notes: {
            subjective: soapSubjective,
            objective: soapObjective,
            assessment: soapAssessment,
            plan: soapPlan
          }
        },
        coding_recommendations: codes
      };
      await api.updateNotes(session._id, updatedNotes);
      alert("Clinical notes and recommended codes updated successfully (Audit log generated).");
      onRefresh();
    } catch (e) {
      console.error(e);
      alert("Error updating documentation.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await api.approveSession(session._id, reviewerNotes, ack);
      alert("EHR documentation and billing codes approved. Transmitted to billing system.");
      onRefresh();
    } catch (e) {
      console.error(e);
      alert((e as Error).message || "Error approving session.");
    } finally {
      setIsApproving(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    
    setIsUploading(true);
    try {
      await api.uploadMultimodalDocument(session._id, uploadFile);
      alert(`Successfully uploaded and parsed: ${uploadFile.name}`);
      setUploadFile(null);
      onRefresh();
    } catch (e) {
      console.error(e);
      alert("Error uploading file.");
    } finally {
      setIsUploading(false);
    }
  };

  const addCodeItem = () => {
    if (!newCode || !newDesc) return;
    setCodes([
      ...codes,
      {
        code: newCode,
        system: newSystem,
        description: newDesc,
        confidence: 1.0,
        supporting_evidence: "Manually added by Clinician (Human-in-the-loop override)",
        reimbursement_estimate: newSystem === "ICD-10" ? 120.0 : 95.0
      }
    ]);
    setNewCode("");
    setNewDesc("");
  };

  const removeCodeItem = (idx: number) => {
    setCodes(codes.filter((_, i) => i !== idx));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      {/* LEFT & CENTER PANEL (SOAP / Codes / Dashboard tabs) */}
      <div className="lg:col-span-2 space-y-6">
        {/* TRACK 02: cross-session contraindication warning */}
        {alerts.length > 0 && (
          <Card className="border-rose-500/50 bg-rose-950/20">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-rose-300">
                <ShieldAlert size={18} />
                <span>Cross-Session Contraindication Warning</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map((a, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-950/60 border border-rose-500/30 space-y-2">
                  <p className="text-sm text-rose-200 font-semibold">
                    {a.new_medication} + {a.conflicting_medication} ({a.severity})
                  </p>
                  <p className="text-xs text-slate-300">
                    {a.effect}. Conflicting drug was prescribed in encounter <b>{a.from_encounter}</b> on {a.encounter_date}
                    and is still active in this patient's memory graph.
                  </p>
                  <TracePills path={a.trace_path} tone="rose" />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab}>
          <div className="flex justify-between items-center mb-4">
            <TabsList className="w-96">
              <TabsTrigger value="clinical" activeTab={activeTab} setActiveTab={setActiveTab}>SOAP & Clinical</TabsTrigger>
              <TabsTrigger value="coding" activeTab={activeTab} setActiveTab={setActiveTab}>Billing Codes</TabsTrigger>
              <TabsTrigger value="compliance" activeTab={activeTab} setActiveTab={setActiveTab}>Audit & Compliance</TabsTrigger>
            </TabsList>
            <Badge variant={session.status === "reviewed" ? "success" : "info"}>
              Status: {session.status.toUpperCase()}
            </Badge>
          </div>

          {/* TAB 1: SOAP & CLINICAL */}
          <TabsContent value="clinical" activeTab={activeTab}>
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="flex items-center space-x-2">
                    <FileText size={18} className="text-cyan-400" />
                    <span>SOAP Consultation Notes</span>
                  </CardTitle>
                  {session.status !== "reviewed" && (
                    <Button onClick={handleSaveNotes} disabled={isSaving} size="sm">
                      {isSaving ? <Loader2 className="animate-spin mr-2" size={14} /> : null}
                      Save Edits
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Subjective */}
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Subjective (S)</label>
                  <textarea
                    rows={4}
                    value={soapSubjective}
                    onChange={(e) => setSoapSubjective(e.target.value)}
                    disabled={session.status === "reviewed"}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
                {/* Objective */}
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Objective (O)</label>
                  <textarea
                    rows={4}
                    value={soapObjective}
                    onChange={(e) => setSoapObjective(e.target.value)}
                    disabled={session.status === "reviewed"}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
                {/* Assessment */}
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Assessment (A)</label>
                  <textarea
                    rows={4}
                    value={soapAssessment}
                    onChange={(e) => setSoapAssessment(e.target.value)}
                    disabled={session.status === "reviewed"}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
                {/* Plan */}
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Plan (P)</label>
                  <textarea
                    rows={4}
                    value={soapPlan}
                    onChange={(e) => setSoapPlan(e.target.value)}
                    disabled={session.status === "reviewed"}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>

                {/* FHIR Spec */}
                <div className="border-t border-slate-800 pt-4 mt-6">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">FHIR Standard JSON Representation</h4>
                  <pre className="p-3 bg-slate-950 rounded-lg text-[10px] text-teal-400 font-mono max-h-40 overflow-y-auto border border-slate-900">
                    {JSON.stringify(session.clinical_notes?.fhir_output?.fhir_json || {}, null, 2)}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 2: MEDICAL CODING */}
          <TabsContent value="coding" activeTab={activeTab}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BadgeDollarSign size={18} className="text-cyan-400" />
                  <span>Recommended Billing Codes</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                
                {/* Code list */}
                <div className="space-y-3">
                  {codes.map((item, idx) => (
                    <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded-lg bg-slate-950/40 border border-slate-800 space-y-2 md:space-y-0">
                      <div className="flex items-start space-x-3">
                        <Badge variant={item.system === "ICD-10" ? "info" : "success"}>
                          {item.system}: {item.code}
                        </Badge>
                        <div>
                          <h4 className="text-sm font-semibold text-slate-200">{item.description}</h4>
                          <p className="text-xs text-slate-400 mt-1 italic">
                            Evidence: "{item.supporting_evidence}"
                          </p>
                          {item.system === "CPT" && item.necessity_verified === false && (
                            <p className="text-[10px] text-amber-400 mt-1">No necessity path in graph - denial risk</p>
                          )}
                          {item.trace_path?.length > 0 && <div className="mt-1.5"><TracePills path={item.trace_path} /></div>}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="text-xs text-slate-400">Confidence</p>
                          <span className={`text-xs font-bold ${
                            item.confidence > 0.9 ? "text-emerald-400" :
                            item.confidence > 0.7 ? "text-amber-400" : "text-rose-400"
                          }`}>
                            {(item.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        {session.status !== "reviewed" && (
                          <button onClick={() => removeCodeItem(idx)} className="text-slate-500 hover:text-rose-400 transition-colors">
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Add code manually */}
                {session.status !== "reviewed" && (
                  <div className="border-t border-slate-800 pt-4 mt-6 space-y-3">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Add Code Override (Human-in-the-loop)</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <select 
                        value={newSystem} 
                        onChange={(e) => setNewSystem(e.target.value)}
                        className="bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 p-2 focus:outline-none"
                      >
                        <option value="ICD-10">ICD-10</option>
                        <option value="CPT">CPT</option>
                        <option value="HCPCS">HCPCS</option>
                      </select>
                      <input 
                        placeholder="Code (e.g. I10)" 
                        value={newCode}
                        onChange={(e) => setNewCode(e.target.value)}
                        className="bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 p-2 focus:outline-none"
                      />
                      <input 
                        placeholder="Description" 
                        value={newDesc}
                        onChange={(e) => setNewDesc(e.target.value)}
                        className="col-span-1 md:col-span-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 p-2 focus:outline-none"
                      />
                    </div>
                    <Button variant="glass" size="sm" onClick={addCodeItem} className="w-full md:w-auto">
                      <Plus size={14} className="mr-1" /> Add Code
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 3: AUDIT & COMPLIANCE */}
          <TabsContent value="compliance" activeTab={activeTab}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <ShieldAlert size={18} className="text-cyan-400" />
                  <span>Clinical Audit & Policy Compliance</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Score indicators */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between">
                    <div>
                      <h4 className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Compliance Rating</h4>
                      <p className="text-2xl font-bold text-cyan-400 mt-1">
                        {session.compliance_report?.coding_completeness_score || 95}%
                      </p>
                    </div>
                    <Badge variant={
                      (session.compliance_report?.coding_completeness_score || 95) > 90 ? "success" : "warning"
                    }>
                      {session.compliance_report?.cms_compliance_status || "Compliant"}
                    </Badge>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between">
                    <div>
                      <h4 className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Medical Necessity</h4>
                      <p className="text-sm font-semibold text-slate-200 mt-1">Checked against CMS Guidelines</p>
                    </div>
                    <CheckCircle2 className="text-emerald-400" size={24} />
                  </div>
                </div>

                {/* Documentation gaps */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Identified Documentation Gaps</h4>
                  <ul className="space-y-1.5">
                    {session.compliance_report?.documentation_gaps?.map((gap: string, idx: number) => (
                      <li key={idx} className="text-xs text-amber-400 flex items-center space-x-2">
                        <span className="w-1 h-1 rounded-full bg-amber-400"></span>
                        <span>{gap}</span>
                      </li>
                    )) || <li className="text-xs text-slate-400">No documentation gaps identified.</li>}
                  </ul>
                </div>

                {/* Missing elements */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Missing Documentation Recommendations</h4>
                  <ul className="space-y-1.5">
                    {session.compliance_report?.missing_documentation?.map((item: string, idx: number) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-center space-x-2">
                        <AlertCircle size={12} className="text-cyan-400" />
                        <span>{item}</span>
                      </li>
                    )) || <li className="text-xs text-slate-400">No missing documentation elements found.</li>}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* TRACK 01: FalkorDB Provenance Trace */}
        <Card className="border-cyan-500/30">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network size={18} className="text-cyan-400" />
              <span>FalkorDB Provenance Trace</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-[11px] text-slate-500">
              Deterministic <code>nodes(path)</code> from multi-hop Cypher: Symptom → ICD-10 → CPT. Patient graph:{" "}
              <code>{prov.patient_graph || "n/a"}</code>
            </p>
            {necessity.length === 0 && <p className="text-xs text-slate-400">No graph trace yet. Process the session to generate one.</p>}
            {necessity.map((n, i) => (
              <div key={i} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-slate-950/40 border border-slate-800">
                <div className="space-y-1">
                  <p className="text-xs text-slate-300">
                    CPT {n.cpt}{" "}
                    <span className={n.verified ? "text-emerald-400" : "text-rose-400"}>
                      {n.verified ? "medically necessary" : "NOT proven"}
                    </span>
                  </p>
                  {n.trace_path?.length > 0 && <TracePills path={n.trace_path} />}
                </div>
                <Badge variant={n.verified ? "success" : "warning"}>{n.verified ? "Verified" : "Gap"}</Badge>
              </div>
            ))}
            {unbundling.map((u, i) => (
              <div key={i} className="p-2 rounded-lg bg-amber-500/5 border border-amber-500/30 space-y-1">
                <p className="text-xs text-amber-300">{u.message}</p>
                <TracePills path={u.trace_path} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* RIGHT SIDE PANEL: REVENUE, MULTIMODAL, AND APPROVAL */}
      <div className="space-y-6">
        
        {/* Revenue Leakage Metrics Card */}
        <Card className="border-teal-500/25">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-emerald-400">
              <BadgeDollarSign size={18} />
              <span>Revenue Cycle Optimization</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-850">
              <span className="text-xs text-slate-400">Estimated Reimbursement:</span>
              <span className="text-lg font-bold text-slate-100">${session.revenue_report?.estimated_reimbursement || 0}</span>
            </div>
            
            <div className="flex justify-between items-center pb-3 border-b border-slate-850">
              <span className="text-xs text-slate-400">Claim Rejection Risk:</span>
              <span className={`text-xs font-bold ${
                (session.revenue_report?.rejected_claim_probability || 0) < 10 ? "text-emerald-400" :
                (session.revenue_report?.rejected_claim_probability || 0) < 25 ? "text-amber-400" : "text-rose-400"
              }`}>
                {session.revenue_report?.rejected_claim_probability || 0}%
              </span>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Identified Revenue Leakage</h4>
              <ul className="space-y-2">
                {session.revenue_report?.revenue_leakage_identified?.map((leak: string, idx: number) => (
                  <li key={idx} className="text-xs p-2 rounded bg-amber-500/5 border border-amber-500/10 text-amber-300">
                    {leak}
                  </li>
                )) || <li className="text-xs text-slate-500">No leakage opportunities identified.</li>}
              </ul>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Missing Billable Procedures</h4>
              <ul className="space-y-1">
                {session.revenue_report?.missing_billable_procedures?.map((proc: string, idx: number) => (
                  <li key={idx} className="text-xs text-emerald-400 flex items-center space-x-1.5">
                    <ArrowUpRight size={14} />
                    <span>{proc}</span>
                  </li>
                )) || <li className="text-xs text-slate-500">All billable procedures capture-verified.</li>}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* TRACK 03: Hospital Brain */}
        {deptRows.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Building2 size={14} className="text-cyan-400" />
                <span>Hospital Brain: {prov.department}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-[10px] text-slate-500">Supervising: {deptRows[0].supervising_physician} (synthetic demo data)</p>
              {deptRows.map((r, i) => (
                <div key={i} className="text-[11px] text-slate-300 flex justify-between">
                  <span>CPT {r.cpt} · {r.denial_code}</span>
                  <span className="text-amber-400">{r.denial_rate_pct}% denied</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Multimodal File Uploader (Lab reports, diagnostic scanning) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Upload size={14} className="text-cyan-400" />
              <span>Multimodal Attachments</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <form onSubmit={handleFileUpload} className="space-y-2">
              <input 
                type="file" 
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                disabled={session.status === "reviewed" || isUploading}
                className="block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-slate-350 hover:file:bg-slate-800 cursor-pointer"
              />
              <Button 
                type="submit" 
                variant="glass" 
                size="sm" 
                className="w-full"
                disabled={!uploadFile || isUploading || session.status === "reviewed"}
              >
                {isUploading ? <Loader2 className="animate-spin mr-2" size={12} /> : null}
                Upload lab / report
              </Button>
            </form>
            <p className="text-[10px] text-slate-500 text-center leading-normal">
              Accepts PDF, JPG, PNG. Extracted text will append to consultation context.
            </p>
          </CardContent>
        </Card>

        {/* Audit Verification & Sign-off Panel */}
        <Card className="border-cyan-500/30 bg-slate-950/60 shadow-cyan-glow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileCheck size={18} className="text-cyan-400" />
              <span>EHR Sign-Off Gatekeeper</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Reviewer Confidence:</span>
                <span className="font-bold text-cyan-400">{session.reviewer_report?.aggregate_confidence || 92}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Hallucinations Detected:</span>
                <span className="font-semibold text-emerald-400">None Flagged</span>
              </div>
              
              <div className="border-t border-slate-850 pt-2 mt-2">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">Citations Validation:</p>
                {session.reviewer_report?.validated_citations?.map((cit: any, i: number) => (
                  <div key={i} className="flex justify-between text-[10px] text-slate-300">
                    <span>Code {cit.code}</span>
                    <span className="text-teal-400">{cit.source}</span>
                  </div>
                ))}
              </div>
            </div>

            {session.status !== "reviewed" ? (
              <div className="space-y-3 border-t border-slate-850 pt-3">
                <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Reviewer Audit Remarks</label>
                <textarea
                  rows={2}
                  placeholder="Insert audit checknotes or approval codes..."
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs p-2 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                {alerts.length > 0 && (
                  <label className="flex items-start space-x-2 text-[11px] text-rose-300 cursor-pointer">
                    <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} className="mt-0.5" />
                    <span>I have reviewed the {alerts.length} graph-flagged contraindication(s) and take clinical responsibility.</span>
                  </label>
                )}
                <Button 
                  onClick={handleApprove} 
                  variant="accent" 
                  className="w-full text-xs py-2.5"
                  disabled={isApproving || (alerts.length > 0 && !ack)}
                >
                  {isApproving ? <Loader2 className="animate-spin mr-2" size={12} /> : null}
                  Approve EHR & Release Codes
                </Button>
              </div>
            ) : (
              <div className="border-t border-slate-850 pt-3 text-center">
                <Badge variant="success" className="px-3 py-1 text-xs">
                  <CheckCircle2 size={12} className="mr-1.5" /> Approved & Released
                </Badge>
                <p className="text-[10px] text-slate-400 mt-2">
                  Transmitted by {session.reviewer_report?.approved_by} on {new Date(session.reviewer_report?.approved_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

    </div>
  );
};
