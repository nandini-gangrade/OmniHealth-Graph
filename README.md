# OmniHealth Graph
### Intelligent Clinical Documentation & Revenue Optimization Assistant Powered by FalkorDB

[![FalkorDB](https://img.shields.io/badge/Graph_Engine-FalkorDB-E23636.svg)](https://www.falkordb.com/)
[![Track 1](https://img.shields.io/badge/Track_01-Agents_on_Connected_Data-3B82F6.svg)](#-track-01-agents-that-act-on-connected-data)
[![Track 2](https://img.shields.io/badge/Track_02-Agent_Memory_%26_Coordination-10B981.svg)](#-track-02-agent-memory--coordination)
[![Track 3](https://img.shields.io/badge/Track_03-Company_Brain-8B5CF6.svg)](#-track-03-company-brain)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Submission for Graph Hacks: Context for AI Agents Powered by FalkorDB**  
> **Challenge:** *Intelligent Clinical Documentation & Revenue Optimization Assistant*  
> *Targeting all three tracks: Track 01 (Connected Data), Track 02 (Agent Memory & Coordination), and Track 03 (Company Brain).*

---

## 📌 Executive Summary

**OmniHealth Graph** is an enterprise-grade **Intelligent Clinical Documentation & Revenue Optimization Assistant** where **FalkorDB serves as the load-bearing context, reasoning, memory, and governance layer** alongside LangGraph-orchestrated specialized agents. 

Rather than treating the graph database as an auxiliary data store or passive visualizer, **FalkorDB actively shapes what every AI agent does**:
1. **Medical Necessity Proofs:** Proves deterministically through multi-hop Cypher traversals that clinical symptoms justify billing CPT procedures, surfacing literal `nodes(path)` pill trails to eliminate claim denials (CARC CO-50).
2. **Pre-Claim Unbundling Interception:** Navigates procedure hierarchy edges to block NCCI unbundling penalties (CARC CO-97) before claims leave the hospital.
3. **Cross-Session Safety & Multi-Tenant Memory:** Retains isolated longitudinal patient subgraphs (`patient_<id>`) to catch lethal drug-drug contraindications prescribed across visits months apart.
4. **Institutional Hospital Brain:** Mines enterprise claim denial hotspots and supervising physician hierarchies to protect hospital solvency.

---

## 🏆 How OmniHealth Graph Fulfills All 3 Hackathon Tracks

| Track | Requirement | How FalkorDB Drives the Agent | Cypher Traversal In Action |
| :--- | :--- | :--- | :--- |
| **Track 01: Agents That Act on Connected Data** | *"The graph has to shape what the agent does, not sit on the side"* | Medical coding & compliance agents traverse `clinical_rules` to evaluate necessity. If no graph path links Symptom ➔ Diagnosis ➔ Procedure, the code is flagged as unproven and the claim is gated. Unbundling edges intercept bundled components. | `MATCH path = (s:Symptom)-[:INDICATES]->(d:Diagnosis)-[:SUPPORTS_NECESSITY]->(p:Procedure {code: $c})` |
| **Track 02: Agent Memory & Coordination** | *"Agent memory across sessions with multi-tenant graph isolation"* | Every patient has an isolated subgraph (`patient_<id>`). When new medications are prescribed, the clinical agent traverses past encounters against pharmacovigilance contraindication rules, hard-locking the approval button until acknowledged. | `MATCH (p:Patient)-[:HAS_ACTIVE_MED]->(m) ... MATCH path = (new:Drug)-[:IN_CLASS]->()-[:CONTRAINDICATED_WITH]-()<-[:IN_CLASS]-(active:Drug)` |
| **Track 03: Company Brain** | *"Institutional knowledge & revenue optimization"* | Models the hospital's operational brain (`hospital_brain`), mapping Departments, Supervising Physicians, frequently billed CPTs, and historical denial reasons (CARC codes) to alert clinicians of denial patterns before submission. | `MATCH path = (d:Department)-[:FREQUENTLY_BILLS]->(c:CPT)-[:DENIED_FOR]->(r:DenialReason)` |

---

## 🎯 Problem Statement & Solution Overview

### 📋 The Challenge: Intelligent Clinical Documentation & Revenue Optimization Assistant

> **Description:**  
> Healthcare providers face an unsustainable administrative burden, spending **over 2 hours on EHR data entry and documentation for every 1 hour of direct patient care**, leading to severe clinician burnout. At the same time, healthcare organizations lose **$260+ billion annually** to claim denials, downcoding, and revenue leakage caused by missing documentation, improper medical coding, unbundled procedures, and uncaptured clinical services.  
>  
> Clinical consultations are inherently unstructured, fast-paced dialogues. Manually translating these conversations into compliant clinical notes, discharge summaries, and billing-ready documentation is error-prone, slow, and labor-intensive. Furthermore, navigating complex billing rules, National Correct Coding Initiative (NCCI) bundling edits, and payer medical necessity guidelines creates significant friction between clinical care and revenue cycle management.

### ⚠️ Why Conventional Generative AI & Flat Vector Search Fall Short
Many modern clinical tools attempt to address this crisis using generic Large Language Models paired with flat **Vector RAG**. However, vector similarity is fundamentally insufficient for healthcare compliance and billing:
1. **Semantic Closeness ≠ Clinical Proof:** A vector cosine similarity score of `0.85` cannot prove to a CMS auditor or insurance payer that an ECG or lab test was legally justified by exertional angina. Payers demand deterministic, explainable necessity links.
2. **Blind to Relational Hierarchies & Unbundling:** A flat vector index cannot determine if CPT `93010` (ECG interpretation) is an unbundled sub-component of CPT `93000` (complete 12-lead ECG), triggering automated CARC CO-97 denial penalties and clawbacks.
3. **Amnesia Across Patient Encounters:** Flat vector stores cannot reliably isolate multi-tenant longitudinal patient histories, risking cross-patient hallucinations and missing lethal contraindications from medications prescribed months earlier.

---

### 💡 The Solution: OmniHealth Graph

**OmniHealth Graph** is an AI-powered healthcare documentation and revenue optimization assistant that listens to doctor-patient conversations, automatically generates structured clinical documentation, recommends appropriate medical codes, and identifies potential revenue leakage opportunities.

By leveraging **Generative AI, Speech-to-Text, Natural Language Processing, and Medical Large Language Models (LLMs)** alongside **FalkorDB's Graph Engine**, the system converts unstructured clinical conversations into compliant clinical notes, discharge summaries, and billing-ready documentation. The solution provides intelligent coding recommendations, highlights documentation gaps, and supports healthcare professionals in delivering better patient care while reducing clinician burnout:

* 🎙️ **Ambient Consultation Ingestion:** Listens to ambient doctor-patient consultations, applies HIPAA Safe Harbor de-identification, and generates compliant **SOAP notes**, **visit summaries**, **discharge summaries**, and **EHR-ready records**.
* 🏷️ **Intelligent Coding & Medical Necessity Proofs:** Automatically extracts clinical entities and recommends appropriate **ICD-10** diagnosis and **CPT** procedure codes. Uses FalkorDB graph traversals (`Symptom ➔ Diagnosis ➔ Procedure`) to produce deterministic medical necessity proof trails that eliminate CARC CO-50 claim denials.
* 💰 **Pre-Claim Revenue Leakage & Compliance Optimization:** Identifies documentation gaps that impact reimbursement, highlights unbilled high-value clinical services, and blocks NCCI unbundling penalties (CARC CO-97) before claims leave the hospital.
* 🛡️ **Longitudinal Multi-Tenant Patient Memory:** Isolates patient subgraphs (`patient_<id>`) to remember active medications and past diagnoses across sessions, hard-locking clinician approval if lethal drug contraindications are detected.
* 🏥 **Institutional Hospital Brain:** Models department denial patterns, billing frequencies, and supervising physician hierarchies to guide revenue cycle teams on denial prevention.
* 🖥️ **Intuitive Clinician & Revenue Cycle Dashboard:** Provides an interactive dashboard enabling clinicians, medical coders, compliance auditors, and revenue cycle teams to review AI-generated notes, validate coding recommendations, inspect visual graph provenance pills, monitor documentation quality metrics, and track revenue recovery.

---

### 🛡️ Data Considerations & Responsible AI

* **Synthetic & Anonymized Healthcare Datasets:** The solution utilizes synthetic and anonymized healthcare datasets, including clinical consultation transcripts, medical notes, electronic health record (EHR) samples, coding guidelines, billing records, reimbursement policies, and medical terminology libraries.
* **Privacy-Safe & Zero Real Patient Information:** All datasets are strictly privacy-safe, free from real patient information, and engineered to demonstrate secure handling of sensitive healthcare data while maintaining compliance with healthcare regulations (HIPAA Safe Harbor de-identification, 256-bit Fernet encryption at rest).
* **Responsible & Trustworthy AI Principles:** Combines creative graph-native approaches with strict clinical governance. AI agents never autonomously release claims without human review; clinicians retain full editorial authority and must explicitly acknowledge safety alerts.

---

### 🚀 Expected Outcomes & Value Delivered

The solution automatically transcribes and analyzes doctor-patient consultations to generate structured clinical documentation such as SOAP notes, visit summaries, discharge summaries, and EHR-ready records. It recommends appropriate ICD and CPT codes, identifies missing documentation that may impact reimbursement, and highlights potential revenue leakage opportunities:

* **Reduced Manual Documentation Effort:** Drastically lowers administrative burden and clinician burnout by turning voice conversations into finished notes in seconds.
* **Improved Coding Accuracy:** Anchors billing codes to verifiable clinical symptoms and medical necessity paths, eliminating coding hallucinations.
* **Faster Claim Preparation:** Accelerates billing workflows by delivering audit-ready, pre-validated claim packages with zero manual cross-referencing.
* **Enhanced Compliance & Denial Prevention:** Eliminates costly NCCI unbundling penalties (CO-97) and medical necessity denials (CO-50) before submission.
* **Streamlined Multi-Disciplinary Workflows:** Empowers doctors, coders, compliance auditors, and administrators with intuitive role-based dashboards to monitor documentation quality metrics and track revenue optimization opportunities.

---

## 🔄 Multi-Agent System Architecture (LangGraph)

Our 8-node LangGraph state machine orchestrates specialized agents with FalkorDB at the core:

```text
          [ Ambient Consultation / Audio File ]
                          |
                          v
                 [ 1. Voice Ingestion ]
                          |
                          v
                  [ 2. PII Sanitizer ]
                   (HIPAA Safe Harbor)
                          |
                          v
             +------------------------------+
             | 3. FalkorDB Retrieval Node   |
             | (symptoms + patient memory)  |
             +--------------+---------------+
                            |
                            v
                 [ 4. Clinical SOAP Agent ]
                            |
                            v
             +------------------------------+
             | 5. Medical Coding Agent      |
             +--------------+---------------+
                            |
                            v
             [ FalkorDB Medical Necessity Traversal ]
                            |
                            v
             +------------------------------+
             | 6. Compliance & Audit Node   |
             +--------------+---------------+
                            |
                            v
                [ FalkorDB NCCI Unbundling Traversal ]
                            |
                            v
             +------------------------------+
             | 7. Revenue & Hospital Brain  |
             +--------------+---------------+
                            |
                            v
             [ FalkorDB Institutional Denial Analytics ]
                            |
                            v
             +------------------------------+
             | 8. Reviewer & Guardrails     |
             +--------------+---------------+
                            |
                            v
             [ Cross-Session Contraindication Gate ]
                            |
                            v
              [ Locked Approval Gate:
                Doctor Acknowledges ]
                            |
                            v
              [ Idempotent FalkorDB Writeback ]
                            |
                            v
                 (Updates patient_<id> memory)
```

---
## 🕸️ Graph Data Model in FalkorDB

Hosted across three graph families within FalkorDB:

```text
TRACK 01: Clinical Rules Engine (clinical_rules)

[Symptom: chest tightness]
          |
          | INDICATES
          v
[Diagnosis: I20.9 Angina]
          |
          | SUPPORTS_NECESSITY
          v
[Procedure: 93000 12-Lead ECG]
          |
          | INCLUDES
          v
[Procedure: 93010 ECG Interp]


[Drug: nitroglycerin] --IN_CLASS--> [DrugClass: Nitrate]
                                             |
                                             | CONTRAINDICATED_WITH
                                             | Fatal Refractory Hypotension
                                             |
                                             v
[Drug: sildenafil] ----IN_CLASS----> [DrugClass: PDE5 Inhibitor]


TRACK 02: Multi-Tenant Patient Memory (patient_P-9801)

[Patient: Robert Vance P-9801]
          |
          +---- HAD_ENCOUNTER ----> [Encounter: ENC-01]
          |                         Date: 2026-03-14
          |
          +---- HAD_ENCOUNTER ----> [Encounter: ENC-02]
                                    Date: Today

[Encounter: ENC-01] ---- PRESCRIBED ----> [Medication: Sildenafil 50mg]
                                                  ^
                                                  |
[Patient: Robert Vance P-9801] -- HAS_ACTIVE_MED -+

[Encounter: ENC-02] ---- PRESCRIBED ----> [Medication: Nitroglycerin 0.4mg]

[Encounter: ENC-02] ---- DIAGNOSED -----> [Condition: Angina pectoris]


TRACK 03: Institutional Hospital Brain (hospital_brain)

[Department: Cardiology]
          |
          +---- SUPERVISED_BY ----> [Physician: Dr. Meera Iyer]
          |
          +---- FREQUENTLY_BILLS --> [CPT: 93000]
                                            |
                                            +---- DENIED_FOR ----> [DenialReason: CO-50 Medical Necessity]
                                            |
                                            +---- DENIED_FOR ----> [DenialReason: CO-97 Unbundling]


CROSS-GRAPH TRAVERSAL INTERSECTIONS

[Medication: Sildenafil 50mg]
          - - - Resolved in Rules - - -> [Drug: sildenafil]

[Medication: Nitroglycerin 0.4mg]
          - - - Resolved in Rules - - -> [Drug: nitroglycerin]

[Procedure: 93000 12-Lead ECG]
          - - - Resolved in Brain - - -> [CPT: 93000]
```

### Graph Schema Specifications

[Google Drive — Graph Schema Specifications](https://drive.google.com/file/d/1WSfj9CppZfFpID9ZBmPxuRA9_68aHYc_/view?usp=sharing)

1. **`clinical_rules` Graph (Track 01):**
   - **Node Labels:** `(:Symptom {name, aliases})`, `(:Diagnosis {code, description})`, `(:Procedure {code, description})`, `(:Drug {name, aliases})`, `(:DrugClass {name})`.
   - **Relationship Types:** `[:INDICATES]`, `[:SUPPORTS_NECESSITY]`, `[:INCLUDES]`, `[:IN_CLASS]`, `[:CONTRAINDICATED_WITH {severity, effect}]`.

2. **`patient_<id>` Subgraphs (Track 02 - Multi-Tenant Isolation):**
   - **Node Labels:** `(:Patient {id, name})`, `(:Encounter {id, date})`, `(:Condition {name})`, `(:Medication {name})`.
   - **Relationship Types:** `[:HAD_ENCOUNTER]`, `[:DIAGNOSED]`, `[:PRESCRIBED]`, `[:HAS_ACTIVE_MED]`.

3. **`hospital_brain` Graph (Track 03):**
   - **Node Labels:** `(:Department {name})`, `(:Physician {name})`, `(:CPT {code, name})`, `(:DenialReason {code, name})`.
   - **Relationship Types:** `[:SUPERVISED_BY]`, `[:FREQUENTLY_BILLS {count}]`, `[:DENIED_FOR {count}]`.

---

## ⚡ Core Cypher Queries That Drive the Agents

### 1. Multi-Hop Medical Necessity Proof (Track 01)
```cypher
MATCH path = (s:Symptom)-[:INDICATES]->(d:Diagnosis)-[:SUPPORTS_NECESSITY]->(p:Procedure {code: $code})
WHERE s.name IN $symptoms
RETURN [n IN nodes(path) | coalesce(n.name, n.code)] AS trace_path, d.code AS icd, p.code AS cpt
ORDER BY d.code LIMIT 1
```
* **Output in UI:** `chest tightness ➔ I20.9 ➔ 93000` (rendered as visual provenance pills).

### 2. NCCI Procedure Unbundling Detection (Track 01)
```cypher
MATCH path = (a:Procedure)-[:INCLUDES]->(b:Procedure)
WHERE a.code IN $cpt_codes AND b.code IN $cpt_codes
RETURN a.code AS comprehensive, b.code AS component, [n IN nodes(path) | n.code] AS trace_path
```
* **Output in UI:** Flags CPT `93010` because CPT `93000` already includes it (preventing CARC CO-97 denial).

### 3. Cross-Session Patient Memory & Pharmacovigilance (Track 02)
```cypher
// Step 1: Query historical active medications from isolated patient subgraph
MATCH (p:Patient {id: $patient_id})-[:HAS_ACTIVE_MED]->(m:Medication)<-[:PRESCRIBED]-(e:Encounter)
RETURN m.name AS med_name, e.id AS encounter_id, e.date AS encounter_date

// Step 2: Multi-hop drug-class contraindication traversal in rules graph
MATCH path = (new:Drug {name: $new_drug})-[:IN_CLASS]->(:DrugClass)-[r:CONTRAINDICATED_WITH]-(:DrugClass)<-[:IN_CLASS]-(active:Drug)
WHERE active.name IN $active_med_names
RETURN active.name, r.severity, r.effect, [n IN nodes(path) | n.name] AS trace_path
```
* **Output in UI:** Red Alert Card intercepting `Nitroglycerin` with active `Sildenafil` (`Fatal refractory hypotension`).

### 4. Idempotent Encounter Memory Writeback (Track 02)
```cypher
MERGE (p:Patient {id: $pid}) SET p.name = coalesce($name, p.name)
MERGE (p)-[:HAD_ENCOUNTER]->(e:Encounter {id: $eid}) SET e.date = $date
MERGE (e)-[:DIAGNOSED]->(c:Condition {name: $condition})
MERGE (m:Medication {name: $medication})
MERGE (e)-[:PRESCRIBED]->(m)
MERGE (p)-[:HAS_ACTIVE_MED]->(m)
```
* **Outcome:** Commits the encounter into `patient_<id>` so future encounters immediately inherit this context.

### 5. Institutional Hospital Brain Denial Analytics (Track 03)
```cypher
MATCH path = (d:Department {name: $department})-[b:FREQUENTLY_BILLS]->(c:CPT)-[x:DENIED_FOR]->(r:DenialReason)
RETURN c.code, c.name, b.count, r.code, r.name, x.count, [n IN nodes(path) | coalesce(n.name, n.code)] AS trace_path
ORDER BY x.count DESC
```
* **Output in UI:** Surfaces Cardiology historical denial rates (CO-50 and CO-97) to the reviewer.

---

## 🚀 Quickstart & Local Setup Instructions

The platform uses a **Dual-Engine Architecture**: it connects directly to **FalkorDB Cloud** (active) or local Docker, with an embedded **zero-latency in-memory graph fallback** so the entire platform works out of the box without external dependencies.

### Prerequisites
* Python 3.10+ (tested on Python 3.10 - 3.14)
* Node.js 18+

### Step 1: Start Backend Server
```bash
git clone https://github.com/nandini-gangrade/OmniHealth-Graph.git
cd healthcare_platform/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (starts on http://localhost:8000)
uvicorn app.main:app --port 8000 --reload
```
* **Backend API:** `http://localhost:8000`
* **Swagger Interactive Docs:** `http://localhost:8000/docs`
* **Health Check Probe:** `http://localhost:8000/health`

### Step 2: Start Frontend Application
In a second terminal window:
```bash
cd healthcare_platform/frontend
npm install
npm run dev
```
* **Open in Browser:** `http://localhost:5173`

---

## 🔑 Demo Personas & Login Credentials

Pre-seeded role-based accounts ready for testing:

| Role | Username / Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Clinician (Doctor)** | `doctor@hospital.com` | `doctor123` | Patient Ingestion, Audio Playback, SOAP Notes, Sign-Off Gate |
| **Medical Coder** | `coder@hospital.com` | `coder123` | Code Audit, NCCI Unbundling Review, CPT Overrides |
| **Compliance Auditor**| `auditor@hospital.com` | `auditor123` | CARC Denial Analytics, Provenance Trail Inspections |
| **Hospital Admin** | `admin@hospital.com` | `admin123` | Full System Audit Logs, Department Compliance Oversight |

---

## 🧪 Live Demo Case Walkthrough (Robert Vance)

To experience the full multi-track workflow in 2 minutes:

1. **Sign in** at `http://localhost:5173` as `doctor@hospital.com` / `doctor123`.
2. Click **New Session** → Enter Patient Name: `Robert Vance`, DOB: `1960-05-12`, Department: `Cardiology` → Click **Create Session**. *(Automatically binds to FalkorDB tenant graph `patient_P-9801`)*.
3. Click **Play Consultation Audio** to hear the audio dialogue, then click **Load demo case (Robert Vance)**:
   ```text
   Doctor: Hello Mr. Vance, what brings you in today?
   Patient: For two weeks my chest feels heavy and tight when I climb stairs. It goes away when I rest.
   Doctor: This sounds like angina. I will order a 12-lead ECG and a blood glucose, and prescribe nitroglycerin 0.4 mg sublingual as needed.
   ```
4. Click **Optimize & Generate EHR**. Watch the LangGraph state machine orchestrate the agent pipeline.
5. **Inspect the FalkorDB Clinical Intelligence:**
   * **Red Contraindication Alert (Track 02):** Active Sildenafil from `ENC-01` conflicts with prescribed Nitroglycerin (`Fatal refractory hypotension`). Shows rose pill trail: `nitroglycerin ➔ Nitrate ➔ PDE5 Inhibitor ➔ sildenafil`.
   * **Medical Necessity Trace (Track 01):** Under CPT `93000`, see the green pill trail: `chest tightness ➔ I20.9 ➔ 93000`.
   * **NCCI Unbundling Flag (Track 01):** Amber warning on CPT `93010` (included in `93000`).
   * **Hospital Brain (Track 03):** Cardiology denial hotspots (CARC CO-50 and CO-97).
6. **Enforced Human-in-the-Loop Sign-Off:**
   * Notice the **Approve EHR & Release Codes** button is **locked/disabled**.
   * Check the safety acknowledgement checkbox: *"I have reviewed the 1 graph-flagged contraindication(s) and take clinical responsibility."*
   * Click **Approve EHR & Release Codes**. The encounter is committed into FalkorDB `patient_P-9801`.

---

## 📁 Repository Directory Structure

```
healthcare_platform/
├── README.md                      # Comprehensive hackathon presentation guide
├── backend/
│   ├── .env                       # Clean environment variables
│   ├── generate_env.py            # Automated cryptographic secret generator
│   ├── requirements.txt           # Backend dependencies (FastAPI, FalkorDB, LangGraph)
│   └── app/
│       ├── main.py                # FastAPI app initialization & graph health probe
│       ├── core/
│       │   ├── config.py          # Pydantic settings with FalkorDB Cloud & SSL support
│       │   └── security.py        # Fernet PHI encryption & JWT role verification
│       ├── services/
│       │   ├── falkor_service.py  # Load-bearing FalkorDB service (Cloud + 0ms Fallback)
│       │   └── pii_service.py     # HIPAA Safe Harbor de-identification engine
│       ├── agents/
│       │   ├── graph.py           # Compiled LangGraph state machine (8 agent nodes)
│       │   ├── clinical_agent.py  # Structured SOAP & FHIR Bundle generation
│       │   ├── coding_agent.py    # FalkorDB necessity traversal engine
│       │   ├── compliance_agent.py# NCCI bundling & documentation audit
│       │   ├── revenue_agent.py   # Leakage recovery & CARC denial optimization
│       │   └── reviewer_agent.py  # Human sign-off & safety gate enforcement
│       └── routers/
│           ├── auth.py            # Role-based OAuth2 authentication
│           ├── sessions.py        # Clinical encounter lifecycle & writeback
│           └── graph.py           # FalkorDB Cypher endpoints
└── frontend/
    ├── package.json               # Frontend dependencies (React, Vite, Lucide)
    ├── vercel.json                # Vercel SPA deployment configuration
    ├── public/voices/             # Consultation audio asset (consultation_vance.mp3)
    └── src/
        ├── pages/
        │   ├── LiveRecording.tsx  # Ambient voice ingestion & agent execution
        │   └── Sessions.tsx       # Encounter manager & status overview
        ├── components/
        │   ├── SessionDetails.tsx # SOAP notes, provenance pills, contraindication alerts
        │   └── AudioRecorder.tsx  # WebSocket audio streaming & speech-to-text
        └── services/
            └── api.ts             # REST client for backend agent pipeline
```

---

## 🔒 Security, Compliance & Governance
* **Deterministic Proof Paths:** Billing codes are anchored to Cypher graph traversals—preventing LLM coding hallucinations.
* **HIPAA Safe Harbor Compliance:** All patient transcripts are scrubbed of PII and encrypted at rest with Fernet 256-bit keys before database storage.
* **Non-Bypassable Clinical Governance:** AI agents never autonomously release billing claims. Clinicians retain full editorial control and must explicitly acknowledge contraindications to sign off.

---

*Healthcare AI shouldn't guess. With FalkorDB, we can prove it.*
