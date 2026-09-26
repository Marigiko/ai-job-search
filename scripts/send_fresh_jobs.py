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

    # Use existing CVs - they're already tailored for these types of roles
    # We'll reuse the Serra CV (founding engineer) and Clera CV (founding SWE) as base templates
    # Since we don't have specific CVs for each, we'll use the ones we have

    applications = [
        {
            "to": "jcoghlan@gitlab.com",
            "subject": "Application: Intermediate Backend Engineer — Mario Aquino",
            "body": """Hi GitLab team,

I'm applying for the Intermediate Backend Engineer role on the Platform Readiness team (posted Aug 4). With 5+ years building cloud-native products at early-stage startups, I bring:

- Backend at scale: Architected cloud-native services on AWS using Node.js, TypeScript, NestJS, Docker, Kubernetes
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n) that reduced operational friction at two startups
- CI/CD: Optimized deployment pipelines, reducing deployment time by 50%
- Rapid delivery: Shipped validated MVPs in under 72 hours at Syloper

I'm comfortable with TypeScript and Python, and excited about GitLab's agentic workflow direction. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "GitLab",
        },
        {
            "to": "founders@peter.md",
            "subject": "Application: Backend Developer — Mario Aquino",
            "body": """Hi Peter MD team,

I'm applying for the Backend Developer role (posted Aug 3). With 5+ years building cloud-native and AI products:

- Node.js/TypeScript backends: Architected scalable services at SalesMatch.Ai using Node.js, TypeScript, NestJS
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n) that reduced operational friction
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
            "cv": CV_DIR / "main_zoominfo_swe.pdf" if (CV_DIR / "main_zoominfo_swe.pdf").exists() else CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "ZoomInfo",
        },
        {
            "to": "mstevens@healthequity.com",
            "subject": "Application: Sr Cloud Applications Engineer — Mario Aquino",
            "body": """Hi HealthEquity team,

I'm applying for the Sr Cloud Applications Engineer role (posted Aug 3). With 5+ years building cloud-native products:

- AWS infrastructure: Architected services using EC2, S3, Lambda, RDS, EKS, Docker, Kubernetes
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- CI/CD: Optimized deployment pipelines, reducing deployment time by 50%
- API design: Designed REST APIs reducing integration issues by 40%

I'm excited about HealthEquity's AI platform on Azure with Claude Code. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_healthcloud_swe.pdf" if (CV_DIR / "main_healthcloud_swe.pdf").exists() else CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "HealthEquity",
        },
        {
            "to": "kkustron@cityofhope.org",
            "subject": "Application: AI Automation Developer — Mario Aquino",
            "body": """Hi City of Hope team,

I'm applying for the AI Automation Developer role (posted Aug 3). With 5+ years building AI automation systems:

- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n) that reduced operational friction at two startups
- Automation workflows: Built internal automation with Python and n8n at SalesMatch.Ai
- Backend at scale: AWS, Docker, Kubernetes, CI/CD
- Web scraping: Designed data pipelines collecting from government sources across three countries

I'm excited about bringing AI automation to healthcare workflows at City of Hope. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_clickhouse_ai.pdf",
            "cover": COVER_DIR / "cover_clickhouse_ai.pdf",
            "company": "City of Hope",
        },
        {
            "to": "founder@hunthorpe.com",
            "subject": "Application: Full Stack Engineer — Mario Aquino",
            "body": """Hi Hunthorpe Labs team,

I'm applying for the Full Stack Engineer role (posted Aug 3). With 5+ years building full-stack products:

- React/Next.js: Built high-performance web apps at Syloper, delivering MVPs in under 72 hours
- Node.js/TypeScript: Architected scalable backends at SalesMatch.Ai
- Database optimization: 45% API improvement via PostgreSQL/Redis tuning
- AWS infrastructure: Docker, Kubernetes, CI/CD (50% deployment reduction)

I'm excited about Hunthorpe's flat culture and gov project work. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "Hunthorpe Labs",
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
            "cv": CV_DIR / "main_celigo_swe.pdf" if (CV_DIR / "main_celigo_swe.pdf").exists() else CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "Celigo",
        },
        {
            "to": "arman@sayvo.ai",
            "subject": "Application: Junior Full Stack Developer — Mario Aquino",
            "body": """Hi Arman,

I'm applying for the Junior Full Stack Developer role at SayVo AI (posted Aug 2). With 5+ years building full-stack and AI products:

- Full-stack JavaScript: Built web apps with React, Next.js, Node.js at Syloper
- AI automation: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- Rapid delivery: Shipped MVPs in under 72 hours
- Database: PostgreSQL, MongoDB, Redis optimization

I'm excited about SayVo AI's AI voice agents and the opportunity to contribute from the ground floor. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_sayvo_jr.pdf" if (CV_DIR / "main_sayvo_jr.pdf").exists() else CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "SayVo AI",
        },
        {
            "to": "david-poll@github.com",
            "subject": "Interest: Staff Software Engineer, Identity — Mario Aquino",
            "body": """Hi GitHub team,

I'm reaching out regarding the Staff Software Engineer, Identity Core role (posted Aug 3). With 5+ years building cloud-native products:

- Backend at scale: Architected cloud-native services on AWS using Node.js, TypeScript, NestJS, Docker, Kubernetes
- AI/LLM engineering: Built multi-agent LLM systems (Ollama, LangChain, n8n)
- CI/CD: Optimized deployment pipelines, reducing deployment time by 50%
- API design: Designed REST APIs reducing integration issues by 40%

I'm excited about GitHub's identity and authorization platform. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
            "cv": CV_DIR / "main_github_staff.pdf" if (CV_DIR / "main_github_staff.pdf").exists() else CV_DIR / "main_serra_founding_engineer.pdf",
            "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
            "company": "GitHub",
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
