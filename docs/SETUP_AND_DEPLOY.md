# Sightscreen - setup, LLM, GitHub, Render (follow in order)

> This is a NEW project. Use a NEW GitHub repo (for example `sightscreen`) and a NEW Render service so your original submission link stays untouched. Reuse the same Groq key.

## 0. Install once
- Python 3.10+ (python.org; on Windows tick "Add Python to PATH")
- Node.js 20 LTS (nodejs.org)
- Git (git-scm.com) and a free GitHub account
Check: `python --version`, `node --version`, `git --version` (use `python3` on Mac/Linux).

## 1. Run on your laptop (two terminals)
**Terminal 1 - backend**
```
cd Sightscreen/backend
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1      (if blocked: Set-ExecutionPolicy -Scope Process Bypass)
# Mac/Linux:           source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/health -> `{"status":"ok","ai_provider":"none"}`.

**Terminal 2 - frontend**
```
cd Sightscreen/frontend
npm install
npm run dev
```
Open http://localhost:5173 (the dev server forwards /api to port 8000, so nothing else to connect).

Run the tests: `cd backend && python -m pytest -q` (57 should pass).

## 2. Turn the LLM on (free)
1. Groq: console.groq.com -> API Keys -> Create key. (Or Gemini: aistudio.google.com/apikey.)
2. Stop the backend (Ctrl+C), set the key in that terminal, start it again:
   - Windows PowerShell: `$env:GROQ_API_KEY="paste-key"` then `python -m uvicorn app.main:app --reload --port 8000`
   - Mac/Linux: `export GROQ_API_KEY="paste-key"` then the same uvicorn command
   - Gemini instead: `GEMINI_API_KEY`
3. Reload the app. The sidebar chip changes to **AI on: groq**. /health shows `"ai_provider":"groq"`.
4. Play the replay: the Live Lens source line now says "AI (groq), verified against facts".
Never paste the key into code, GitHub, screenshots or the form.

## 2b. Protect the operations pages (recommended before sharing a public link)
Set `ADMIN_TOKEN` to a long random value (on your laptop in the same terminal as the key, on Render under Environment). Then Operations, AI traces and the AI quality evaluations ask for the token under Settings > Admin access. Fan-facing pages never need it.

## 3. Push to GitHub
1. github.com -> New repository -> name `sightscreen` -> Public -> Create (do not add a README).
2. In the unzipped Sightscreen folder:
```
git init
git add .
git commit -m "Sightscreen 2.0"
git branch -M main
git remote add origin https://github.com/<your-username>/sightscreen.git
git push -u origin main
```
(No git? On the repo page click "uploading an existing file" and drag in the contents of Sightscreen: Dockerfile, render.yaml, backend, frontend, docs. Not node_modules.)
3. The repo root must show `Dockerfile` and `render.yaml` directly.

## 4. Deploy on Render (one URL for UI + API)
1. render.com -> sign up with GitHub.
2. New -> Blueprint -> pick `sightscreen` -> Apply. (Or New -> Web Service -> pick repo -> Language: Docker -> Instance: Free.)
3. Wait for "Live" (3-6 minutes the first time).
4. Open `https://<name>.onrender.com/health` -> status ok.
5. Service -> Environment -> add `GROQ_API_KEY` (or `GEMINI_API_KEY`) -> Save. It redeploys in about a minute.
6. Open the main URL. The chip must say "AI on". Play the replay, try every page.
7. Copy the URL into `1_Sightscreen_Artifact_Link.docx` with your GitHub link.

## 5. Final check before the Google Form
- [ ] URL opens in a private/incognito window and on your phone
- [ ] Chip says AI on; a Live Lens card shows "AI (...)" as its source
- [ ] All pages work: Match room, Impact replay, What-if lab, Ask, Stats centre, Fantasy pulse, AI quality, Control room, Settings
- [ ] Copilot drawer: ask 'Explain Umpire's Call' (shows a cited passage); with a key set the Copilot button shows a green dot and the answer shows tool steps
- [ ] Command palette: Ctrl or Cmd + K, type 'hindi'
- [ ] Catch me up: briefing shows, Hinglish/Hindi switch works, Share and the link /?catchup=22 open on your phone
- [ ] Control room: Replay messy vendor feed shows Reconciled
- [ ] Support copilot: pick Ball 14.5 correction, ask the sample tickets, run the evaluation (expect 0 false resolutions)
- [ ] Language switch (Hinglish, Hindi) and I support change the Live Lens text
- [ ] AI quality: both runs complete (about 15 seconds each with the LLM on)
- [ ] Link document has the real URLs (no yellow placeholders)
- [ ] Open the URL again a few minutes before submitting (free instances sleep)

## Troubleshooting
| Problem | Fix |
|---|---|
| `uvicorn` not found | use `python -m uvicorn ...` and make sure the virtual environment is activated |
| PowerShell blocks activation | `Set-ExecutionPolicy -Scope Process Bypass` then activate again |
| Frontend says "Could not load the match" | the backend is not running on port 8000 |
| Render build fails at `npm ci` | `frontend/package-lock.json` was not uploaded |
| Render URL says Not Found | the Docker build did not copy the frontend; read the build log |
| Chip still says AI off on Render | key name typed wrong, or no redeploy yet; check Environment |
| AI on but answers say "rejected or unavailable" | model name changed; set `GROQ_MODEL` / `GEMINI_MODEL` to a current model from the provider docs |
| 429 "Too many requests" | the demo limits each IP to 60 requests a minute; wait a minute |
