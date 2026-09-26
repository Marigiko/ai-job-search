#!/usr/bin/env python3
"""Send batch applications to 10 fresh US jobs (posted Aug 1-4, 2026)."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

def main() -> None:
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
            "to": "hr@mercola.com",
            "subject": "Application: Systems Engineer, Full-Stack Infrastructure — Mario Aquino",
            "body": """Hi Mercola team,

I'm applying for the Systems Engineer — Full-Stack Infrastructure role (posted Aug 3). With 5+ years building cloud-native products and infrastructure:

- Full-stack development: React, Next.js, Node.js, TypeScript, Python
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
            "to": "jcoghlan@gitlab.com",
            "subject": "Application: Intermediate Backend Engineer, Platform Readiness — Mario Aquino",
            "body": """Hi GitLab team,

I'm applying for the Intermediate Backend Engineer role on the Platform Readiness team (posted Aug 4). With 5+ years building cloud-native products:

- Backend: Node.js, TypeScript, NestJS, Python
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- CI/CD: Optimized deployment pipelines, reducing deployment time by 50%
- Database: PostgreSQL, MongoDB, Redis optimization
- Cloud: AWS, Docker, Kubernetes

I'm comfortable with TypeScript and Python, and excited about GitLab's agentic workflow direction. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_recruitslab_founding.pdf",
            "cover": COVER_DIR / "cover_recruitslab_founding.pdf",
            "company": "GitLab",
        },
        {
            "to": "kkustron@cityofhope.org",
            "subject": "Application: AI Automation Developer — Mario Aquino",
            "body": """Hi City of Hope team,

I'm applying for the AI Automation Developer role (posted Aug 3). With 5+ years building AI automation systems:

- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Automation workflows: Built internal automation with Python and n8n at SalesMatch.Ai
- Backend at scale: AWS, Docker, Kubernetes, CI/CD
- Data pipelines: Designed web scrapers collecting from government sources across three countries

I'm excited about bringing AI automation to healthcare workflows at City of Hope. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_clickhouse_ai.pdf",
            "cover": COVER_DIR / "cover_clickhouse_ai.pdf",
            "company": "City of Hope",
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
        {
            "to": "tal.valler@celigo.com",
            "subject": "Application: Senior Developer — Mario Aquino",
            "body": """Hi Celigo team,

I'm applying for the Senior Developer role (posted Aug 2). With 5+ years building cloud-native products:

- JavaScript/TypeScript: Architected scalable services at SalesMatch.Ai using Node.js, TypeScript, NestJS
- API integrations: Designed REST APIs reducing integration issues by 40%
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)

I'm excited about Celigo's AI Studio and agentic workflow capabilities. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "Celigo",
        },
        {
            "to": "connect@theteammc.com",
            "subject": "Application: Junior Full-Stack Developer — Mario Aquino",
            "body": """Hi Globixs team,

I'm applying for the Junior Full-Stack Developer role (posted Aug 1). With 5+ years building full-stack products:

- Next.js/TypeScript: Built high-performance web apps at Syloper with React, Next.js, Node.js
- Full-stack: Shipped MVPs in under 72 hours
- Database: PostgreSQL, MongoDB, Redis optimization
- Cloud: AWS, Docker, Kubernetes, CI/CD
- Tailwind/shadcn/ui: Experience with modern component libraries

I'm excited about Globixs's junior-friendly approach and the opportunity to contribute. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "Globixs",
        },
        {
            "to": "cara.alcini@cbrands.com",
            "subject": "Application: Software Engineer — Mario Aquino",
            "body": """Hi Constellation Brands team,

I'm applying for the Software Engineer role (posted Aug 3). With 5+ years building cloud-native products:

- Full-stack: React, Next.js, Node.js, TypeScript, Python
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Database: PostgreSQL, MongoDB, Redis optimization (45% API improvement)

I'm excited about contributing to Constellation Brands' technology team. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "Constellation Brands",
        },
        {
            "to": "founders@peter.md",
            "subject": "Application: Backend Developer — Mario Aquino",
            "body": """Hi Peter MD team,

I'm applying for the Backend Developer role (posted Aug 3). With 5+ years building cloud-native and AI products:

- Node.js/TypeScript backends: Architected scalable services at SalesMatch.Ai
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- Rapid delivery: Shipped MVPs in under 72 hours at Syloper

I'm excited about Peter MD's AI assistant layer and telehealth mission. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_recruitslab_founding.pdf",
            "cover": COVER_DIR / "cover_recruitslab_founding.pdf",
            "company": "Peter MD",
        },
        {
            "to": "jrocheford@techglobal.com",
            "subject": "Interest: Applications Developer — Mario Aquino",
            "body": """Hi TechGlobal team,

I'm reaching out regarding the Applications Developer role (posted Aug 1). With 5+ years building cloud-native products:

- Full-stack: React, Next.js, Node.js, TypeScript, Python
- Backend at scale: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Database: PostgreSQL, MongoDB, Redis optimization

I'm excited about contributing to TechGlobal's team. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "TechGlobal",
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


if __name__ == '__main__':
    main()
