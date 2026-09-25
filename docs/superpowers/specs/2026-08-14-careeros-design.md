# CareerOS — Design Specification

**Date**: 2026-08-14
**Author**: AI Assistant
**Status**: Approved for Implementation

## 1. Problem Statement

The current job-search workspace is a collection of **18 Python scripts**, **8 duplicated email senders** (~1,400 lines), **2 conflicting dashboards**, and **zero tests on the most critical code**. It works, but:

- Adding a new portal means copy-pasting SMTP boilerplate
- The browser apply runner **returns fake success** without doing anything
- Data lives in 6+ inconsistent JSON/CSV files with no schema
- There's no visual pipeline — just static HTML reports
- Config drifts between files (salary targets contradict each other)

## 2. Vision

**CareerOS** — a unified, visual, premium job-search operating system.

### Key Differentiators from Base Project
| Before | After |
|--------|-------|
| 8 duplicated email scripts | 1 outreach module with queue + A/B testing |
| Static HTML dashboard | Live React UI with Kanban + real-time updates |
| JSON files with no schema | SQLite with typed schema + migrations |
| Fake browser apply runner | Real Playwright automation with progress tracking |
| CLI-only search | Unified search UI with multi-portal aggregation |
| Scattered config | Single source of truth in DB + .env |
| Zero tests on critical paths | 80%+ coverage on outreach/pipeline modules |

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CareerOS                                  │
├─────────────────────┬───────────────────────────────────────┤
│   Frontend (React)  │          Backend (FastAPI)             │
│                     │                                        │
│  - Kanban Board     │  - /api/v1/* REST endpoints           │
│  - Funnel Charts    │  - WebSocket for live updates         │
│  - Outreach Composer│  - Background task queue (Celery-like)│
│  - CV/CL Preview    │  - SQLite via SQLAlchemy              │
│  - Search Dashboard │  - Plugin system for portal scrapers  │
│                     │                                        │
├─────────────────────┴───────────────────────────────────────┤
│                    Data Layer                                 │
│  - SQLite (careeros.db)                                      │
│  - Migrations via Alembic                                    │
│  - File storage for CVs/CLs (PDFs)                           │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI + uvicorn | Async, type hints, auto-docs, Python ecosystem |
| ORM | SQLAlchemy 2.0 | Mature, async support, migrations |
| DB | SQLite | Zero-config, single-user, file-based |
| Migrations | Alembic | Standard for SQLAlchemy |
| Frontend | React 18 + Vite | Fast HMR, modern tooling |
| Styling | TailwindCSS 3 | Utility-first, dark-mode native |
| Animations | Framer Motion | Declarative, performant |
| Charts | Recharts | React-native, beautiful |
| State | Zustand | Lightweight, no boilerplate |
| API Client | TanStack Query | Caching, background refresh |
| Task Queue | FastAPI BackgroundTasks + asyncio | No extra infra needed |
| LaTeX | Existing texlive setup | Reuse existing compilation |

## 4. Database Schema

```sql
-- Core entities
companies (
  id, name, domain, industry, size, created_at, updated_at
)

job_postings (
  id, company_id, title, description, url, salary_min, salary_max,
  currency, location, remote_type, visa_sponsorship,
  portal_source, portal_id, status, discovered_at, applied_at,
  notes, raw_data JSON
)

applications (
  id, job_posting_id, status, applied_date, follow_up_date,
  cv_version, cover_letter_version, notes, created_at, updated_at
)

outreach_emails (
  id, application_id, template_id, recipient_email, subject,
  body, status, sent_at, opened_at, replied_at, ab_variant
)

email_templates (
  id, name, subject_template, body_template, language,
  is_ab_test, ab_variant, usage_count, reply_rate, created_at
)

contacts (
  id, company_id, name, email, title, linkedin_url,
  is_recruiter, source, created_at
)

search_queries (
  id, query, portal, last_run, result_count, is_active
)

-- Tracking & analytics
email_events (
  id, outreach_email_id, event_type, metadata JSON, created_at
)

pipeline_snapshots (
  id, snapshot_date, stage_counts JSON, conversion_rates JSON
)
```

## 5. API Design

### Endpoints
```
GET    /api/v1/jobs                    # List jobs (filter, sort, paginate)
POST   /api/v1/jobs                    # Create job manually
GET    /api/v1/jobs/{id}               # Job detail
PATCH  /api/v1/jobs/{id}               # Update job
DELETE /api/v1/jobs/{id}               # Delete job

GET    /api/v1/pipeline                # Pipeline stage counts
GET    /api/v1/pipeline/kanban         # Jobs grouped by stage

POST   /api/v1/outreach/search         # Search contacts
POST   /api/v1/outreach/compose        # Compose email (with A/B)
POST   /api/v1/outreach/send           # Send immediately
POST   /api/v1/outreach/queue          # Queue for later
GET    /api/v1/outreach/queue          # View queue
DELETE /api/v1/outreach/queue/{id}     # Remove from queue

GET    /api/v1/templates               # List email templates
POST   /api/v1/templates               # Create template
PATCH  /api/v1/templates/{id}          # Update template

POST   /api/v1/search                  # Trigger portal search
GET    /api/v1/search/status           # Search job status

POST   /api/v1/documents/generate      # Generate CV/CL
GET    /api/v1/documents/{id}/preview  # Preview PDF
GET    /api/v1/documents/{id}/download # Download PDF

GET    /api/v1/analytics/funnel        # Funnel metrics
GET    /api/v1/analytics/outreach     # Outreach metrics
GET    /api/v1/analytics/salary       # Salary insights

WS     /ws                             # WebSocket for live updates
```

### Response Format
```json
{
  "data": {...},
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

## 6. Frontend Structure

```
careeros-frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # Sidebar, TopBar, MainLayout
│   │   ├── kanban/          # KanbanBoard, StageColumn, JobCard
│   │   ├── jobs/            # JobList, JobDetail, JobForm
│   │   ├── outreach/        # Composer, TemplateEditor, QueueView
│   │   ├── documents/       # CVDocument, CLDocument, Preview
│   │   ├── analytics/       # FunnelChart, MetricCard, TrendLine
│   │   └── ui/              # Button, Modal, Badge, Tooltip
│   ├── pages/
│   │   ├── Dashboard.tsx    # Overview with metrics
│   │   ├── Pipeline.tsx     # Kanban board
│   │   ├── Jobs.tsx         # Job list + search
│   │   ├── Outreach.tsx     # Email composer + queue
│   │   ├── Documents.tsx    # CV/CL generator
│   │   ├── Analytics.tsx    # Charts and insights
│   │   └── Settings.tsx     # Config, templates, portals
│   ├── stores/              # Zustand stores
│   ├── hooks/               # Custom React hooks
│   ├── api/                 # API client + query keys
│   ├── types/               # TypeScript interfaces
│   └── utils/               # Helpers, formatters
```

### Visual Design Tokens
```css
/* Dark Mode Premium */
--bg-primary: #0a0a0f;
--bg-secondary: #12121a;
--bg-tertiary: #1a1a26;
--accent-primary: #6366f1;    /* Indigo */
--accent-secondary: #8b5cf6;  /* Violet */
--accent-success: #10b981;
--accent-warning: #f59e0b;
--accent-danger: #ef4444;
--text-primary: #f1f5f9;
--text-secondary: #94a3b8;
--border-color: #2a2a3a;

/* Typography */
--font-sans: 'Inter', system-ui;
--font-mono: 'JetBrains Mono', monospace;

/* Spacing & Radius */
--radius-sm: 6px;
--radius-md: 10px;
--radius-lg: 16px;
--radius-xl: 24px;
```

## 7. Module Design

### 7.1 Portal Search Module (Plugin System)
```python
# plugins/base.py
class PortalPlugin(ABC):
    name: str
    @abstractmethod
    async def search(self, query: str, filters: dict) -> list[JobPosting]:
        ...

# plugins/remoteok.py, plugins/linkedin.py, etc.
```

### 7.2 Outreach Module
```python
# Outreach service with:
# - Dedup check (replaces dedup.py + 8 senders)
# - Bounce tracking (replaces check_bounced_emails.py)
# - A/B template selection (replaces ab_templates.py)
# - Rate limiting + queue management
# - Preview before send
```

### 7.3 Document Module
```python
# CV/CL generation with:
# - Template selection per company
# - Variable interpolation
# - Async LaTeX compilation
# - PDF preview generation
# - Version tracking
```

### 7.4 Pipeline Module
```python
# Kanban pipeline with:
# - Stage transitions (Applied → Screening → Interview → Offer → Rejected)
# - Follow-up reminders
# - Activity logging
# - Stage duration tracking
```

## 8. Migration Strategy

### Phase 1: Backend Foundation
- Project structure + FastAPI app
- Database models + migrations
- Core CRUD endpoints
- Plugin system skeleton

### Phase 2: Search Integration
- Integrate existing portal skills as plugins
- Unified search endpoint
- Job deduplication + storage

### Phase 3: Outreach System
- Email sending (replaces 8 scripts)
- Template management
- A/B testing
- Dedup + bounce tracking

### Phase 4: Frontend
- Vite + React setup
- Layout + routing
- Kanban board
- Job detail views

### Phase 5: Documents + Analytics
- CV/CL generation
- PDF preview
- Funnel charts
- Metrics dashboard

### Phase 6: Polish
- Animations
- WebSocket live updates
- Settings page
- Final testing

## 9. Testing Strategy

| Module | Coverage Target | Key Tests |
|--------|----------------|-----------|
| Outreach | 90% | Send, dedup, bounce, A/B selection |
| Pipeline | 85% | Stage transitions, reminders, metrics |
| Search | 80% | Plugin interface, dedup, storage |
| Documents | 75% | Generation, compilation, preview |
| API | 80% | All endpoints, auth, validation |

## 10. Security Considerations

- `.env` for secrets (app password, API keys) — single loader, no duplication
- No hardcoded credentials in source
- Input validation via Pydantic
- Rate limiting on email sending
- CORS configuration for local dev

## 11. Performance Targets

- Search aggregation (5 portals): < 3s
- Kanban load (100 jobs): < 200ms
- Email queue processing: 1 email / 30s (rate limited)
- PDF generation: < 5s
- WebSocket latency: < 100ms

## 12. Open Decisions

1. **Monorepo structure**: `careeros/backend/` + `careeros/frontend/` in single repo
2. **Single command startup**: `make dev` starts both backend and frontend
3. **Keep LaTeX as-is**: Compilation via existing texlive, not replacement
4. **No auth needed**: Single-user local app
5. **Data preservation**: Migrate existing JSON data into SQLite on first run
