from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# ✅ TEST endpoint (çok önemli)
@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ request modeli
class AnalyzeRequest(BaseModel):
    text: str

# ✅ analyze endpoint
@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    text = req.text.lower()

    if "ölü" in text or "saldırı" in text or "bomba" in text:
        return {"risk": 85, "safe": 15}

    return {"risk": 20, "safe": 80}

# ⚠️ EN ALTA OLMALI
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")