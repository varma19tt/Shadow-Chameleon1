from fastapi import FastAPI

app = FastAPI(title="Shadow Chameleon - Backend")

@app.get("/alive")
async def alive():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
