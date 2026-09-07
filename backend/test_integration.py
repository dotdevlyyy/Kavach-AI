"""
Kavach AI — Full Integration Verification Script
Tests all real backend endpoints, database persistence, ReAct agent loop, and file storage.
"""

import io
from starlette.testclient import TestClient
from app.main import app

def run_tests():
    print("=" * 60)
    print("KAVACH AI — BACKEND INTEGRATION TEST SUITE")
    print("=" * 60)

    with TestClient(app) as client:
        # 1. Health check
        h = client.get("/api/health")
        assert h.status_code == 200, f"Health check failed: {h.status_code}"
        print("  [PASS] 1. GET /api/health -> 200 OK")
        print("         Health data:", h.json())

        # 2. Root check
        r = client.get("/")
        assert r.status_code == 200, f"Root check failed: {r.status_code}"
        print("  [PASS] 2. GET / -> 200 OK")

        # 3. File upload
        f = io.BytesIO(b"MRPL refinery pressure vessel inspection report content")
        upload_res = client.post("/api/files/upload", files={"files": ("inspection.txt", f, "text/plain")})
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.status_code}"
        data = upload_res.json()
        file_id = data["files"][0]["id"]
        print(f"  [PASS] 3. POST /api/files/upload -> 200 OK (file_id: {file_id})")

        # 4. File metadata
        meta = client.get(f"/api/files/{file_id}")
        assert meta.status_code == 200, f"Metadata failed: {meta.status_code}"
        assert meta.json()["original_name"] == "inspection.txt"
        print(f"  [PASS] 4. GET /api/files/{file_id} -> 200 OK")

        # 5. File download
        dl = client.get(f"/api/files/download/{file_id}")
        assert dl.status_code == 200, f"Download failed: {dl.status_code}"
        assert b"MRPL refinery" in dl.content
        print(f"  [PASS] 5. GET /api/files/download/{file_id} -> 200 OK ({len(dl.content)} bytes)")

        # 6. Agent execution with ReAct loop
        agent_res = client.post(
            "/api/agent/execute",
            json={"task_description": "Draft an approval note for pipe corrosion inspection", "max_steps": 2}
        )
        assert agent_res.status_code == 200, f"Agent execute failed: {agent_res.status_code}"
        text = agent_res.text
        assert "event: metadata" in text
        assert "event: step" in text
        assert "event: tool_result" in text
        assert "event: done" in text
        print("  [PASS] 6. POST /api/agent/execute -> 200 OK (ReAct loop, tool execution & deliverables streamed)")

        # 7. Agent tasks list
        tasks = client.get("/api/agent/tasks")
        assert tasks.status_code == 200, f"Tasks failed: {tasks.status_code}"
        tasks_data = tasks.json()
        total_tasks = tasks_data.get("total", 0)
        assert total_tasks > 0
        print(f"  [PASS] 7. GET /api/agent/tasks -> 200 OK ({total_tasks} tasks recorded in DB)")

        # 8. Chat conversations list
        convs = client.get("/api/chat/conversations")
        assert convs.status_code == 200, f"Conversations failed: {convs.status_code}"
        convs_data = convs.json()
        print(f"  [PASS] 8. GET /api/chat/conversations -> 200 OK ({convs_data.get('total', 0)} conversations)")

        # 9. Chat stream
        chat_res = client.post(
            "/api/chat",
            json={"message": "What is the standard operating procedure for crude distillation?"}
        )
        assert chat_res.status_code == 200, f"Chat failed: {chat_res.status_code}"
        assert "event: metadata" in chat_res.text
        print("  [PASS] 9. POST /api/chat -> 200 OK (Model routing & SSE metadata streamed)")

    print("=" * 60)
    print("ALL 9 BACKEND ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
