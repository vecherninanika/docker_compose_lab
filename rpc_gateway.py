import httpx
import logging

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rpc_gateway")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    MULTIPLY_URL: str = 'http://multiply:8000/api/v1/do'
    DIVIDE_URL: str = 'http://divide:8000/api/v1/do'


settings = Settings()


METHOD_TO_SERVER = {
    'message.multiply': settings.MULTIPLY_URL,
    'message.divide': settings.DIVIDE_URL,
}


@app.post("/rpc")
async def handle_rpc(request: Request):
    logger.info("Received RPC request")
    rpc_request = await request.json()
    method = rpc_request.get("method")
    data = rpc_request.get("data")

    url = METHOD_TO_SERVER.get(method)
    if not url:
        raise HTTPException(detail={"error": "Unknown method"}, status_code=status.HTTP_404_NOT_FOUND)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
    return JSONResponse(content=response.json(), status_code=response.status_code)
