from pathlib import Path

from fastapi.testclient import TestClient


def _set_env(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "optiforge.db"
    monkeypatch.setenv("OPTIFORGE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OPTIFORGE_PROVIDER", "stub")
    monkeypatch.setenv("OPTIFORGE_PROVIDER_MODEL", "stub-model")
    monkeypatch.setenv("OPTIFORGE_LOG_LEVEL", "INFO")


def test_e2e_stub_provider(monkeypatch, tmp_path: Path) -> None:
    _set_env(monkeypatch, tmp_path)
    from optiforge.core.config import get_settings

    get_settings.cache_clear()
    from optiforge.api import main

    main.get_store.cache_clear()
    client = TestClient(main.app)
    payload = {
        "text": "Minimize cost with x and y given constraints.",
        "tables": [],
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 200
    run_id = response.json()["id"]
    response = client.post(f"/api/runs/{run_id}/generate")
    assert response.status_code == 200
    assert response.json()["status"] == "ir_generated"
    response = client.post(f"/api/runs/{run_id}/solve")
    assert response.status_code == 200
    assert response.json()["status"] in {"solved", "infeasible"}
    response = client.get(f"/api/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run_id
    assert data["ir"] is not None
    assert data["solution"] is not None