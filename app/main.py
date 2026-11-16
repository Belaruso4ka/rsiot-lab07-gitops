import logging
import os
import socket
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Строка, которую меняем в части 4 (путь коммита): после push новая версия
# должна сама доехать до кластера.
GREETING = "readings v1"

STU_ID = os.environ["STU_ID"]
STU_VARIANT = os.environ["STU_VARIANT"]
PORT = int(os.environ["PORT"])
APP_VERSION = os.environ.get("APP_VERSION", "dev")
ALERT_THRESHOLD_C = float(os.environ["ALERT_THRESHOLD_C"])
READY_DELAY_SECONDS = float(os.environ.get("READY_DELAY_SECONDS", "5"))
POD_NAME = socket.gethostname()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("readings")


class SkipHealthChecks(logging.Filter):
    # Пробы Kubernetes приходят каждые несколько секунд и забили бы лог.
    def filter(self, record):
        return "/health/" not in record.getMessage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").addFilter(SkipHealthChecks())
    log.info(
        "start: version=%s pod=%s STU_ID=%s STU_VARIANT=%s port=%s",
        APP_VERSION, POD_NAME, STU_ID, STU_VARIANT, PORT,
    )
    log.info("config: ALERT_THRESHOLD_C=%s READY_DELAY_SECONDS=%s", ALERT_THRESHOLD_C, READY_DELAY_SECONDS)
    app.state.ready_at = time.monotonic() + READY_DELAY_SECONDS
    yield
    log.info("stop: shutdown signal handled, graceful shutdown complete (pod=%s)", POD_NAME)


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def info():
    return {
        "service": "readings",
        "message": GREETING,
        "version": APP_VERSION,
        "pod": POD_NAME,
        "student_id": STU_ID,
        "variant": STU_VARIANT,
    }


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.get("/health/ready")
async def ready():
    seconds_left = app.state.ready_at - time.monotonic()
    if seconds_left > 0:
        return JSONResponse(status_code=503, content={"status": "warming up", "seconds_left": round(seconds_left, 1)})
    return {"status": "ready", "version": APP_VERSION, "pod": POD_NAME}


@app.get("/readings/check")
async def check(sensor_id: str, temperature_c: float):
    status = "alert" if temperature_c > ALERT_THRESHOLD_C else "ok"
    return {
        "sensor_id": sensor_id,
        "temperature_c": temperature_c,
        "threshold_c": ALERT_THRESHOLD_C,
        "status": status,
        "pod": POD_NAME,
        "version": APP_VERSION,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
