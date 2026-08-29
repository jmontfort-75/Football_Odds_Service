from fastapi import FastAPI

from app.api.v1.routes import router as v1_router

app = FastAPI(title="football-odds-service")
app.include_router(v1_router)


@app.get("/")
def root():
    return {"project": "football-odds-service", "description": ""}


@app.get("/health")
def health():
    return {"status": "ok", "service": "football-odds-service"}
