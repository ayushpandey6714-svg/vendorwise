# Gemini free API: pehle local app chalao

VendorWise mein Gemini support add hai. Code ke automated tests live Google calls nahi hain: tumhari key lagne ke baad real extraction aur Q&A check karna abhi baaki hai. Public deployment bhi alag step hai.

## 1. Key banao

[Google AI Studio API keys](https://aistudio.google.com/apikey) kholo, Google account se login karo aur **Create API key** se project/key banao. Free-tier project use karo; paid billing enable karna is setup ka step nahi hai. Key chat, screenshot ya GitHub par mat bhejo.

Default model `gemini-3.5-flash-lite` hai. [Google pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) par iske input/output ki limited free tier listed hai (checked 23 November 2026). Unlimited requests nahi milti; apne account ki actual quota AI Studio mein check karo. Free-tier content product improvement ke liye use ho sakta hai, isliye pehle supplied synthetic PDFs use karo, confidential quotations nahi.

## 2. Apni project folder mein .env banao

PowerShell mein:

```powershell
cd D:\VendorWise\vendorwise
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

File mein in entries ko set karo (same entry dobara add mat karo). `your-key-here` ki jagah apni key **sirf is local file mein** paste karo, phir save:

```dotenv
VENDORWISE_MODE=live
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.5-flash-lite
VENDORWISE_PUBLIC_DEMO=false
EMBEDDING_BACKEND=tfidf
VENDORWISE_API_URL=http://127.0.0.1:8000
```

File ka naam `.env` hona chahiye, `.env.txt` nahi. TF-IDF pehla run simple rakhta hai: local keyword retrieval, model download nahi. Gemini extraction/answers phir bhi real API se aayenge. Baad mein semantic retrieval ke liye `fastembed` select kar sakte ho.

## 3. Dependencies sirf pehli baar install karo

Isi folder mein:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Python 3.14 par project test hua hai. Agar `python` command nahi milti, Python install/setup pehle chahiye. Agar `.venv` aur dependencies pehle se ready hain, ye step skip karo.

## 4. Dono servers start karo

Pehli PowerShell window, project folder mein:

```powershell
$env:VENDORWISE_MODE = 'live'
$env:LLM_PROVIDER = 'gemini'
$env:VENDORWISE_PUBLIC_DEMO = 'false'
$env:EMBEDDING_BACKEND = 'tfidf'
.\.venv\Scripts\python.exe -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000
```

Doosri PowerShell window:

```powershell
cd D:\VendorWise\vendorwise
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Dono windows khuli rehne do. Browser mein [app](http://127.0.0.1:8501) kholo. Purane servers chal rahe hon to pehle unki windows mein Ctrl+C karo. `.env` badalne ke baad backend restart karna zaroori hai; pehle se set shell variables `.env` se upar priority rakhte hain.

## 5. Pehla real AI check

- Nayi analysis banao; **Use the three synthetic demo PDFs** select karo aur **Create analysis and extract** dabao.
- App mode **live** hona chahiye. Sample PDFs bhi live mode mein Gemini se extract honge.
- Extraction evidence/amounts inspect karo. Budget 1200000, warranty 36 months, delivery 10 days par correctly extracted sample inputs se Vendor C qualify karta hai.
- Question pucho: `Does Vendor B cover the battery?` Source citation inspect karo.
- Free quota exhaust hone par 429 error aayega. Dashboard ka reset time dekho; baar-baar extract button dabane se quota jaldi khatam ho sakti hai. Ek analysis multiple API requests use karti hai.
- Missing key, unsupported model, invalid JSON or quotation evidence mismatch par app error dikhayega; live mode silently fixture answer nahi dega.

## Public link baad mein

Ye localhost URL sirf tumhare computer par hai. API key set karne se public website nahi banti. Supplied Docker/Render config abhi **sample-only fixture demo** deploy karti hai. Public live AI ke liye access control aur shared quota protection chahiye; public demo guard ko sirf key lagane ke liye disable mat karo. [Deployment guide](DEPLOY_HINGLISH.md) dekho.

Provider implementation follows [Google's official OpenAI compatibility documentation](https://ai.google.dev/gemini-api/docs/openai). Existing OpenAI SDK Google ke endpoint ko call karta hai; Gemini use karne par OpenAI key/billing nahi chahiye.
