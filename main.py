import enum
import time
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter("app_requests_total", "Total number of requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("app_request_latency_seconds", "Request latency", ["endpoint"])


class Job(enum.Enum):
    DIVIDE = 'divide'
    MULTIPLY = 'multiply'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    DO_JOB: Job = Job.DIVIDE


settings = Settings()

app = FastAPI()

JOB_TO_FUNCTION = {
    Job.DIVIDE: lambda x: x.divide(),
    Job.MULTIPLY: lambda x: x.multiply()
}


class DoRequest(BaseModel):
    message: str


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
        response = await call_next(request)
        request_latency = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(request_latency)
        return response


app.add_middleware(MetricsMiddleware)

@app.post("/api/v1/do")
async def do(body: DoRequest):
    func = JOB_TO_FUNCTION[settings.DO_JOB]
    return {"result": func(body.message)}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
