# 13 — Competitor Analysis

## Direct Competitors (Local/Self-Hosted AI)

### 1. Open WebUI

| Attribute | Detail |
|---|---|
| **What it is** | Web-based chat UI for Ollama / OpenAI-compatible backends |
| **GitHub Stars** | 75k+ |
| **License** | MIT |
| **Air-gapped** | ✓ (when used with Ollama) |
| **Multi-model** | Partial — user manually switches models from dropdown |
| **Auto-selection** | ✗ No task-based routing |
| **Agentic** | ✗ No tool use, no planning, no multi-step |
| **Multimodal** | ~ Basic image input if model supports it |
| **Document output** | ✗ Chat text only |
| **Knowledge base** | ~ Basic document upload, no hybrid search |
| **Code sandbox** | ✗ |

**Why Kavach wins:** Open WebUI is a chat wrapper. Kavach is a workbench. Auto-selection, agentic execution, document generation, and code sandbox are entirely missing.

---

### 2. AnythingLLM

| Attribute | Detail |
|---|---|
| **What it is** | All-in-one desktop AI app with RAG |
| **GitHub Stars** | 35k+ |
| **License** | MIT |
| **Air-gapped** | ✓ |
| **Multi-model** | ✓ Supports multiple providers, but one model at a time |
| **Auto-selection** | ✗ Manual model selection |
| **Agentic** | ~ Has "agents" but limited tool set, no planning loop |
| **Multimodal** | ~ Basic OCR via external tools |
| **Document output** | ✗ Chat text only |
| **Knowledge base** | ✓ Good RAG with multiple vector DBs |
| **Code sandbox** | ✗ |

**Why Kavach wins:** AnythingLLM has decent RAG but no true agentic loop, no auto-selection, no document generation. Kavach's agent can plan, use tools, iterate, and produce real deliverables.

---

### 3. LM Studio

| Attribute | Detail |
|---|---|
| **What it is** | Desktop app for running local LLMs |
| **License** | Proprietary (free for personal use) |
| **Air-gapped** | ✓ |
| **Multi-model** | ~ One model loaded at a time |
| **Auto-selection** | ✗ |
| **Agentic** | ✗ |
| **Multimodal** | ~ Limited to model capabilities |
| **Document output** | ✗ |
| **Knowledge base** | ✗ |
| **Code sandbox** | ✗ |

**Why Kavach wins:** LM Studio is a model runner, not a workbench. No agent, no tools, no outputs, no KB.

---

### 4. Jan.ai

| Attribute | Detail |
|---|---|
| **What it is** | Open-source ChatGPT alternative that runs offline |
| **GitHub Stars** | 25k+ |
| **License** | AGPLv3 |
| **Air-gapped** | ✓ |
| **Multi-model** | ✓ Supports multiple models |
| **Auto-selection** | ✗ |
| **Agentic** | ✗ |
| **Multimodal** | ~ Basic |
| **Document output** | ✗ |
| **Knowledge base** | ~ Basic RAG |

**Why Kavach wins:** Jan is a personal chat app. Not designed for industrial workloads. No agent, no document generation, no sovereignty proof.

---

### 5. PrivateGPT

| Attribute | Detail |
|---|---|
| **What it is** | Interact with documents using LLMs, 100% private |
| **GitHub Stars** | 55k+ |
| **License** | Apache 2.0 |
| **Air-gapped** | ✓ |
| **Multi-model** | ~ Primarily one model |
| **Auto-selection** | ✗ |
| **Agentic** | ✗ |
| **Multimodal** | ✗ |
| **Document output** | ✗ |
| **Knowledge base** | ✓ Good document ingestion |

**Why Kavach wins:** PrivateGPT does document Q&A well but nothing else. No code, no vision, no agent, no document generation.

---

### 6. LibreChat

| Attribute | Detail |
|---|---|
| **What it is** | Open-source multi-provider chat UI |
| **GitHub Stars** | 20k+ |
| **License** | MIT |
| **Air-gapped** | ✓ (with local providers) |
| **Multi-model** | ✓ Multiple providers |
| **Auto-selection** | ✗ |
| **Agentic** | ~ Plugin system, limited tools |
| **Multimodal** | ~ Via provider support |
| **Document output** | ✗ |
| **Knowledge base** | ✗ |

**Why Kavach wins:** LibreChat is a chat aggregator. Good UI but no industrial workbench features.

---

## Cloud Competitors (For Context)

| Platform | Key Limitation |
|---|---|
| **ChatGPT / GPT-4** | Cloud-based. Data leaves premises. Enterprise plan still routes through OpenAI servers. |
| **Claude (Anthropic)** | Cloud-based. No self-hosted option available. |
| **GitHub Copilot** | Cloud-based. Source code sent to Microsoft. Banned in most PSUs. |
| **Azure OpenAI** | Cloud-based (Microsoft datacenter). Even private endpoint is not on-premise. Requires internet. |
| **Google Vertex AI** | Cloud-based (GCP). Not on-premise. |
| **AWS Bedrock** | Cloud-based (AWS). Not on-premise. |

**Common limitation:** All cloud solutions fundamentally cannot guarantee that data stays on the organization's premises.

---

## Comprehensive Feature Matrix

| Feature | Kavach AI | Open WebUI | AnythingLLM | LM Studio | Jan.ai | PrivateGPT | LibreChat |
|---|---|---|---|---|---|---|---|
| **Air-gapped** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Multi-model preloaded** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Auto-selection** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Agentic (ReAct)** | ✓ | ✗ | ~ | ✗ | ✗ | ✗ | ~ |
| **Multi-step planning** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Tool calling** | ✓ | ✗ | ~ | ✗ | ✗ | ✗ | ~ |
| **Code sandbox** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Vision/OCR** | ✓ | ~ | ~ | ~ | ~ | ✗ | ~ |
| **DOCX generation** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **XLSX generation** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **PPTX generation** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Local KB (RAG)** | ✓ | ~ | ✓ | ✗ | ~ | ✓ | ✗ |
| **Hybrid search** | ✓ | ✗ | ~ | ✗ | ✗ | ~ | ✗ |
| **Network monitor** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Sovereignty proof** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## Key Differentiators Summary

1. **Model Auto-Selection** — No other self-hosted solution does this. Users don't need to know which model to use.
2. **True Agentic Execution** — Planning, tool use, iteration. Not just chat.
3. **Document Output** — Real DOCX/XLSX/PPTX files. No other local tool does this.
4. **Code Sandbox** — Safe code execution without exposing internals.
5. **Sovereignty Proof** — Built-in network monitor. Not just "it's local" — we prove it live.
6. **All models preloaded** — Instant switching. No cold-start delay.
7. **Industrial focus** — Designed for refineries, PSUs, manufacturing — not just developers.
