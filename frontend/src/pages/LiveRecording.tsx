import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AudioRecorder } from "../components/AudioRecorder";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../components/ui/shadcn";
import { api } from "../services/api";
import { Sparkles, BrainCircuit, CheckSquare, Loader2, ArrowRight } from "lucide-react";

// Demo case for the OmniHealth Graph hackathon (patient "Robert Vance" -> graph P-9801)
const DEMO_TRANSCRIPT = `Doctor: Hello Mr. Vance, what brings you in today?
Patient: For two weeks my chest feels heavy and tight when I climb stairs. It goes away when I rest.
Doctor: This sounds like angina. I will order a 12-lead ECG and a blood glucose, and prescribe nitroglycerin 0.4 mg sublingual as needed.`;

export const LiveRecording: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(-1);

  const location = useLocation();
  const navigate = useNavigate();

  // Handle auto-selected query ID
  const queryParams = new URLSearchParams(location.search);
  const queryId = queryParams.get("id");

  useEffect(() => {
    const fetchActiveSessions = async () => {
      try {
        const list = await api.listSessions();
        // filter active ones
        const actives = list.filter((s: any) => s.status === "active");
        setSessions(actives);
        
        if (queryId) {
          setSelectedId(queryId);
        } else if (actives.length > 0) {
          setSelectedId(actives[0]._id);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchActiveSessions();
  }, [queryId]);

  const agentSteps = [
    { name: "Voice Segmenter", desc: "Whisper STT & speaker validation" },
    { name: "PII Sanitizer", desc: "Masking names, SSNs, DOBs" },
    { name: "Knowledge Agent", desc: "Querying ChromaDB Vector Guidelines" },
    { name: "Clinical SOAP Agent", desc: "Structuring EHR documents & FHIR" },
    { name: "Coding Agent", desc: "Extracting ICD-10 & CPT billing codes" },
    { name: "Compliance Agent", desc: "Auditing documentation CMS completeness" },
    { name: "Revenue Optimizer", desc: "Calculating recovery scores & leakages" },
    { name: "Lead Reviewer Agent", desc: "Aggregating outputs & citation check" }
  ];

  const handleProcess = async () => {
    if (!selectedId || !transcript) return;
    
    setIsProcessing(true);
    setActiveStep(0);

    // Simulate stepping through the Multi-Agent roadmaps for hackathon visualization
    const stepInterval = setInterval(() => {
      setActiveStep(prev => {
        if (prev < agentSteps.length - 1) {
          return prev + 1;
        } else {
          clearInterval(stepInterval);
          return prev;
        }
      });
    }, 1200);

    try {
      // Trigger FastAPI endpoint (runs the backend LangGraph Multi-Agent state flow)
      const res = await api.processSession(selectedId, transcript);
      clearInterval(stepInterval);
      setActiveStep(agentSteps.length); // complete
      
      // Auto-navigate to session detail view
      setTimeout(() => {
        navigate(`/sessions?id=${res._id}`);
      }, 1000);
      
    } catch (e) {
      clearInterval(stepInterval);
      alert("Agent engine processing encountered an error.");
      setIsProcessing(false);
      setActiveStep(-1);
    }
  };

  const currentSess = sessions.find(s => s._id === selectedId);

  return (
    <div className="space-y-6">
      
      <div>
        <h2 className="text-2xl font-bold text-slate-100 font-outfit">Consultation Voice Assistant</h2>
        <p className="text-sm text-slate-400 mt-1">Capture clinical conversations. Our multi-agent orchestrator will structure EHR and suggest codes.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recorders and target patient selector */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Session Target Patient</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-4 items-end">
                <div className="flex-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Active Patient Files</label>
                  <select
                    value={selectedId}
                    onChange={(e) => setSelectedId(e.target.value)}
                    disabled={isProcessing}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    {sessions.map(s => (
                      <option key={s._id} value={s._id}>
                        {s.patient_name} (DOB: {s.patient_dob})
                      </option>
                    ))}
                    {sessions.length === 0 && (
                      <option value="">No active sessions. Create a Patient File first.</option>
                    )}
                  </select>
                </div>
                <Button 
                  onClick={() => navigate("/sessions")} 
                  variant="secondary"
                  disabled={isProcessing}
                >
                  Create New File
                </Button>
              </div>
            </CardContent>
          </Card>

          {selectedId && (
            <AudioRecorder 
              sessionId={selectedId} 
              onTranscriptUpdate={setTranscript} 
            />
          )}

          {selectedId && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Transcript (editable)</CardTitle>
                  <Button variant="secondary" size="sm" onClick={() => setTranscript(DEMO_TRANSCRIPT)} disabled={isProcessing}>
                    Load demo case (Robert Vance)
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <textarea
                  rows={5}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  disabled={isProcessing}
                  placeholder="Record audio above, paste a transcript, or load the demo case..."
                  className="w-full rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
              </CardContent>
            </Card>
          )}

          {transcript && !isProcessing && (
            <Card>
              <CardContent className="p-4 flex justify-between items-center bg-cyan-950/15 border border-cyan-500/20 rounded-xl">
                <span className="text-xs text-cyan-300">Transcript captured. Ready to run clinical agents.</span>
                <Button onClick={handleProcess} className="animate-pulse">
                  <BrainCircuit size={16} className="mr-1.5" /> Optimize & Generate EHR
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Processing Roadmap / Agents list */}
        <div>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-cyan-400">
                <BrainCircuit size={18} />
                <span>Multi-Agent Roadmap</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              
              {!isProcessing ? (
                <div className="text-center py-12 text-slate-500 text-xs">
                  Roadmap will activate when agent pipeline execution begins.
                </div>
              ) : (
                <div className="space-y-4">
                  {agentSteps.map((step, idx) => {
                    const isCompleted = activeStep > idx;
                    const isActive = activeStep === idx;
                    
                    return (
                      <div key={idx} className="flex items-start space-x-3">
                        <div className="flex flex-col items-center">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border transition-all duration-300 ${
                            isCompleted ? "bg-emerald-500 border-emerald-500 text-white" :
                            isActive ? "bg-cyan-500 border-cyan-500 text-slate-950 animate-pulse scale-110" :
                            "bg-slate-900 border-slate-700 text-slate-400"
                          }`}>
                            {isCompleted ? "✓" : idx + 1}
                          </div>
                          {idx < agentSteps.length - 1 && (
                            <div className={`w-[2px] h-8 transition-colors duration-500 ${
                              isCompleted ? "bg-emerald-500" : "bg-slate-800"
                            }`}></div>
                          )}
                        </div>
                        <div>
                          <h4 className={`text-xs font-semibold ${
                            isActive ? "text-cyan-400" : isCompleted ? "text-slate-300" : "text-slate-500"
                          }`}>
                            {step.name}
                          </h4>
                          <p className="text-[10px] text-slate-500 mt-0.5">{step.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

            </CardContent>
          </Card>
        </div>

      </div>

    </div>
  );
};
