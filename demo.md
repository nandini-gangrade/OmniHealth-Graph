# OmniHealth Graph: 3-Minute Demo Script

**Setup before recording:** FalkorDB running, backend + frontend up, logged in as the doctor, FalkorDB Browser (localhost:3000) open in a second tab on graph `patient_P-9801`, Fresh session.

## 0:00 – 0:20 · The hook (Sessions page)
**Screen:** Sessions list → click **New Session** → type `Robert Vance`, DOB → create.
**Say:** "Vector RAG retrieves text that *sounds* relevant. In healthcare that is not enough: a coding agent has to *prove* medical necessity, and a clinical agent has to remember that this patient is already on Sildenafil. OmniHealth Graph makes FalkorDB the load-bearing context, reasoning and memory layer. We enter all three tracks."

## 0:20 – 0:45 · Conversation → structured output
**Screen:** Recording page → click **Load demo case (Robert Vance)** → click **Optimize & Generate EHR**. Let the agent steps animate.
**Say:** "Speech-to-text feeds a LangGraph pipeline: PII sanitising, extraction, SOAP notes, ICD and CPT coding, compliance, revenue, review. Notice there is no vector store. The retrieval node runs Cypher against FalkorDB."

## 0:45 – 1:25 · Track 01: Agents that act on connected data
**Screen:** Open the session → **Billing Codes** tab, then scroll to the **FalkorDB Provenance Trace** card.
**Say:** "For every CPT code the coding agent runs a multi-hop query: Symptom to Diagnosis to Procedure. Here: *chest tightness → I20.9 → 93000*. That pill trail is the literal `nodes(path)` from the graph, so every billing decision is explainable and deterministic."
**Click:** Point to CPT 93010 marked **Gap**, and the amber unbundling banner.
**Say:** "The LLM also suggested 93010. The graph knows 93000 already includes 93010, so it flags unbundling before the claim is denied. No similarity score could do that."

## 1:25 – 2:10 · Track 02: Agent memory and coordination
**Screen:** Scroll up to the red **Cross-Session Contraindication Warning** and the Plan section of the SOAP note.
**Say:** "Today's visit prescribes nitroglycerin. Seven months ago, in encounter ENC-01, this patient was started on Sildenafil. Each patient lives in an isolated subgraph, `patient_P-9801`. The agent traversed his active medications against the contraindication edges in the rules graph: *nitroglycerin → Nitrate → PDE5 Inhibitor → sildenafil*, fatal refractory hypotension. The alert is inserted straight into the Plan."
**Screen:** Switch to FalkorDB Browser tab, run `MATCH (n) RETURN n` on `patient_P-9801` and show Patient → Encounter → Medication.
**Say:** "Tenant isolation is structural: one graph per patient, so memory cannot leak across patients."

## 2:10 – 2:35 · Track 03: Company brain
**Screen:** Right column → **Hospital Brain: Cardiology** card.
**Say:** "The institutional brain connects Departments, supervising physicians, frequently billed CPTs and historical denial reasons. The agent infers this is a Cardiology claim and surfaces that ECGs in this department have been denied for medical necessity and bundling, so the coder knows where the risk is. (This hospital data is synthetic for the demo.)"

## 2:35 – 3:00 · Human validation and close
**Screen:** Sign-Off panel → try **Approve** (button disabled) → tick the acknowledgement → **Approve EHR & Release Codes**. Switch to FalkorDB Browser and refresh: the new encounter node appears.
**Say:** "A clinician cannot approve past a graph-flagged contraindication without acknowledging it, and approval commits the encounter back into the patient's memory graph, so the next session is smarter. The graph is not a visualizer: it proves necessity, remembers history, and encodes institutional knowledge. OmniHealth Graph, powered by FalkorDB."

**Backup if the LLM key fails:** the simulator produces the same demo case; all graph results are still live.
