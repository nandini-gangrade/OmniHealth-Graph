# OmniHealth Graph: Devpost Submission Copy

**Tagline:** Healthcare AI agents that prove, remember, and learn, with FalkorDB as the reasoning layer.

## The problem: vector RAG is the wrong tool for clinical coding
Ambient clinical documentation tools turn conversations into SOAP notes and billing codes. Most pair an LLM with vector search over guidelines. That breaks down exactly where healthcare is least forgiving:
- **Similarity is not necessity.** Payers deny claims when a procedure is not *linked* to a supporting diagnosis. A vector hit that "sounds like" a guideline is not a proof.
- **No memory across visits.** A stateless agent cannot know that a drug started months ago is dangerous with today's prescription.
- **No explainability.** "The embedding was close" does not survive an audit, a denial appeal, or a clinician's scrutiny.
- **Institutional knowledge is relational.** Which department bills which codes, who supervises them, and why claims get denied are relationships, not paragraphs.

## The solution
OmniHealth Graph refactors a multi-agent documentation platform so **FalkorDB is the context, reasoning and memory layer**. ChromaDB is gone entirely. Every major agent decision returns a deterministic `nodes(path)` trace.

Workflow: doctor-patient conversation → speech-to-text → clinical extraction → SOAP notes and ICD/CPT coding → documentation-gap detection → revenue-leakage insights → human validation with graph provenance → billing finalization.

### Track 01: Agents that act on connected data
Coding and compliance agents run multi-hop Cypher (Symptom → Diagnosis → Procedure) to prove medical necessity per CPT code, and traverse `INCLUDES` edges to catch NCCI-style unbundling (for example 93010 billed with 93000). The UI renders the result as a pill trail: *chest tightness → I20.9 → 93000*.

### Track 02: Agent memory and coordination
Each patient has an isolated subgraph (`patient_<id>`) holding encounters, conditions and active medications across sessions. When a new prescription is drafted, the clinical agent traverses historical medications against drug-class contraindication edges (for example Nitrate vs PDE5 inhibitor) and inserts an alert into the Plan. Approved encounters are written back, so memory compounds.

### Track 03: Company brain
A `hospital_brain` graph links Departments, Supervising Physicians, frequently billed CPTs and historical denial reasons (real CARC codes such as CO-50 and CO-97). The compliance agent infers the owning department and surfaces its denial patterns at review time.

## How we built it
FalkorDB (Cypher, one graph per tenant) · FastAPI · LangGraph · Gemini via `langchain-google-genai` at temperature 0.1 · MongoDB with embedded fallback · React + Vite + Tailwind · JWT auth, Fernet-encrypted PHI, audit log.

## Why it is graph-native
- Medical necessity is a *path query*; contraindications are *edges between classes*; patient memory is *a subgraph per tenant*; institutional knowledge is *a connected brain*.
- The LLM drafts; the graph verifies. Deterministic traces make every decision auditable.
- Human-in-the-loop is enforced by the system: approval is blocked until flagged contraindications are acknowledged.

## Honest notes
Ground-truth ICD-10-CM, CPT and CARC codes and the drug-class interactions are real, but this is a hackathon prototype and **not a medical device**; the interaction set is a small seed, and hospital_brain figures and patient P-9801 are synthetic demo data.

## Why it should win
It enters all three tracks with one coherent system where removing the graph breaks the product, not just its visuals. It ships a verifiable, reproducible demo (one Docker command), explainable traces on every decision, and a safety behavior that a vector store structurally cannot provide.
