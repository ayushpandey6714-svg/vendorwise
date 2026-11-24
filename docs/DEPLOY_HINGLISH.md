# VendorWise ko public link par kaise laayein

## Pehle project ka status samjho

**Local portfolio demo ban gaya hai. Public website abhi deploy nahi hui.**

- FastAPI = PDF extraction, comparison, calculations aur Q&A ka backend.
- Streamlit = browser mein dikhne wali screen.
- Docker = dono ko ek package mein chalata hai.
- Render = us Docker package ko internet par run karke shareable URL deta hai.

Docker ko apne laptop par run karna aur public hosting karna alag steps hain. `localhost` sirf us computer ka address hai; woh link doston ke laptop par tumhara app nahi kholega.

## Is deployment mein kya milega?

Ek **public synthetic sample demo**: visitors A/B/C quotations compare kar sakte hain, requirements badal sakte hain, source evidence dekh sakte hain aur fixture Q&A try kar sakte hain. No live LLM calls, no API key, no personal PDF uploads. UI clearly demo mode dikhati hai. Public image TF-IDF local retrieval use karti hai; full local project mein BGE semantic embeddings available hain.

Local OpenRouter live sample workflow verify ho gaya: three-PDF extraction, comparison, what-if, cited battery answer aur report endpoint. Public live AI enable karne se pehle authentication aur usage limits chahiye. Docker public-demo mode mein `live` mode reject karta hai; public sample demo live AI nahi chalata.

## Route A — Public URL chahiye: GitHub + Render

Is route ke liye laptop par Docker Desktop install karna zaroori nahi: Render Docker image build karega. GitHub aur Render accounts chahiye. Account login apne browser mein karo; password/token chat mein mat bhejo.

1. [GitHub](https://github.com/new) par `vendorwise` naam ka repository banao.
2. Repository mein **Add file → Upload files** se project folder ke **andar ki files/folders** upload karo. Repository ke top level par `Dockerfile`, `requirements-docker.txt`, `streamlit_app.py` aur `vendorwise/` hone chahiye. ZIP file upload mat karna. `.env`, `.venv`, `data`, `work` aur `deployment-backup-*` folders upload mat karna. Private repo bhi supported hai agar Render ko access diya ho.
3. [Render Dashboard](https://dashboard.render.com/) mein **New → Web Service** kholo. GitHub connect karo aur `vendorwise` repo select karo.
4. Settings: **Language/Runtime = Docker**, **Dockerfile path = ./Dockerfile**, **Root Directory = blank** (agar files repo root mein hain). **Instance type = Free** select karo if available. Is small demo ke liye paid resources automatically select mat karo.
5. **Health Check Path = /_stcore/health**. Environment variables mein `PORT=7860` set karo. Baaki demo defaults Dockerfile mein already hain. API key add mat karo. Docker command override blank rakho.
6. **Create Web Service** dabao aur build logs dekho. `Live` status ke baad Render jo HTTPS URL de, wahi friends/recruiters ko share karo. URL app create hone ke baad milega; abhi koi real public URL create nahi hua.

Render browser button ka label thoda badal sakta hai. Current official instructions: [Web Services](https://render.com/docs/web-services).

Free service idle rehne par sleep hoti hai, next visit par start hone mein time lag sakta hai, aur restart/redeploy par analysis data lost ho sakta hai. Memory/usage limits bhi apply hote hain. Agar logs memory exhaustion dikhayein toh deployment successful claim mat karna; logs ke basis par memory usage reduce karo ya hosting capacity choose karo. [Free service limitations](https://render.com/docs/free).

### Agar folder GitHub mein nested aa gaya

Agar GitHub par `vendorwise/Dockerfile` dikhta hai, toh Render **Root Directory = vendorwise** rakho. Dockerfile path us root ke relative `./Dockerfile` hi rahega.

## Route B — Pehle apne laptop par Docker try karna hai

1. [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) install/start karo, Linux containers use karo. Windows/WSL requirements installer ki official instructions se follow karo.
2. PowerShell kholo aur run karo:

```powershell
cd 'D:\VendorWise\vendorwise'
docker compose up --build -d
```

3. Browser mein [http://localhost:7860](http://localhost:7860) kholo. First build ko dependencies download karni hongi.
4. Logs dekhne ke liye:

```powershell
docker compose logs -f
```

5. Band karne ke liye:

```powershell
docker compose down
```

Ye local Docker demo hai. Public link ke liye Route A follow karo. Port 8000 internal hai; browser ko Streamlit ka port 7860 milta hai, aur Streamlit FastAPI ko container ke andar call karta hai.

## Technical details, sirf jab zaroorat ho

- `scripts/serve_container.py` FastAPI ko loopback port 8000 par start karta hai; healthy hone ke baad Streamlit ko hosting ke `PORT` par start karta hai. Koi service fail ho toh doosri bhi stop hoti hai, taaki host clean restart kar sake.
- Container non-root user se run hota hai. `.dockerignore` keys, venv aur local analysis files ko build se exclude karta hai.
- Only Streamlit is public. Backend endpoints are not exposed as a second public port. One backend worker serializes work. Each visitor gets a separate generated analysis ID.
- Public uploads are rejected by SHA256 before PDF parsing unless they match a supplied synthetic sample. A 200-analysis cap bounds accumulated demo sessions; a fresh temporary instance resets it. This is a small demonstration, not a high-traffic authenticated service.
- `requirements-docker.txt` is a smaller runtime dependency list. It intentionally omits the semantic-model download and test tooling for this sample-only image. Direct library versions match the local project; a Linux Docker build is still required to validate their resolved dependencies on the hosting platform.

## Verification status

GitHub upload ke baad **Actions → Docker demo check** dekho. Workflow actual Linux image build karta hai, frontend health wait karta hai aur container ke andar extraction → comparison → what-if → cited fixture Q&A → report check karta hai. Green result milne tak Docker verified mat samjho. Workflow ko abhi remote par run nahi kiya gaya.

The original local project passed its recorded tests and demo checks. Docker Desktop/CLI was not available in the author's current execution environment, so **a Docker image build and actual cloud deployment have not been verified**. The deployment files are supplied for that next step; they are not a claim that your public website already exists.

Deployment preparation checks: **46 pytest tests passed**, including public-demo restrictions, supervisor behavior with simulated child processes and a headless frontend flow against the in-process FastAPI app. Type checking passed. Compose and Render YAML parsed successfully. These checks do not replace building the actual Linux container.
