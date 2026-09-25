#!/usr/bin/env python3
"""Send batch 3 applications to fresh US jobs."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

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

BASE = Path(__file__).parent.parent
CV_DIR = BASE / "cv"
COVER_DIR = BASE / "cover_letters"

applications = [
    {
        "to": "cchantala@indeed.com",
        "subject": "Application: Software Engineer III — Mario Aquino",
        "body": """Hi Indeed team,

I'm applying for the Software Engineer III role (posted Aug 3). With 5+ years building cloud-native products at early-stage startups:

- React/TypeScript: Built high-performance web apps with React, Next.js, and TypeScript at Syloper and SalesMatch.Ai
- APIs and GraphQL: Designed comprehensive REST APIs, reducing cross-team integration issues by 40%
- Backend at scale: Node.js, NestJS, AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- Database: PostgreSQL, MongoDB, Redis optimization (45% API improvement)
- Data visualization: Built dashboards and analytics interfaces at SalesMatch.Ai

I'm excited about Indeed's Hiring Insights product and the opportunity to build data-driven experiences that help people get jobs. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "Indeed",
    },
    {
        "to": "founder@shmusik.com",
        "subject": "Application: Web Developer — Mario Aquino",
        "body": """Hi Shmusik team,

I'm applying for the Web Developer role (posted Aug 1). With 5+ years building web applications:

- Frontend: React, Angular, Vue.js, Next.js, TypeScript, HTML5, CSS3, Bootstrap
- Backend: Node.js, Python, PHP, Django, Express - RESTful APIs, GraphQL
- Database: MySQL, PostgreSQL, MongoDB, SQL optimization
- Cloud: AWS, Docker, CI/CD (GitHub Actions), Jenkins
- DevOps: Git, Docker, Ansible, Azure deployment

I'm excited about the opportunity to build cutting-edge web applications at Shmusik. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "Shmusik",
    },
    {
        "to": "jaya@bvteck.com",
        "subject": "Application: Conversational AI Engineer — Mario Aquino",
        "body": """Hi BV Teck team,

I'm applying for the Conversational AI Engineer role (posted Aug 3). With 5+ years building AI/LLM systems:

- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n) at SalesMatch.Ai and personal projects
- Python: Built scalable backends and automation workflows
- RAG and agents: Experience with retrieval-augmented generation and agentic architectures
- API integrations: Designed REST APIs reducing integration issues by 40%
- Cloud: AWS, Docker, Kubernetes, CI/CD

I'm excited about building enterprise conversational AI and LLM-powered applications. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_clickhouse_ai.pdf",
        "cover": COVER_DIR / "cover_clickhouse_ai.pdf",
        "company": "BV Teck",
    },
    {
        "to": "careers@mercola.com",
        "subject": "Application: Systems Engineer, Full-Stack Infrastructure — Mario Aquino",
        "body": """Hi Mercola team,

I'm applying for the Systems Engineer — Full-Stack Infrastructure role (posted Aug 3). With 5+ years building cloud-native products and infrastructure:

- Full-stack: React, Next.js, Node.js, TypeScript, Python
- Cloud and infrastructure: AWS (EC2, S3, Lambda, RDS, EKS), Docker, Kubernetes, Terraform
- CI/CD: Optimized deployment pipelines, reducing deployment time by 50%
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Database: PostgreSQL, MongoDB, Redis optimization (45% API improvement)

I'm excited about Mercola's health-focused mission and the opportunity to own infrastructure end-to-end. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "Mercola",
    },
    {
        "to": "taposting@wwt.com",
        "subject": "Application: Execution Engineer, AI Execution Platforms — Mario Aquino",
        "body": """Hi WWT team,

I'm applying for the Execution Engineer (Full-Stack) – AI Execution Platforms role (posted Aug 3). With 5+ years building cloud-native and AI products:

- Full-stack: React, Next.js, Node.js, TypeScript, Python
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- APIs and integrations: Designed REST APIs reducing integration issues by 40%
- Cloud: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- AI coding tools: Experienced with Claude Code and AI-assisted development

I'm excited about WWT's AI execution platforms and the opportunity to build reusable solutions. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "WWT",
    },
    {
        "to": "careers@zoominfo.com",
        "subject": "Application: Senior Software Engineer, IDP — Mario Aquino",
        "body": """Hi ZoomInfo team,

I'm applying for the Senior Software Engineer - IDP role (posted Aug 3). With 5+ years building cloud-native products and AI systems:

- TypeScript/Node.js backends: Architected scalable services at SalesMatch.Ai
- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- API design: Designed comprehensive REST APIs, reducing integration issues by 40%

I'm excited about ZoomInfo's Backstage IDP with LLM/MCP server integration. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "ZoomInfo",
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
        print(f"  SENT: {app['company']} -> {app['to']}")
        sent += 1
    except Exception as e:
        print(f"  FAILED: {app['company']} -> {app['to']}: {e}")
        failed += 1

print(f"\nDone: {sent} sent, {failed} failed")
