from fastapi import FastAPI

app = FastAPI(
    title="AI Investment Impact Radar",
    description="Global events and investment impact analysis API",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}