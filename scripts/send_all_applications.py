#!/usr/bin/env python3
"""Send all 11 job application emails with CV + cover letter attachments."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()

SENDER = os.environ.get("GMAIL_SENDER", "you@example.com")
PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
if not PASSWORD:
    print("ERROR: GMAIL_APP_PASSWORD not set")
    exit(1)

BASE = Path(__file__).parent.parent
CV_DIR = BASE / "cv"
COVER_DIR = BASE / "cover_letters"

applications = [
    {
        "to": "founders@serra.io",
        "subject": "Application: Founding Engineer — Mario Aquino",
        "body": """Dear Serra team,

I am applying for the Founding Engineer role. I have been following Serra's mission to transform how skilled trades are hired in the US, and I believe my experience building full-stack products and data pipelines at early-stage startups makes me a strong fit.

My background aligns with what you need:
- Full-stack at speed: Built and shipped MVPs in under 72 hours at Syloper, using React, Next.js, and Node.js
- Data pipelines: Designed web scrapers at Magnar that collect and normalize public legal documents from government sources across three countries
- Cloud-native on AWS: Architected backend services at SalesMatch.Ai using Node.js, NestJS, Docker, Kubernetes, with CI/CD that cut deployment time 50%
- AI automation: Built multi-agent LLM workflows (Ollama, LangChain, n8n) that reduced operational friction

What excites me about Serra is the scale: 2M+ skilled candidates and 500+ hires made. I want to be the engineer who helps take that from hundreds to thousands.

I am based in Argentina, fully remote-ready, and open to relocation. My CV and cover letter are attached.

Looking forward to hearing from you.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
    },
    {
        "to": "paytransparency@clickhouse.com",
        "subject": "Application: AI Product Engineer — Mario Aquino",
        "body": """Dear ClickHouse team,

I am applying for the AI Product Engineer role. With 5+ years building data pipelines and AI automation systems at early-stage startups, I bring:

- Data engineering: Designed web scrapers at Magnar that collect and normalize public legal documents from government sources across three countries, feeding an AI platform
- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n) that reduced operational friction at two startups
- Backend at scale: Architected cloud-native services on AWS using Node.js, TypeScript, NestJS, Docker, Kubernetes
- Database optimization: Optimized PostgreSQL and Redis queries, achieving 45% improvement in API response times

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_clickhouse_ai.pdf",
        "cover": COVER_DIR / "cover_clickhouse_ai.pdf",
    },
    {
        "to": "careers@launchdarkly.com",
        "subject": "Application: Backend Engineer, Flag Delivery — Mario Aquino",
        "body": """Dear LaunchDarkly team,

I am applying for the Backend Engineer role. With 5+ years building scalable backend services at early-stage startups:

- Backend at scale: Architected cloud-native services on AWS using Node.js, TypeScript, NestJS, Docker, Kubernetes
- CI/CD and reliability: Optimized deployment pipelines (50% faster), automated test suites (30% more stable)
- API design: Designed REST APIs reducing integration issues by 40%
- Distributed systems: Built event-driven architectures with Kafka, RabbitMQ, MQTT

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_launchdarkly_backend.pdf",
        "cover": COVER_DIR / "cover_launchdarkly_backend.pdf",
    },
    {
        "to": "experts@storetasker.com",
        "subject": "Application: Senior Shopify Developer — Mario Aquino",
        "body": """Dear Storetasker team,

I am applying for the Senior Shopify Developer role. With 5+ years building web applications at startups:

- Full-stack: Shipped MVPs in under 72 hours using React, Next.js, Node.js
- Database optimization: 45% API improvement via PostgreSQL/Redis tuning
- Component libraries: Created reusable UI libraries (30% faster frontend delivery)
- Cloud: AWS, Docker, Kubernetes, CI/CD

I am remote-ready, fast learner, comfortable with new stacks. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_storetasker_shopify.pdf",
        "cover": COVER_DIR / "cover_storetasker_shopify.pdf",
    },
    {
        "to": "support@askclera.com",
        "subject": "Application: Founding Software Engineer — Mario Aquino",
        "body": """Dear Clera team,

I am applying for the Founding Software Engineer role. As a full-stack engineer with experience building cloud-native products at early-stage startups, I am drawn to the challenge of transforming insurance workflows with AI.

My experience maps directly to what you need:
- TypeScript and Python backends: Architected scalable services at SalesMatch.Ai using Node.js, TypeScript, NestJS, with Python automation workflows
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n) that reduced operational friction at two startups
- AWS and infrastructure: Designed cloud-native infrastructure on AWS with Docker, Kubernetes, and CI/CD pipelines that cut deployment time 50%
- Rapid delivery: Shipped validated MVPs in under 72 hours at Syloper, using React, Next.js, and Node.js

I am based in Argentina, fully remote-ready, and open to relocation. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_clera_founding.pdf",
        "cover": COVER_DIR / "cover_clera_founding.pdf",
    },
    {
        "to": "darren@recruitslab.com",
        "subject": "Application: Founding Senior AI/ML Engineer — Mario Aquino",
        "body": """Dear Darren,

I am applying for the Founding Senior AI/ML Engineer role. With 5+ years building AI automation systems and data pipelines at early-stage startups, I am excited about the opportunity to lead technical development at a real estate AI company.

My background aligns with your needs:
- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n) at SalesMatch.Ai and personal projects
- Data pipelines: Designed web scrapers at Magnar that collect and normalize public legal documents from government sources across three countries
- Backend at scale: Architected cloud-native services on AWS using Node.js, TypeScript, NestJS, Docker, Kubernetes
- Full-stack ownership: Shipped MVPs in under 72 hours at Syloper, owning features end-to-end

I am remote-ready, comfortable with autonomy, and bring both technical depth and a builder mindset. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_recruitslab_founding.pdf",
        "cover": COVER_DIR / "cover_recruitslab_founding.pdf",
    },
    {
        "to": "founder@getadvisoryai.com",
        "subject": "Application: Founding Software Engineer — Mario Aquino",
        "body": """Dear AdvisoryAI team,

I am applying for the Founding Software Engineer role. With 5+ years building cloud-native products at early-stage startups:

- Full-stack at speed: MVPs in under 72 hours using React, Next.js, Node.js
- TypeScript/Python backends: Architected scalable services on AWS
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Infrastructure: Docker, Kubernetes, CI/CD (50% deployment reduction)

I am remote-ready (UK hours compatible), based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_advisoryai_founding.pdf",
        "cover": COVER_DIR / "cover_advisoryai_founding.pdf",
    },
    {
        "to": "founder@neuralledger.com",
        "subject": "Application: Full Stack Founding Engineer — Mario Aquino",
        "body": """Dear Neural Ledger team,

I am applying for the Full Stack Founding Engineer role. With 5+ years building cloud-native and AI products:

- Python/FastAPI backends: Built scalable Python backends with Node.js, NestJS
- React/Next.js frontends: Shipped MVPs in under 72 hours
- PostgreSQL and LLM workflows: 45% API improvement, multi-agent LLM systems (Ollama, LangChain, n8n)
- AWS infrastructure: Docker, Kubernetes, CI/CD (50% deployment reduction)

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_neuralledger_founding.pdf",
        "cover": COVER_DIR / "cover_neuralledger_founding.pdf",
    },
    {
        "to": "founder@naviohq.com",
        "subject": "Application: Founding Engineer — Mario Aquino",
        "body": """Dear Navio team,

I am applying for the Founding Engineer role. With 5+ years building cloud-native products and AI automation:

- Full-stack: MVPs in under 72 hours using React, Next.js, Node.js
- AI automation: Multi-agent LLM systems (Ollama, LangChain, n8n)
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- Rapid prototyping: Validated MVPs in under 72 hours

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_navio_founding.pdf",
        "cover": COVER_DIR / "cover_navio_founding.pdf",
    },
    {
        "to": "founder@orangestorm.io",
        "subject": "Application: Full-stack AI Engineer (Founding) — Mario Aquino",
        "body": """Dear Orange Storm team,

I am applying for the Full-stack AI Engineer (Founding) role. With 5+ years building AI automation and cloud-native products:

- AI/LLM engineering: Multi-agent LLM systems (Ollama, LangChain, n8n)
- Full-stack: MVPs in under 72 hours using React, Next.js, Node.js
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- Data pipelines: Web scrapers collecting data from government sources across three countries

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_orangestorm_founding.pdf",
        "cover": COVER_DIR / "cover_orangestorm_founding.pdf",
    },
    {
        "to": "founder@impactcare.org",
        "subject": "Application: Founding VP of Engineering — Mario Aquino",
        "body": """Dear IMPaCT Care team,

I am applying for the Founding VP of Engineering role. With 5+ years building cloud-native products and leading technical teams:

- Technical leadership: Mentored 150+ students (92% satisfaction), reduced PR errors by 40%
- AI/LLM engineering: Multi-agent LLM systems (Ollama, LangChain, n8n)
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction, 30% stability increase)
- Architecture: Clean Architecture (SOLID, DDD), event-driven systems

I am remote-ready, based in Argentina. CV and cover letter attached.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_impactcare_vpe.pdf",
        "cover": COVER_DIR / "cover_impactcare_vpe.pdf",
    },
]

sent = 0
failed = 0
for app in applications:
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = app["to"]
    msg["Subject"] = app["subject"]
    msg.attach(MIMEText(app["body"], "plain"))

    for path in [app["cv"], app["cover"]]:
        if path.exists():
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={path.name}")
            msg.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER, PASSWORD)
            server.send_message(msg)
        print(f"  SENT: {app['subject']} -> {app['to']}")
        sent += 1
    except Exception as e:
        print(f"  FAILED: {app['subject']} -> {app['to']}: {e}")
        failed += 1

print(f"\nDone: {sent} sent, {failed} failed")
