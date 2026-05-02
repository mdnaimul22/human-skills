---
trigger: always_on
name: project-tree-example
description: follow similar kind of Project Structure or more schema base Architectural Pattern that track code structure without viewing the full context of code.
---

### Canonical Project Structure Example-1

```
project_root/
│
├── src/
│   │
│   ├── config/                       # ⚙️ LAYER 1 — Single Source of Truth (Like a Gear Box)
│   │   ├── __init__.py               # auto-loads dotenv, exports everything
│   │   ├── paths.py                  # PROJECT_ROOT auto-detection
│   │   ├── files.py                  # read/write/json/delete utilities
│   │   ├── dotenv.py                 # load/set/get/remove .env values
│   │   └── settings.py               # BaseProjectSettings — API keys, timeouts, limits
│   │
│   ├── schema/                       # 📐 LAYER 1 — Data Contracts (পরম সত্য)
│   │   ├── __init__.py
│   │   ├── profile.py                # LinkedInProfile, ConnectionRequest
│   │   ├── message.py                # Message, MessageThread
│   │   └── job.py                    # JobPost, Application
│   │
│   ├── api/                          # 🚪 LAYER 1 — HTTP Interface
│   │   ├── __init__.py
│   │   ├── routes.py                 # app.js এখানে fetch() করে
│   │   └── helpers/                  # 🔐 Private — api/ internal only
│   │       └── request_validator.py
│   │
│   ├── providers/                    # 🔌 LAYER 1 — AI / External API integrations
│   │   ├── __init__.py
│   │   ├── openai.py                 # AI provider
│   │   └── helpers/                  # 🔐 Private — শুধু providers/ ব্যবহার করবে
│   │       └── session_guard.py
│   │
│   ├── services/                     # 🧠 LAYER 1 — Business Logic
│   │   ├── __init__.py
│   │   ├── profile.py                # Profile scraping & analysis
│   │   ├── outreach.py               # Connection & message automation
│   │   ├── job.py                    # Job search & apply
│   │   └── helpers/                  # 🔐 Private — শুধু services/ ব্যবহার করবে
│   │       └── message_builder.py
│   │
│   ├── browser/                      # 🧠 LAYER 1
│   │   ├── __init__.py
│   │   ├── manager.py                # Manages the LinkedIn browser session lifecycle and delegates tasks to scrapers/actors.
│   │   ├── session.py                # Session manager — manages browser profiles, session state, and runtime identity.
│   │   ├── actors/                   # 🔐 Private browser/ internal only actors is to change something or take an action through the browser. For example: submitting a form
│   │   │   ├── auth.py
│   │   │   ├── interactor.py
│   │   │   └── profile_editor.py
│   │   ├── scrapers/                 # 🔐 Private browser/ internal only scrapers/ is just to extract data or read information from the browser. For example read job listings and send them to the database or service.
│   │   │   ├── profile.py
│   │   │   ├── company.py
│   │   │   └── connections.py
│   │   └── helpers/                  # 🔐 Private
│   │       └── dom.py
│   │
│   ├── tools/                        # L4 — Interface layer
│   │    ├── helpers/                 # 🔐 Private
│   │    └── search.py
│   │
│   └── helpers/                      # 🌐 GLOBAL Helpers — সবাই ব্যবহার করতে পারে
│       ├── logger.py
│       └── exceptions.py
│       └── date_utils.py
│
├── web/                              # 🖥️ Frontend (সম্পূর্ণ আলাদা জগৎ)
│   ├── app.js                        # fetch(`${API_BASE}/profiles`) করে
│   ├── index.html
│   └── style.css
│
├── docs/
│
├── tests/                            # src/ এর mirror
│   ├── test_services/
│   └── test_api/
│
├── .env                              # Config যদি একটি Gear Box হয় তাহলে এই .env Secrets হচ্ছে ড্রাইভার, যে কনফিগ কে ম্যানুপুলেট করতে পারে।
├── main.py                           # Entry point
└── pyproject.toml
```

### Canonical Project Structure Example-2

```
project_root/
├── main.py                  # Entry point — Flask server
├── pyproject.toml           # Dependencies
├── src/
│   ├── api/
│   │   └── routes.py        # All REST API endpoints
│   ├── core/
│   │   └── commands.py      # ← Add new ADB commands here
│   ├── services/
│   │   ├── device.py        # Device info & command execution
│   │   ├── profile.py       # Backup/restore/rename logic
│   │   └── dns.py           # DNS speed test
│   ├── providers/
│   │   └── adb.py           # Low-level ADB wrapper
│   ├── schema/
│   │   └── models.py        # Pydantic data models
│   └── config/              # App settings
├── static/
│   ├── index.html           # Single-page UI
│   ├── css/style.css        # All styles
│   └── js/app.js            # Frontend logic
└── profiles_data/           # Saved backup JSON files
```

### Canonical Project Structure Example-2.1 with local import relations

```
epic-adb/
├── docs/
│   ├── img/
│   └── /docs/commands.md
├── logs/
├── profiles_data/
│   └── /profiles_data/profiles.json
├── src/
│   ├── api/
│   │   ├── /src/api/__init__.py  # .routes
│   │   └── /src/api/routes.py  # src.services, src.schema
│   ├── config/
│   │   ├── /src/config/__init__.py  # .paths, .files, .dotenv, .settings
│   │   └── /src/config/settings.py
│   ├── core/
│   │   ├── /src/core/__init__.py  # .commands
│   │   └── /src/core/commands.py  # src.schema.models
│   ├── helpers/
│   │   ├── /src/helpers/date_utils.py
│   │   ├── /src/helpers/logger.py  # src.config.settings
│   │   ├── /src/helpers/network.py
│   │   └── /src/helpers/responses.py  # src.helpers.date_utils, src.schema.models
│   ├── providers/
│   │   ├── /src/providers/__init__.py  # .adb
│   │   └── /src/providers/adb.py  # src.config
│   ├── schema/
│   │   ├── /src/schema/__init__.py  # .models
│   │   └── /src/schema/models.py
│   └── services/
│       ├── /src/services/__init__.py  # .device, .dns, .profile
│       ├── /src/services/device.py  # src.providers, src.schema
│       ├── /src/services/dns.py  # src.providers, src.schema
│       └── /src/services/profile.py  # .device, src.config, src.core, src.providers, src.schema
├── static/
│   ├── css/
│   │   └── /static/css/style.css
│   ├── js/
│   │   └── /static/js/app.js
│   └── /static/index.html
├── tests/
│   ├── /tests/__init__.py
│   ├── /tests/test_adb_commands.py  # src.providers, src.schema.models, src.services
│   ├── /tests/test_app.py  # src.main
│   └── /tests/test_config.py  # src.config
├── /main.py  # src.config, src.api
├── /pyproject.toml
├── /README.md
└── /tree.py
```
### Canonical Project Structure Example-3

```
ClassLens/
│
├── main.py                          # Entry point — FastAPI server boot
├── worker.py                        # Entry point — Pipeline worker boot
├── pyproject.toml
├── .env
├── .env.example
│
├── src/
│   │
│   ├── config/                      # ⚙️ Single Source of Truth
│   │   ├── __init__.py
│   │   ├── paths.py
│   │   ├── files.py
│   │   ├── dotenv.py
│   │   └── settings.py              # EduWatchSettings extends BaseProjectSettings
│   │
│   ├── schema/                      # 📐 Data Contracts — পরম সত্য
│   │   ├── __init__.py
│   │   ├── student.py               # Student, GuardianContact
│   │   ├── detection.py             # DetectionResult, FaceMatch
│   │   ├── attendance.py            # AttendanceRecord, DailyAggregate
│   │   ├── behavior.py              # BehaviorEvent, BehaviorScore
│   │   ├── report.py                # WeeklyReport, ReportDelivery
│   │   └── pipeline.py              # PipelineEvent, PipelineStatus
│   │
│   ├── core/                        # 🧠 Pure Business Logic
│   │   ├── __init__.py
│   │   ├── settings.py              # EduWatchSettings (extends BaseProjectSettings)
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            # PipelineEngine — orchestrates all stages
│   │   │   ├── registry.py          # ModuleRegistry — plugin loader
│   │   │   └── base.py              # BasePipelineModule (ABC)
│   │   ├── voting.py                # Attendance voting logic
│   │   └── aggregator.py           # Daily/weekly aggregation logic
│   │
│   ├── modules/                     # 🔌 Pipeline Modules (Plugin System)
│   │   ├── __init__.py
│   │   ├── base.py                  # BasePipelineModule (ABC) — contract
│   │   │
│   │   ├── ingestion/               # Phase 1
│   │   │   ├── __init__.py
│   │   │   └── frame_sampler.py     # RTSPFrameSampler
│   │   │
│   │   ├── vision/                  # Phase 2
│   │   │   ├── __init__.py
│   │   │   ├── face_detector.py     # InsightFaceFaceDetector
│   │   │   ├── embedder.py          # ArcFaceEmbedder
│   │   │   └── matcher.py           # VectorDBMatcher
│   │   │
│   │   ├── behavior/                # Phase 3 — Future modules এখানে আসবে
│   │   │   ├── __init__.py
│   │   │   ├── head_pose.py         # HeadPoseAnalyzer
│   │   │   ├── drowsiness.py        # DrowsinessDetector
│   │   │   ├── phone_detector.py    # PhoneDetector
│   │   │   └── seat_tracker.py      # SeatPresenceTracker
│   │   │
│   │   └── reporting/               # Phase 5
│   │       ├── __init__.py
│   │       ├── sms.py               # SMSReporter
│   │       ├── push.py              # PushNotificationReporter
│   │       └── dashboard.py         # DashboardReporter
│   │
│   ├── providers/                   # 🔌 External Service Wrappers
│   │   ├── __init__.py
│   │   ├── vector_db.py             # ChromaDB / pgvector abstraction
│   │   ├── llm.py                   # OpenAI / Claude for report generation
│   │   ├── sms.py                   # SSL Wireless API
│   │   └── camera.py                # RTSP stream provider
│   │
│   ├── services/                    # 🏗️ Use-case orchestration
│   │   ├── __init__.py
│   │   ├── enrollment.py            # Student face enrollment
│   │   ├── attendance.py            # Attendance CRUD + aggregation
│   │   ├── behavior.py              # Behavior event CRUD + scoring
│   │   ├── report.py                # Weekly report generation + delivery
│   │   └── helpers/
│   │       └── report_builder.py    # Bengali LLM prompt builder
│   │
│   ├── api/                         # 🚪 HTTP Interface (FastAPI)
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── enrollment.py        # POST /students/enroll
│   │   │   ├── attendance.py        # GET /attendance/{date}
│   │   │   ├── behavior.py          # GET /behavior/{student_id}
│   │   │   └── reports.py           # GET /reports/weekly
│   │   └── helpers/
│   │       └── auth.py              # JWT middleware
│   │
│   ├── db/                          # 🗄️ Database Layer
│   │   ├── __init__.py
│   │   ├── connection.py            # Async SQLAlchemy engine
│   │   ├── migrations/              # Alembic migrations
│   │   └── repositories/
│   │       ├── student.py
│   │       ├── detection.py
│   │       ├── attendance.py
│   │       └── behavior.py
│   │
│   └── helpers/                     # 🌐 Global Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── exceptions.py
│       └── date_utils.py
│
├── tests/
│   ├── test_modules/
│   ├── test_services/
│   └── test_api/
│
└── docs/
    └── architecture.md
```