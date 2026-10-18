# OmniHealth Graph: Setup Instructions

Everything below is copy-paste. Total time: about 15 minutes.

## 0. What you need installed
- Docker Desktop (for FalkorDB)
- Python 3.10+ and Node 18+
- (Optional) MongoDB. If it is not running, the backend automatically uses an embedded in-memory store.

## 1. Start FalkorDB (the graph engine)
```bash
docker run -d --name falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```
- Graph engine: `localhost:6379`
- FalkorDB Browser (visual graph explorer): http://localhost:3000
- Check it is up: `docker ps` should list `falkordb`.

## 2. Get a Gemini API key and create `.env`
1. Go to https://aistudio.google.com/apikey and sign in.
2. Click **Create API key** and copy it.
3. Generate your `.env` (random JWT + Fernet secrets are created for you):
```bash
cd backend
python generate_env.py PASTE_YOUR_GEMINI_KEY_HERE
```
This writes `backend/.env`. The app refuses to start if `JWT_SECRET_KEY` or `FERNET_KEY` are missing (no hardcoded fallbacks).

**No key?** Leave it empty (`python generate_env.py`). The app runs with the built-in offline simulator, and the FalkorDB graph logic is still 100% real.

**Model note:** the default is `GEMINI_MODEL=gemini-1.5-pro` as specified. Google has been retiring older Gemini models, so if the logs show a 404/model-not-found error, set `GEMINI_MODEL=` to a current model name (see https://ai.google.dev/gemini-api/docs/models) in `backend/.env`. The agents fall back to the simulator on LLM errors, so the demo never breaks.

## 3. Run the backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
Verify: open http://localhost:8000/health. You should see `"graph_engine": "online"` and graphs `clinical_rules`, `hospital_brain`, `patient_P-9801`.
API docs: http://localhost:8000/docs

## 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and log in with the seeded doctor account: `doctor@hospital.com` / `doctor123`.

## 5. Try the demo case
1. **Sessions → New Session**: patient name `Robert Vance`, any DOB. (The name maps to graph patient `P-9801`, who has active Sildenafil from encounter ENC-01.)
2. On the recording page click **Load demo case (Robert Vance)** (or paste the text below into the Transcript box), then click **Optimize & Generate EHR**:
```
Doctor: Hello Mr. Vance, what brings you in today?
Patient: For two weeks my chest feels heavy and tight when I climb stairs. It goes away when I rest.
Doctor: This sounds like angina. I will order a 12-lead ECG and a blood glucose, and prescribe nitroglycerin 0.4 mg sublingual as needed.
```
3. Open the session details. You will see the red contraindication card, the FalkorDB provenance pills, the unbundling flag, and the Hospital Brain card.
4. Try approving: you must tick the acknowledgement box (the API returns 409 otherwise). Approval writes the encounter into `patient_P-9801`.

Optional: open http://localhost:3000, pick graph `patient_P-9801`, run `MATCH (n) RETURN n` to see the memory graph grow.

## 6. Push to GitHub
```bash
cd healthcare_platform
git init
git add .
git commit -m "OmniHealth Graph: FalkorDB-powered healthcare agents"
git branch -M main
git remote add origin https://github.com/<you>/omnihealth-graph.git
git push -u origin main
```
`.gitignore` already excludes `.env`, `node_modules`, and `__pycache__`. Never commit `.env`.

## 7. Deploy the frontend to Vercel (free)
1. https://vercel.com → **Add New → Project** → import your GitHub repo.
2. **Root Directory:** `frontend`. Framework preset: Vite. Build command `npm run build`, output `dist`.
3. **Environment variable:** `VITE_API_BASE` = `https://<your-backend-url>/api`.
4. Deploy. `vercel.json` already handles SPA routing.

The backend allows CORS from `http://localhost:5173`, `http://localhost:3000` and any `*.vercel.app` origin.

**The backend must be hosted somewhere reachable** (Render, Railway, Fly.io, or your own machine through a tunnel such as `cloudflared tunnel --url http://localhost:8000`). Set the same env vars there (`JWT_SECRET_KEY`, `FERNET_KEY`, `GEMINI_API_KEY`, `FALKORDB_HOST/PORT/PASSWORD`) and point `FALKORDB_HOST` at a reachable FalkorDB (for example FalkorDB Cloud; check their current free tier). For a hackathon demo video, running everything locally is perfectly fine.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `/health` says `graph_engine: offline` | Docker container not running: re-run step 1, then restart uvicorn |
| `ValidationError: JWT_SECRET_KEY field required` | Run `python generate_env.py` inside `backend/` |
| Logged out / old sessions unreadable after regenerating `.env` | Expected: new `JWT_SECRET_KEY` invalidates tokens and a new `FERNET_KEY` cannot decrypt old stored transcripts. Log in again; with the in-memory store nothing is lost |
| Port 6379 already used | `docker run -d -p 6380:6379 ...` and set `FALKORDB_PORT=6380` |
| Frontend cannot reach API | Check `VITE_API_BASE` and that uvicorn is on port 8000 |
