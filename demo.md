# OmniHealth Graph: 3-Minute Demo Recording Script

**Product Identity:** Intelligent Clinical Documentation & Revenue Optimization Assistant Powered by FalkorDB  
**Target Video Duration:** 3 Minutes (180 Seconds)  
**Tone:** Authoritative, clinically fluent, technical, and crisp.

---

## 🛠️ Recording Setup Checklist (Do This Before Hitting Record)
1. **FalkorDB Container Running:** `docker run -d -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest`
2. **Backend Server Running:** `http://localhost:8000` (Health check shows online)
3. **Frontend App Running:** `http://localhost:5173`
4. **Browser Tab 1:** `http://localhost:5173` (Logged in as `doctor@hospital.com`, on the Sessions screen)
5. **Browser Tab 2:** `http://localhost:3000` (FalkorDB Browser open on graph `patient_P-9801`, with query `MATCH (n) RETURN n` ready in the query bar)
6. **Clean Session State:** Ready to create a fresh session for `Robert Vance`.

---

## ⏱️ Video Script & Screen Action Timeline

### 0:00 – 0:40 | The Challenge: Clinician Burnout & The Vector RAG Flaw
- **On Screen:** Start on the OmniHealth Graph **Sessions Dashboard** (`http://localhost:5173/sessions`).
- **Action:** Click **New Session** button. Enter Patient Name `Robert Vance`, DOB `1960-05-12`, and click **Create Session**. The screen transitions to the Recording page.
- **Narrator (Say):**
  > *"Clinicians spend two hours on EHR paperwork for every single hour of patient care. Worse, hospitals lose 15% of their revenue to claim denials because documentation fails to prove medical necessity.*
  > 
  > *Most ambient AI tools use generic Vector RAG. But vector similarity is not a clinical proof. Semantic closeness cannot prove that a procedure was medically justified, cannot prevent procedure unbundling, and cannot remember a patient's historical medications across visits.*
  > 
  > *This is **OmniHealth Graph**—an enterprise Intelligent Clinical Documentation & Revenue Optimization Assistant where **FalkorDB** serves as the load-bearing context, reasoning, and memory layer across all three hackathon tracks."*

---

### 0:41 – 1:20 | Consultation Ingestion & Structured SOAP Notes
- **On Screen:** In the Recording page, click **Load demo case (Robert Vance)**. The sample doctor-patient dialogue appears in the Transcript box:
  ```
  Doctor: Hello Mr. Vance, what brings you in today?
  Patient: For two weeks my chest feels heavy and tight when I climb stairs. It goes away when I rest.
  Doctor: This sounds like angina. I will order a 12-lead ECG and a blood glucose, and prescribe nitroglycerin 0.4 mg sublingual as needed.
  ```
- **Action:** Click **Optimize & Generate EHR**. 
- **On Screen:** Watch the LangGraph state machine animate through the agent nodes: *Voice Ingestion ➔ PII Sanitizer ➔ FalkorDB Retrieval ➔ Clinical Documentation ➔ Medical Coding ➔ Compliance ➔ Revenue Integrity ➔ Reviewer*.
- **Action:** As the structured SOAP note appears, point your cursor to the **Subjective**, **Objective**, **Assessment**, and **Plan** sections.
- **Narrator (Say):**
  > *"When the consultation concludes, our LangGraph pipeline scrubs protected health information under HIPAA rules, extracts symptoms, and generates comprehensive, structured SOAP notes in real time.*
  > 
  > *Notice there is no vector store here. Our retrieval and validation nodes run direct Cypher queries against FalkorDB to anchor every single clinical entity."*

---

### 1:21 – 2:00 | Track 01: Coding Assistance & Documentation Gap Detection
- **On Screen:** Open the session details and switch to the **Billing Codes** tab. Scroll down to the **FalkorDB Provenance Trace** section.
- **Action:** Point your cursor to the multi-hop pill trail: 
  **`chest tightness ➔ I20.9 (Angina) ➔ 93000 (12-Lead ECG)`**
- **Action:** Scroll to CPT `93010` and point out the amber **Unbundling Warning** (CARC CO-97).
- **Narrator (Say):**
  > *"In **Track 01: Agents That Act on Connected Data**, our Medical Coding agent doesn't guess billing codes from semantic embeddings. It executes a multi-hop Cypher traversal: Symptom to Diagnosis to Procedure.*
  > 
  > *Here, chest tightness proves the medical necessity of CPT 93000 through Angina I20.9. That pill trail is the literal `nodes(path)` from the graph, providing an immutable audit trail.*
  > 
  > *Simultaneously, the graph checks NCCI procedure bundling. The LLM suggested billing CPT 93010 for ECG interpretation, but FalkorDB knows that 93000 already includes 93010. It flags the unbundling violation immediately, pre-empting a costly payer clawback."*

---

### 2:01 – 2:40 | Track 02: Cross-Session Patient Safety & Memory
- **On Screen:** Scroll up to the **Plan** section of the SOAP note, highlighting the prominent **Red Cross-Session Contraindication Alert**.
- **Action:** Switch to Browser Tab 2 (FalkorDB Browser at `http://localhost:3000`), run `MATCH (n) RETURN n` on graph `patient_P-9801`, and expand the nodes:
  `Patient(Robert Vance) ➔ Encounter(ENC-01) ➔ Medication(Sildenafil)`.
- **Narrator (Say):**
  > *"In **Track 02: Agent Memory & Coordination**, patient memory is structurally isolated: each patient lives in their own private subgraph, `patient_P-9801`.*
  > 
  > *Today, the doctor prescribed sublingual Nitroglycerin. But seven months ago, in Encounter ENC-01, Robert Vance was prescribed Sildenafil. A stateless model or vector chunk would miss this.*
  > 
  > *Our Clinical Agent traversed his historical active medications against pharmacological contraindication edges in our rules graph: Nitrates combined with PDE5 inhibitors cause fatal refractory hypotension. The alert is injected directly into the plan, saving the patient's life."*

---

### 2:41 – 3:00 | Track 03: Revenue Optimization, Human Validation & Sign-Off
- **On Screen:** Switch back to the UI (Browser Tab 1). Point to the right-hand column: **Hospital Brain: Cardiology** card.
- **Action:** Point out the denial hotspots (historical CARC CO-50 and CO-97 denial rates).
- **Action:** Scroll down to the **Sign-Off Panel**. Hover over the **Approve** button (demonstrating that it is disabled).
- **Action:** Check the **Contraindication Acknowledgement** checkbox. Click **Approve EHR & Release Codes**.
- **Action:** Switch to FalkorDB Browser (Tab 2), refresh the query: show the new Encounter node committed back into `patient_P-9801`.
- **Narrator (Say):**
  > *"In **Track 03: Company Brain**, our institutional hospital graph connects Departments, Supervising Physicians, and historical denial reasons, surfacing that cardiology ECGs are frequently challenged for bundling.*
  > 
  > *Finally, human-in-the-loop safety is enforced: the clinician cannot sign off past a critical drug contraindication without explicit acknowledgement. Upon approval, the encounter is committed back into the patient's graph memory.*
  > 
  > *OmniHealth Graph doesn't just draft notes—it proves necessity, eliminates unbundling, preserves patient memory, and protects hospital revenue. Powered by FalkorDB."*

---

## 💡 Troubleshooting & Fallback During Recording
- **If LLM Key has rate limits or network lag:** The system includes a built-in zero-dependency offline simulator that generates the exact same Robert Vance case with 100% fidelity. All graph traversals in FalkorDB remain live.
