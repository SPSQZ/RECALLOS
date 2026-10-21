# RecallOS — 3D Tactile Mechanical Glass Frontend

This is the production frontend application for **RecallOS**, built for the **Nebius × NVIDIA Hackathon 2026** (Personal AI Track).

---

## 💎 Design Philosophy & 3D Mechanical Innovations

1. **3D Physical Extruded Keycaps (`.btn-3d`)**:
   - Built with physical 6px bottom depth extrusion lips and top specular lighting highlights.
   - Provides **4.0px mechanical travel depression** on actuation (`:active`).
   - **Guaranteed 0.0px screen coordinate displacement**: The button does not drift across the screen when hovering or clicking, preventing user frustration from "chasing" moving buttons.

2. **Web Audio Dual-Tone Click Synthesizer**:
   - Zero audio assets or MP3 dependencies. Synthesized dynamically via the Web Audio API.
   - Generates a **1600Hz high-frequency mechanical switch snap** paired with a **140Hz chassis acoustic bottom-out thud**.
   - Can be toggled on/off via the physical sound button or keyboard hotkey `M`.

3. **Volumetric Glass Slabs (`.card-3d-slab`) & Dynamic Cursor Sheen (`.cursor-sheen`)**:
   - Smooth 24px backdrop blur over custom smoky grey canvas (`#282828`).
   - Dynamic holographic cursor spotlight follows mouse movement across panels.

4. **Deterministic PII Sanitization & Observability**:
   - Client-side deterministic tokenization (`[REDACTED_FINANCIAL_ORG_1]`, `[REDACTED_NAME_1]`, etc.).
   - Interactive 3-column observability inspector showing real-time raw input, egress cloud payload, and in-RAM rehydration lookup tables.
   - Autonomous query complexity model router: Prompts `<0.42` complexity route to NVIDIA Nemotron Nano-4B fast path (<150ms); higher complexity prompts escalate to Nemotron 3 Ultra.

---

## 🚀 Navigation & Hotkeys

| Hotkey | View | Description |
|:---:|:---|:---|
| `1` | **Dashboard** | High-level metrics, active grounding stack, and inference telemetry. |
| `2` | **Agent Chat** | 3-panel chat shell with memory citations and NemoClaw human approval cards. |
| `3` | **Memory Bank** | Semantic vector memory management, search, and conflict superseding. |
| `4` | **Projects & Tasks** | SQLite-synced task milestones and interactive completion toggles. |
| `5` | **Privacy Audit** | 3-column real-time egress sanitization inspector and RAM vault. |
| `6` | **Knowledge Graph** | Interactive HTML5 Canvas force-directed topology of on-device components. |
| `7` | **Benchmarks** | Automated 100-batch egress test suite runner with live telemetry. |
| `8` | **Settings** | Local ChromaDB paths, Nebius endpoints, and emergency RAM flush. |
| `9` | **3D Button Lab** | Physical keycap actuation stress-test lab with live displacement logs. |
| `M` | **Toggle Sound** | Enable / mute Web Audio mechanical click synthesizer. |
| `S` | **Privacy Shield** | Arm / bypass client-side PII tokenization shield. |

---

## 🛠️ Local Development & Running

### Option 1: Direct File Open
Simply double-click `index.html` or open it in any modern browser (Chrome, Edge, Firefox, Brave).

### Option 2: Run via Dev Server (Vite)
```bash
cd RECALLOS/frontend
npm install
npm run dev
```

---

## 📁 Directory Structure

```
RECALLOS/frontend/
├── index.html              # Master SPA HTML shell with all 9 views
├── package.json            # Development dependencies & scripts
├── README.md               # Architecture & design documentation
├── css/
│   ├── tokens.css          # Design tokens (Grey Canvas, Smoky Glass, Accent Palette)
│   ├── 3d_tactile.css      # 3D mechanical button physics, 4px travel, cursor sheen
│   └── style.css           # Global layout, 3-panel chat, data tables, metrics grid
└── js/
    ├── app.js              # Master SPA router & event orchestrator
    ├── sound_engine.js     # Dual-tone Web Audio acoustic synthesizer
    ├── pii_scrubber.js     # Client-side deterministic tokenizer & router
    ├── storage.js          # Simulated on-device SQLite & ChromaDB persistence
    └── knowledge_graph.js  # HTML5 Canvas force-directed graph renderer
```
