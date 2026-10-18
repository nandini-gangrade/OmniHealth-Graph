# PROGRESS.md: OmniHealth Graph refactor

**Resume instruction for a new Claude session:** read this file first, then continue with the first unchecked item. Do not redo completed work.

## Completed Steps
- [x] Step 1: removed `__pycache__`, `.DS_Store`, ChromaDB code/config/`rag_service.py`, stale `dist/`; no CSV files existed
- [x] Step 1: `backend/requirements.txt` per spec (+ python-multipart, websockets, bcrypt pin, pydantic[email], cryptography which the app needs)
- [x] Step 1: `core/config.py` reads `JWT_SECRET_KEY` / `FERNET_KEY` strictly from env (no fallbacks); `security.py` uses `FERNET_KEY` directly; `generate_env.py` + `.env.example` added
- [x] Step 1: CORS = localhost:5173, localhost:3000, regex `https://.*\.vercel\.app`
- [x] Step 2: `services/falkor_service.py` (`FalkorHealthService`): init_databases, verify_medical_necessity, check_cross_session_contraindications, record_encounter, get_department_compliance (+ extract_symptoms, check_unbundling, verify_necessity_from_diagnoses, infer_department, get_patient_memory)
- [x] Step 3: `agents/llm.py` Gemini (temp 0.1) + role-routed offline simulator (fixed old keyword routing bug) + angina demo fixtures
- [x] Step 3: clinical / coding / compliance agents + `graph.py` retrieval node use FalkorDB; `graph_provenance` stored on the session; startup hook calls `init_databases()`
- [x] Step 3: approval gate (409 unless alerts acknowledged) + encounter memory commit on approve; new `/api/graph/*` router
- [x] Step 4: `LiveRecording.tsx` editable transcript box + demo-case button; `SessionDetails.tsx` provenance pills, contraindication card, hospital brain card, ack checkbox; `api.ts` uses `VITE_API_BASE`; `vercel.json`
- [x] Deliverables: `preview.html`, `instructions.md`, `demo.md`, `pitch.md`
- [x] Verified: backend end-to-end against a real FalkorDB server (login → process → provenance → approve 409/200 → memory); frontend `tsc` + `vite build` pass

## Pending Steps
- [ ] Test with a real Gemini key (never run here; default model `gemini-1.5-pro` is likely retired, set `GEMINI_MODEL`)
- [ ] Visually check `preview.html` and the React UI in a browser with internet (Tailwind CDN was blocked in the build sandbox)
- [ ] Deploy: push to GitHub, Vercel for `frontend/`, host the backend, set `VITE_API_BASE`
- [ ] Record the demo video per `demo.md`

## Modified / Added Files
Backend: `requirements.txt`, `generate_env.py`, `.env.example`, `app/main.py`, `app/core/{config,security,database,logging_config}.py`, `app/agents/{llm,graph,clinical_agent,coding_agent,compliance_agent,revenue_agent,reviewer_agent}.py`, `app/services/{falkor_service,pii_service}.py`, `app/routers/{sessions,graph}.py`, `app/models/session.py`; deleted `app/services/rag_service.py`
Frontend: `src/pages/LiveRecording.tsx`, `src/components/SessionDetails.tsx`, `src/services/api.ts`, `vercel.json`, `.env.example`
Root: `preview.html`, `instructions.md`, `demo.md`, `pitch.md`, `PROGRESS.md`, `.gitignore`; original `.env` was removed (create a new one with `python backend/generate_env.py`)

## Next command / instruction
```
docker run -d -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
cd backend && python generate_env.py <GEMINI_KEY> && pip install -r requirements.txt && uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev
```
Then continue with the first unchecked Pending item.
