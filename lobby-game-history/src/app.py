import uvicorn
from fastapi import FastAPI

from webserver.api.v1.api import api_router


def create_app():
    app = FastAPI()
    app.include_router(api_router, prefix='/api/v1')
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
