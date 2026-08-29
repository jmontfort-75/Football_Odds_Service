from fastapi import FastAPI

app = FastAPI(title="football-odds-service")


@app.get("/")
def root():
    return {"project": "football-odds-service", "description": ""}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
