from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.api.v2_routes import router as v2_router

app = FastAPI(
    title="SupplyChainOptii API",
    description="Real-time optimization service and validation gateway.",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(v2_router)

@app.get("/health")
def health_check():
    import sys
    return {
        "status": "ok",
        "solver": "SupplyChainOptii",
        "version": "0.1.0",
        "python": sys.version.split(' ')[0]
    }

@app.get("/version")
def version():
    return {"version": "0.1.0"}
