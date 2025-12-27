from fastapi import FastAPI
from .modules.router import router as main_router
import uvicorn
from core.config import settings
from core.lifespan import lifespan

main_app = FastAPI(lifespan=lifespan)

main_app.include_router(main_router)



if __name__ == "__main__":
    uvicorn.run(
        settings.server.app_path,
        port=settings.server.port,
        host=settings.server.host,
    )