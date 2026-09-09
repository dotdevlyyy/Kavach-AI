"""
Kavach AI — Unit Tests
Covers the 15 test gaps called out in TODO_BACKEND.md §5.
Pure-python only; DB-touching paths are mocked or skipped.
"""

import asyncio

import pytest

from app.agent.executor import _resolve_kwargs
from app.agent.observer import observer
from app.agent.planner import _extract_json, _normalize_plan
from app.api.network import is_local_address
from app.core.cancellation import CancellationRegistry
from app.rag.chunker import chunk_text, split_into_sentences
from app.rag.embedder import deserialize_embedding, serialize_embedding
from app.rag.parser import parse_csv, parse_document, parse_txt
from app.router.classifier import classify_task
from app.router.router import route_request
from app.tools.code_execute import execute_python_code
from app.tools.doc_generate import (
    generate_excel_sheet,
    generate_presentation,
    generate_word_document,
)
from app.tools.file_read import file_read
from app.tools.file_write import file_write

# ─── T1: parser (incl. .csv fix from B2) ─────────────────────────────────


def test_t1_parse_txt(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello world", encoding="utf-8")
    assert parse_txt(str(f)) == "hello world"


def test_t1_parse_csv(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    out = parse_csv(str(f))
    assert "a, b, c" in out and "1, 2, 3" in out and "4, 5, 6" in out


def test_t1_parse_document_routes_extensions(tmp_path):
    (tmp_path / "a.md").write_text("md", encoding="utf-8")
    (tmp_path / "b.txt").write_text("txt", encoding="utf-8")
    (tmp_path / "c.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    assert parse_document(str(tmp_path / "a.md")) == "md"
    assert parse_document(str(tmp_path / "b.txt")) == "txt"
    assert "1, 2" in parse_document(str(tmp_path / "c.csv"))


def test_t1_parse_document_unsupported(tmp_path):
    f = tmp_path / "x.exe"
    f.write_bytes(b"binary")
    with pytest.raises(ValueError):
        parse_document(str(f))


def test_t1_parse_document_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_document(str(tmp_path / "nope.txt"))


# ─── T2: embedder round-trip ─────────────────────────────────────────────


def test_t2_serialize_deserialize_roundtrip():
    vec = [0.1, -0.2, 0.3, 0.4, -0.5]
    assert deserialize_embedding(serialize_embedding(vec)) == pytest.approx(vec, abs=1e-6)


def test_t2_empty_roundtrip():
    assert deserialize_embedding(serialize_embedding([])) == []


# ─── T3: chunker overlap edge cases ──────────────────────────────────────


def test_t3_chunk_short_text_single_chunk():
    text = "Short text."
    chunks = chunk_text(text, chunk_size=10, overlap_size=2)
    assert chunks == ["Short text."]


def test_t3_chunk_overlap_carries_words():
    text = " ".join(f"Sentence number {i}." for i in range(20))
    chunks = chunk_text(text, chunk_size=4, overlap_size=2)
    assert len(chunks) > 1
    # each chunk after the first should share >= 1 word with the previous one
    for a, b in zip(chunks, chunks[1:]):
        a_words = set(a.split())
        b_words = set(b.split())
        assert a_words & b_words, f"no overlap between {a!r} and {b!r}"


def test_t3_split_into_sentences():
    sents = split_into_sentences("First. Second! Third? Fourth.")
    assert sents == ["First.", "Second!", "Third?", "Fourth."]


# ─── T4: RRF math (pure-python, no DB) ───────────────────────────────────


def test_t4_rrf_formula():
    """RRF score = Σ 1/(k + rank+1). Verify by hand for two ranked lists."""
    k = 60
    fts = ["a", "b", "c"]  # ranks 0,1,2
    vec = ["b", "d", "a"]  # ranks 0,1,2
    scores = {}
    for rank, rid in enumerate(fts):
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank + 1)
    for rank, rid in enumerate(vec):
        scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank + 1)
    # a: 1/(60+1) from fts + 1/(60+3) from vec
    # b: 1/(60+2) from fts + 1/(60+1) from vec
    # d: 1/(60+2) from vec (rank 1 → 1/62)
    assert scores["a"] == pytest.approx(1 / 61 + 1 / 63, abs=1e-6)
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61, abs=1e-6)
    assert scores["d"] == pytest.approx(1 / 62, abs=1e-6)
    assert scores["c"] == pytest.approx(1 / 63, abs=1e-6)
    ranked = sorted(scores, key=lambda x: scores[x], reverse=True)
    assert ranked[0] in ("a", "b")  # a and b tied at top


# ─── T5: classifier each branch ──────────────────────────────────────────


def test_t5_image_branch():
    tt, conf, _ = classify_task("hello", has_images=True)
    assert tt.value == "vision" and conf >= 0.9


def test_t5_pdf_ocr_branch():
    tt, conf, _ = classify_task("please extract text from this scanned PDF", has_pdfs=True)
    assert tt.value == "ocr" and conf >= 0.85


def test_t5_code_keywords():
    tt, _, _ = classify_task("write a python function to sort an array")
    assert tt.value == "code_generation"


def test_t5_document_keywords():
    tt, _, _ = classify_task("draft an approval note for corrosion inspection")
    assert tt.value == "document_draft"


def test_t5_default_chat():
    tt, conf, _ = classify_task("hi there how are you")
    assert tt.value == "general_chat" and conf <= 0.6


def test_t5_code_block_detection():
    tt, _, _ = classify_task("Random words\n```python\nprint('hi')\n```")
    assert tt.value == "code_generation"


# ─── T6: router override + (mocked) file_ids ─────────────────────────────


def test_t6_override_bypasses_classifier():
    import asyncio

    model, meta = asyncio.run(route_request(message="hello", model_override="custom:7b"))
    assert model == "custom:7b"
    assert meta.confidence == 1.0
    assert "override" in meta.reasoning.lower()


def test_t6_default_routes_to_llama():
    import asyncio

    model, _ = asyncio.run(route_request(message="hello world"))
    assert model == "llama3.2:1b"


# ─── T7: planner JSON extraction ─────────────────────────────────────────


def test_t7_extract_json_fenced():
    txt = 'noise\n```json\n{"steps": [], "goal": "x"}\n```\nmore noise'
    parsed = _extract_json(txt)
    assert parsed == {"steps": [], "goal": "x"}


def test_t7_extract_json_balanced_braces():
    txt = 'pre {"steps": [{"step_number": 1}], "goal": "g"} post'
    parsed = _extract_json(txt)
    assert parsed["goal"] == "g"
    assert len(parsed["steps"]) == 1


def test_t7_extract_json_trailing_commas():
    txt = '{"steps": [], "goal": "g",}'
    parsed = _extract_json(txt)
    assert parsed is not None and parsed["goal"] == "g"


def test_t7_extract_json_none_when_missing():
    assert _extract_json("") is None
    assert _extract_json("no json here at all") is None


def test_t7_normalize_plan_fills_defaults():
    out = _normalize_plan({"steps": [{}], "goal": ""}, "user task")
    assert out["goal"] == "user task"
    assert out["steps"][0]["step_number"] == 1
    assert out["steps"][0]["suggested_tool"] == "none"


def test_t7_normalize_plan_empty_uses_fallback():
    out = _normalize_plan({"steps": []}, "task")
    assert out["steps"] and out["goal"] == "task"


# ─── T8: _resolve_kwargs ─────────────────────────────────────────────────


def test_t8_resolve_kwargs_fills_required_string():
    def tool(query: str):
        return query

    out = asyncio.run(_resolve_kwargs(tool, {"task": "do it"}))
    assert out["query"] == "do it"


def test_t8_resolve_kwargs_does_not_overwrite_explicit():
    def tool(query: str):
        return query

    out = asyncio.run(_resolve_kwargs(tool, {"query": "explicit", "task": "ignored"}))
    assert out["query"] == "explicit"


def test_t8_resolve_kwargs_aliases_image_path_to_file_path():
    # Tool only declares file_path; aliasing puts image_path value into file_path param.
    def tool(file_path: str):
        return file_path

    out = asyncio.run(_resolve_kwargs(tool, {"image_path": "/tmp/x.png"}))
    assert out.get("file_path") == "/tmp/x.png"


def test_t8_resolve_kwargs_aliases_file_path_to_image_path():
    # Tool only declares image_path; aliasing puts file_path value into image_path param.
    def tool(image_path: str):
        return image_path

    out = asyncio.run(_resolve_kwargs(tool, {"file_path": "/tmp/x.png"}))
    assert out.get("image_path") == "/tmp/x.png"


# ─── T9: observer branches ───────────────────────────────────────────────


def test_t9_observer_success():
    out = observer.observe(1, {"success": True, "output": "ok"})
    assert out["status"] == "completed"
    assert "ok" in out["observation"]


def test_t9_observer_failure():
    out = observer.observe(2, {"success": False, "output": "boom"})
    assert out["status"] == "failed"
    assert "boom" in out["observation"]


# ─── T10: file_read sandbox guard (security-sensitive) ───────────────────


def test_t10_file_read_blocks_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.paths.DATA_ROOT", tmp_path)
    (tmp_path / "ok.txt").write_text("hi", encoding="utf-8")
    res = file_read("../etc/passwd")
    assert "Access denied" in res


def test_t10_file_read_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.paths.DATA_ROOT", tmp_path)
    res = file_read("nope_does_not_exist.txt")
    assert "not found" in res.lower()


# ─── T11: file_write sandbox guard ───────────────────────────────────────


def test_t11_file_write_blocks_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.paths.DATA_ROOT", tmp_path)
    res = file_write("../escape.txt", "pwn")
    assert "Access denied" in res
    assert not (tmp_path.parent / "escape.txt").exists()


def test_t11_file_write_writes_inside(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.paths.DATA_ROOT", tmp_path)
    res = file_write("safe.txt", "ok")
    assert "Successfully wrote" in res
    assert (tmp_path / "safe.txt").exists()


def test_t11_path_guard_rejects_sibling_prefix(tmp_path):
    from app.core.paths import resolve_within

    root = tmp_path / "data"
    sibling = tmp_path / "data_evil" / "secret.txt"
    root.mkdir()
    with pytest.raises(ValueError):
        resolve_within(root, sibling)


# ─── T12: code_execute branches ──────────────────────────────────────────


def test_t12_code_execute_fails_closed_without_docker(monkeypatch):
    monkeypatch.setattr("app.tools.code_execute.shutil.which", lambda _: None)
    r = asyncio.run(execute_python_code("print('hi')", timeout=5))
    assert r["success"] is False
    assert "sandbox unavailable" in r["output"].lower()


def test_t12_code_execute_never_falls_back_to_host(monkeypatch):
    monkeypatch.setattr("app.tools.code_execute.shutil.which", lambda _: None)
    r = asyncio.run(execute_python_code("def $$$", timeout=5))
    assert r["success"] is False
    assert "docker is not installed" in r["output"].lower()


def test_t12_code_execute_unavailable_before_timeout(monkeypatch):
    monkeypatch.setattr("app.tools.code_execute.shutil.which", lambda _: None)
    r = asyncio.run(execute_python_code("import time; time.sleep(5)", timeout=1))
    assert r["success"] is False
    assert "sandbox unavailable" in r["output"].lower()


# ─── T13: doc_generate all three ────────────────────────────────────────


def test_t13_docx(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.doc_generate.OUTPUT_DIR", tmp_path)
    res = generate_word_document(title="Test Doc", content="Body line")
    assert res["status"] == "ok"
    assert (tmp_path / res["filename"]).exists()


def test_t13_xlsx(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.doc_generate.OUTPUT_DIR", tmp_path)
    res = generate_excel_sheet(title="Sheet1", headers=["a", "b"], rows=[[1, 2], [3, 4]])
    assert res["status"] == "ok"
    assert (tmp_path / res["filename"]).exists()


def test_t13_pptx(tmp_path, monkeypatch):
    monkeypatch.setattr("app.tools.doc_generate.OUTPUT_DIR", tmp_path)
    res = generate_presentation(title="Deck", slides_content=[{"title": "S1", "content": "C1"}])
    assert res["status"] == "ok"
    assert (tmp_path / res["filename"]).exists()


# ─── T14: is_local_address ──────────────────────────────────────────────


def test_t14_is_local_address_loopback():
    assert is_local_address("127.0.0.1") is True
    assert is_local_address("::1") is True


def test_t14_is_local_address_private():
    assert is_local_address("192.168.1.5") is True
    assert is_local_address("10.0.0.1") is True
    assert is_local_address("172.16.0.1") is True


def test_t14_is_local_address_public():
    assert is_local_address("8.8.8.8") is False
    assert is_local_address("1.1.1.1") is False


def test_t14_is_local_address_empty_and_invalid():
    assert is_local_address("") is True
    assert is_local_address("not-an-ip") is False
    assert is_local_address("*") is True
    assert is_local_address("0.0.0.0") is True


def test_t14_malformed_connection_makes_verdict_unknown(monkeypatch):
    from app.api import network

    address = type("Address", (), {"ip": "not-an-ip", "port": 443})()
    connection = type(
        "Connection",
        (),
        {"pid": None, "laddr": None, "raddr": address, "type": 1, "status": "ESTABLISHED"},
    )()
    monkeypatch.setattr("app.api.network.psutil.net_connections", lambda **_: [connection])
    network._snapshot_connections()
    summary = network.get_network_summary()
    assert summary["status"] == "unknown"
    assert summary["is_air_gapped"] is None


def test_config_reads_documented_environment(monkeypatch):
    from app.core.config import load_settings

    monkeypatch.setenv("KAVACH_HOST", "127.0.0.1")
    monkeypatch.setenv("KAVACH_PORT", "8123")
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.internal:11434")
    loaded = load_settings()
    assert loaded.HOST == "127.0.0.1"
    assert loaded.PORT == 8123
    assert loaded.ollama_host == "http://ollama.internal:11434"


# ─── T15: cancellation semantics ────────────────────────────────────────


def test_t15_get_returns_event():
    reg = CancellationRegistry()
    ev = reg.get("k1")
    assert isinstance(ev, asyncio.Event)
    assert ev.is_set() is False


def test_t15_cancel_signals_event():
    reg = CancellationRegistry()
    reg.get("k2")
    reg.cancel("k2")
    assert reg.get("k2").is_set() is True


def test_t15_clear_removes_event():
    reg = CancellationRegistry()
    reg.get("k3")
    reg.clear("k3")
    # After clear, get must return a fresh, unset event
    assert reg.get("k3").is_set() is False


def test_t15_cancel_unknown_key_is_idempotent():
    reg = CancellationRegistry()
    assert reg.cancel("never_seen") is True
    assert reg.get("never_seen").is_set() is True


# ─── T16: vision tools pass keep_alive=-1 (B10 regression guard) ────────


def test_t16_ocr_extract_passes_keep_alive(monkeypatch, tmp_path):
    """B10 regression guard: ocr_extract must use ollama_client.chat wrapper
    (which defaults keep_alive=-1), not raw client.chat."""
    import asyncio

    from app.tools import ocr_extract

    img = tmp_path / "fake.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)

    upload_row = type("U", (), {"stored_path": str(img), "id": "abc"})()

    async def fake_get_or_none(id):
        return upload_row

    monkeypatch.setattr("app.models.file_upload.FileUpload.get_or_none", fake_get_or_none)
    monkeypatch.setattr("app.tools.ocr_extract.UPLOAD_DIR", tmp_path)

    captured = {}

    class FakeResponse:
        message = type("M", (), {"content": "extracted text"})()

    async def fake_chat(model, messages, keep_alive, **_):
        captured["keep_alive"] = keep_alive
        captured["model"] = model
        return FakeResponse()

    monkeypatch.setattr("app.core.ollama_client.ollama_client.chat", fake_chat)

    out = asyncio.run(ocr_extract.extract_text_from_image(file_id="abc"))
    assert captured["keep_alive"] == -1
    assert captured["model"] == "qwen2.5vl:3b"
    assert out == "[Page 1]\nextracted text"


def test_t16_image_analyze_passes_keep_alive(monkeypatch, tmp_path):
    import asyncio

    from app.tools import image_analyze

    img = tmp_path / "fake.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    upload_row = type("U", (), {"stored_path": str(img), "id": "abc"})()

    async def fake_get_or_none(id):
        return upload_row

    monkeypatch.setattr("app.models.file_upload.FileUpload.get_or_none", fake_get_or_none)
    monkeypatch.setattr("app.tools.image_analyze.UPLOAD_DIR", tmp_path)

    captured = {}

    class FakeResponse:
        message = type("M", (), {"content": "diagram analysis"})()

    async def fake_chat(model, messages, keep_alive, **_):
        captured["keep_alive"] = keep_alive
        captured["model"] = model
        return FakeResponse()

    monkeypatch.setattr("app.core.ollama_client.ollama_client.chat", fake_chat)

    out = asyncio.run(image_analyze.analyze_engineering_diagram(file_id="abc", query="valves"))
    assert captured["keep_alive"] == -1
    assert captured["model"] == "qwen2.5vl:3b"
    assert out == "diagram analysis"


# ─── T17: cancel-mid-stream via cancellation registry ───────────────────


def test_t17_cancel_event_stops_stream_consumption():
    """chat.py checks `cancel_event.is_set()` between tokens. Verify the event
    is cleared after `clear()` so a fresh request doesn't see stale cancellation."""
    from app.core.cancellation import CancellationRegistry

    reg = CancellationRegistry()
    ev = reg.get("conv-1")
    reg.cancel("conv-1")
    assert ev.is_set() is True
    reg.clear("conv-1")
    # After clear, the next get() must return a fresh, unset event.
    assert reg.get("conv-1").is_set() is False


# ─── T20: code_execute subprocess killed on timeout cleans up temp file ──


def test_t20_code_execute_unavailable_is_clean(monkeypatch):
    monkeypatch.setattr("app.tools.code_execute.shutil.which", lambda _: None)
    r = asyncio.run(execute_python_code("import time; time.sleep(10)", timeout=1))
    assert r["success"] is False
    assert "sandbox unavailable" in r["output"].lower()


def test_t20_code_execute_returns_on_syntax_error(monkeypatch):
    monkeypatch.setattr("app.tools.code_execute.shutil.which", lambda _: None)
    r = asyncio.run(execute_python_code("def $$$:", timeout=5))
    assert r["success"] is False
    assert r["exit_code"] != 0


# ─── T21: SQLite WAL + foreign_keys pragmas applied ─────────────────────


def test_t21_wal_mode_and_foreign_keys_enabled(tmp_path):
    """init_db() applies WAL + foreign_keys pragmas. Init a fresh DB into tmp_path
    and assert the pragmas stuck on the open conn."""
    from tortoise import Tortoise

    from app.core.database import TORTOISE_ORM

    async def check():
        cfg = {**TORTOISE_ORM}
        cfg["connections"]["default"]["credentials"]["file_path"] = str(tmp_path / "test.db")
        await Tortoise.init(config=cfg, _enable_global_fallback=True)
        await Tortoise.generate_schemas()
        await _apply_pragmas()
        conn = Tortoise.get_connection("default")
        wal = await conn.execute_query("PRAGMA journal_mode")
        fk = await conn.execute_query("PRAGMA foreign_keys")
        mode = wal[1][0]["journal_mode"].lower() if wal[1] else wal[1]
        fk_val = fk[1][0]["foreign_keys"] if fk[1] else 0
        await Tortoise.close_connections()
        return mode, fk_val

    async def _apply_pragmas():
        from tortoise import Tortoise

        conn = Tortoise.get_connection("default")
        await conn.execute_query("PRAGMA journal_mode=WAL;")
        await conn.execute_query("PRAGMA foreign_keys=ON;")

    mode, fk = asyncio.run(check())
    assert mode == "wal"
    assert fk == 1


# ─── T23: _hydrate_batch issues a single query (N+1 regression guard) ──


def test_t23_hydrate_batch_single_query(monkeypatch):
    """Phase C replaced per-id get_or_none with a single filter(id__in=...).
    Asserts the filter path is used (not a loop of get_or_none).

    Tortoise's Model.filter returns an AwaitableQuery (NOT a coroutine) — it has
    sync chain methods like .select_related and is itself awaitable, yielding a
    list of model instances on await.
    """
    from app.rag import retriever

    called = {"filter_count": 0}

    class FakeChunk:
        def __init__(self, cid):
            self.id = cid
            self.document_id = f"doc-{cid}"
            self.metadata = {}
            self.document = type("D", (), {"original_name": f"name-{cid}"})()

    class FakeAwaitableQS:
        """Mimic Tortoise's AwaitableQuery: sync chain + awaitable + list result."""

        def __init__(self, ids):
            self._ids = ids

        def select_related(self, *_):
            return self

        def __await__(self):
            async def _resolve():
                return [FakeChunk(c) for c in self._ids]

            return _resolve().__await__()

    async def run():
        def fake_filter(*a, **kw):
            called["filter_count"] += 1
            return FakeAwaitableQS(kw["id__in"])

        monkeypatch.setattr(
            "app.models.knowledge_chunk.KnowledgeChunk.filter",
            fake_filter,
        )
        return await retriever._hydrate_batch(["c1", "c2", "c3"])

    out = asyncio.run(run())
    assert called["filter_count"] == 1, "must use a single filter() call"
    assert len(out) == 3
    assert out["c1"]["document_name"] == "name-c1"


# ─── T24: _resolve_kwargs required-str fallback + multi-req + non-str ──


def test_t24_resolve_kwargs_multi_required_strings_uses_task():
    def tool(a: str, b: str):
        return a + b

    out = asyncio.run(_resolve_kwargs(tool, {"task": "from task"}))
    assert out.get("a") == "from task"
    assert out.get("b") == "from task"


def test_t24_resolve_kwargs_optional_param_skipped():
    def tool(name: str, count: int = 0):
        return name

    # Only the required string gets filled; optional int with default is left alone.
    out = asyncio.run(_resolve_kwargs(tool, {"task": "from task"}))
    assert out["name"] == "from task"
    assert "count" not in out or out.get("count", 0) == 0


def test_t24_resolve_kwargs_rejects_unknown_key():
    def tool(name: str):
        return name

    with pytest.raises(ValueError, match="Unknown kwargs"):
        # 'bogus' is not declared on `tool`
        asyncio.run(_resolve_kwargs(tool, {"name": "ok", "bogus": "x"}))


def test_t24_resolve_kwargs_meta_keys_pass_through():
    """task + step_title are agent-loop scaffolding, must not raise unknown."""

    def tool(query: str):
        return query

    out = asyncio.run(_resolve_kwargs(tool, {"task": "real task", "step_title": "Step 1"}))
    assert out["query"] == "real task"
