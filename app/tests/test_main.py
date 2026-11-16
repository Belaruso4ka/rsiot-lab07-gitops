import os
import sys
from pathlib import Path

# main.py читает настройки из окружения при импорте, поэтому задаём их до import.
os.environ.update({
    "STU_ID": "230233",
    "STU_VARIANT": "44",
    "PORT": "8124",
    "ALERT_THRESHOLD_C": "30",
    "READY_DELAY_SECONDS": "0",
})
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


def test_info_has_metadata():
    with TestClient(main.app) as client:
        body = client.get("/").json()
    assert body["service"] == "readings"
    assert body["student_id"] == "230233"
    assert body["variant"] == "44"
    assert body["message"]


def test_health_live():
    with TestClient(main.app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_ready_after_warmup():
    with TestClient(main.app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_check_above_threshold_is_alert():
    with TestClient(main.app) as client:
        body = client.get("/readings/check", params={"sensor_id": "t-1", "temperature_c": 31.5}).json()
    assert body["status"] == "alert"
    assert body["threshold_c"] == 30.0


def test_check_at_threshold_is_ok():
    with TestClient(main.app) as client:
        body = client.get("/readings/check", params={"sensor_id": "t-1", "temperature_c": 30}).json()
    assert body["status"] == "ok"


def test_check_rejects_non_numeric_temperature():
    with TestClient(main.app) as client:
        response = client.get("/readings/check", params={"sensor_id": "t-1", "temperature_c": "hot"})
    assert response.status_code == 422
