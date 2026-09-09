"""
Kavach AI — Full Integration Verification
Tests all real backend endpoints, database persistence, ReAct agent loop, and file storage.
"""

import io

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from app.api import chat, files
    from app.core.database import TORTOISE_ORM
    from app.tools import image_analyze, ocr_extract

    test_data = tmp_path_factory.mktemp("integration_data")
    uploads = test_data / "uploads"
    uploads.mkdir()
    TORTOISE_ORM["connections"]["default"]["credentials"]["file_path"] = str(test_data / "test.db")
    files.UPLOAD_DIR = uploads
    chat.UPLOAD_DIR = uploads
    image_analyze.UPLOAD_DIR = uploads
    ocr_extract.UPLOAD_DIR = uploads
    with TestClient(app) as c:
        yield c


def test_health_enriched(client):
    h = client.get("/api/health")
    assert h.status_code == 200
    body = h.json()
    assert body["status"] in ("healthy", "degraded", "unhealthy")
    # New fields per D.4
    assert "uptime_seconds" in body
    assert "disk_usage_gb" in body
    assert "models" in body
    assert isinstance(body["models"], dict)


def test_root_removed(client):
    r = client.get("/")
    assert r.status_code == 404


def test_file_upload_metadata_download_preview(client):
    f = io.BytesIO(b"MRPL refinery pressure vessel inspection report content")
    up = client.post("/api/files/upload", files={"files": ("inspection.txt", f, "text/plain")})
    assert up.status_code == 200
    file_id = up.json()["files"][0]["id"]

    meta = client.get(f"/api/files/{file_id}")
    assert meta.status_code == 200
    assert meta.json()["original_name"] == "inspection.txt"

    dl = client.get(f"/api/files/download/{file_id}")
    assert dl.status_code == 200
    assert b"MRPL refinery" in dl.content

    preview = client.get(f"/api/files/{file_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["preview_kind"] == "text"


def test_agent_execute_streams_full_lifecycle(client):
    res = client.post(
        "/api/agent/execute",
        json={
            "task_description": "Draft an approval note for pipe corrosion inspection",
            "max_steps": 2,
        },
    )
    assert res.status_code == 200
    text = res.text
    for event in ("event: metadata", "event: step", "event: done"):
        assert event in text


def test_agent_tasks_listed(client):
    res = client.get("/api/agent/tasks")
    assert res.status_code == 200
    assert res.json().get("total", 0) > 0


def test_chat_conversations_and_stream(client):
    convs = client.get("/api/chat/conversations")
    assert convs.status_code == 200

    res = client.post(
        "/api/chat",
        json={"message": "What is the standard operating procedure for crude distillation?"},
    )
    assert res.status_code == 200
    assert "event: metadata" in res.text


def test_chat_stop_endpoint(client):
    res = client.post(
        "/api/chat/stop", json={"conversation_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert res.status_code == 404


def test_models_endpoints(client):
    res = client.get("/api/models")
    assert res.status_code == 200
    body = res.json()
    assert "models" in body
    assert isinstance(body["models"], list)


def test_knowledge_endpoints(client):
    res = client.get("/api/knowledge/documents")
    assert res.status_code == 200


def test_network_endpoints(client):
    res = client.get("/api/network/connections")
    assert res.status_code == 200
    res2 = client.get("/api/network/logs")
    assert res2.status_code == 200


def test_knowledge_ingest_e2e(client):
    """Regression F1: /api/knowledge/index parses → chunks → stores Document + chunks."""
    content = (
        "Crude Distillation Unit SOP. Pre-start checklist: verify all pressure gauges, "
        "confirm pump P-101 is offline, drain the boot. Startup sequence: open feed valve "
        "V-201, ignite preheater H-301, monitor overhead temperature for one hour."
    ).encode()
    up = client.post(
        "/api/files/upload", files={"files": ("sop.txt", io.BytesIO(content), "text/plain")}
    )
    assert up.status_code == 200
    file_id = up.json()["files"][0]["id"]

    idx = client.post("/api/knowledge/index", json={"file_id": file_id})
    assert idx.status_code == 200, idx.text
    body = idx.json()
    assert body["chunks_created"] >= 1
    assert body["document_id"]

    docs = client.get("/api/knowledge/documents")
    assert docs.status_code == 200
    ids = [d["id"] for d in docs.json()["documents"]]
    assert body["document_id"] in ids

    search = client.post(
        "/api/knowledge/search",
        json={"query": "Crude Distillation Unit SOP", "search_type": "hybrid"},
    )
    assert search.status_code == 200
    assert search.json()["results"][0]["chunk_id"]


def test_upload_rejects_spoofed_mime(client):
    response = client.post(
        "/api/files/upload",
        files={"files": ("fake.txt", io.BytesIO(b"plain text"), "image/png")},
    )
    assert response.status_code == 400


def test_upload_partial_failure_cleans_files(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.files.UPLOAD_DIR", tmp_path)
    response = client.post(
        "/api/files/upload",
        files=[
            ("files", ("valid.txt", io.BytesIO(b"valid text"), "text/plain")),
            ("files", ("blocked.exe", io.BytesIO(b"MZ"), "application/octet-stream")),
        ],
    )
    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_upload_limit_is_enforced(client, monkeypatch):
    monkeypatch.setattr("app.api.files.MAX_UPLOAD_FILES", 1)
    response = client.post(
        "/api/files/upload",
        files=[
            ("files", ("one.txt", io.BytesIO(b"one"), "text/plain")),
            ("files", ("two.txt", io.BytesIO(b"two"), "text/plain")),
        ],
    )
    assert response.status_code == 400


def test_upload_size_boundary_and_overflow(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.files.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.api.files.MAX_UPLOAD_BYTES", 4)
    at_limit_then_invalid = client.post(
        "/api/files/upload",
        files=[
            ("files", ("four.txt", io.BytesIO(b"1234"), "text/plain")),
            ("files", ("blocked.exe", io.BytesIO(b"MZ"), "application/octet-stream")),
        ],
    )
    assert at_limit_then_invalid.status_code == 400
    assert list(tmp_path.iterdir()) == []

    oversized = client.post(
        "/api/files/upload",
        files={"files": ("five.txt", io.BytesIO(b"12345"), "text/plain")},
    )
    assert oversized.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_knowledge_ingest_failure_creates_no_document(client, monkeypatch):
    upload = client.post(
        "/api/files/upload",
        files={"files": ("rollback.txt", io.BytesIO(b"enough document text"), "text/plain")},
    )
    file_id = upload.json()["files"][0]["id"]
    before = client.get("/api/knowledge/documents").json()["total"]

    async def fail_ingestion(*_):
        raise RuntimeError("forced failure")

    monkeypatch.setattr("app.api.knowledge.ingest_document", fail_ingestion)
    response = client.post("/api/knowledge/index", json={"file_id": file_id})
    after = client.get("/api/knowledge/documents").json()["total"]
    assert response.status_code == 500
    assert after == before


def test_chat_uses_latest_history_and_saved_settings(client, monkeypatch):
    import uuid

    calls = []

    async def fake_stream(**kwargs):
        calls.append(kwargs)
        yield {"message": {"content": "ok"}}

    monkeypatch.setattr("app.api.chat.ollama_client.chat_stream", fake_stream)
    conversation_id = str(uuid.uuid4())
    first = client.post(
        "/api/chat",
        json={
            "conversation_id": conversation_id,
            "message": "old-marker",
            "model_override": "qwen2.5-coder:1.5b",
            "system_prompt": "custom-system",
            "enable_knowledge_base": False,
        },
    )
    assert first.status_code == 200
    for index in range(1, 12):
        response = client.post(
            "/api/chat",
            json={
                "conversation_id": conversation_id,
                "message": f"recent-marker-{index}",
                "enable_knowledge_base": False,
            },
        )
        assert response.status_code == 200

    last = calls[-1]
    history_text = "\n".join(message["content"] for message in last["messages"][1:-1])
    assert last["model"] == "qwen2.5-coder:1.5b"
    assert last["messages"][0]["content"] == "custom-system"
    assert "old-marker" not in history_text
    assert "recent-marker-10" in history_text


def test_chat_history_no_user_duplicate(client):
    """Regression F2: after chat turn, conversation has exactly one user message."""
    import uuid as _uuid

    cid = str(_uuid.uuid4())
    msg = f"F2-dedupe-check {_uuid.uuid4()}"
    res = client.post(
        "/api/chat",
        json={"conversation_id": cid, "message": msg},
    )
    assert res.status_code == 200
    assert "event: metadata" in res.text

    conv = client.get(f"/api/chat/conversations/{cid}")
    assert conv.status_code == 200
    msgs = conv.json()["messages"]
    user_count = sum(1 for m in msgs if m["role"] == "user" and m["content"] == msg)
    assert user_count == 1, f"expected 1 unique user message, got {user_count}: {msgs}"


def test_image_attachment_routes_to_vision(client):
    """Regression F5: image attachment forces qwen2.5vl:3b even on plain text message."""
    # Minimal valid 1x1 PNG bytes
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\rIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\xa5\xf8E\xc0"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    up = client.post(
        "/api/files/upload", files={"files": ("diagram.png", io.BytesIO(png), "image/png")}
    )
    assert up.status_code == 200
    file_id = up.json()["files"][0]["id"]

    res = client.post(
        "/api/chat",
        json={"message": "What does this show?", "file_ids": [file_id]},
    )
    assert res.status_code == 200
    text = res.text
    # Look for the metadata event line; image attachment forces vision model via Rule 1.
    assert "qwen2.5vl:3b" in text, f"expected vision model in metadata, got: {text[:400]}"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
