from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers.datasets import router as datasets_router

app = FastAPI(
    title="图片数据集管理系统",
    description="管理图片数据集的增删改查 API",
    version="0.1.0",
)

app.include_router(datasets_router)

data_path = Path(settings.data.path)
data_path.mkdir(parents=True, exist_ok=True)
if data_path.exists():
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
