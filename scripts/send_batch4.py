#!/usr/bin/env python3
"""Send batch 4 applications."""
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
        "to": "info@newwaltonservices.com",
        "subject": "Application: Mobile Developer — Mario Aquino",
        "body": """Hi New Walton Services team,

I'm applying for the Mobile Developer role (posted Aug 1). With 5+ years building mobile and full-stack products:

- React Native: Built cross-platform mobile applications
- TypeScript/JavaScript: Strong proficiency in modern JS/TS
- REST APIs: Integrated RESTful APIs with mobile backends
- Full-stack: Node.js, React, Next.js, PostgreSQL, MongoDB
- Cloud: AWS, Docker, Kubernetes, CI/CD

I'm excited about WalletPay's invoicing and payments platform, and the opportunity to build mobile payment integrations. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "New Walton Services",
    },
    {
        "to": "nivedita.desai@quantiphi.com",
        "subject": "Interest: Senior Data Engineer, AI Platforms — Mario Aquino",
        "body": """Hi Quantiphi team,

I'm reaching out regarding the Senior Data Engineer role (posted Aug 3). With 5+ years building data pipelines and AI systems:

- Python: Built scalable backends and data pipelines
- Data engineering: Designed web scrapers at Magnar that collect and normalize data from government sources across three countries
- SQL: PostgreSQL, MongoDB, Redis optimization (45% API improvement)
- Cloud: AWS, Docker, Kubernetes, CI/CD (50% deployment reduction)
- AI/LLM: Built multi-agent LLM systems (Ollama, LangChain, n8n)

I'm excited about Quantiphi's AI-first approach and the opportunity to build data platforms for AI use cases. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_clickhouse_ai.pdf",
        "cover": COVER_DIR / "cover_clickhouse_ai.pdf",
        "company": "Quantiphi",
    },
    {
        "to": "aaron@instawork.com",
        "subject": "Application: Webflow Developer — Mario Aquino",
        "body": """Hi Instawork team,

I'm applying for the Webflow Developer role (posted Aug 1). With 5+ years building web applications:

- Frontend: React, Next.js, JavaScript, TypeScript, HTML5, CSS3, Tailwind
- Webflow: Experience building responsive pages from Figma designs
- CMS: Built content management systems and dynamic templates
- SEO: Technical SEO, Core Web Vitals optimization
- API integrations: RESTful APIs, third-party platform integrations

I'm excited about Instawork's mission to create economic opportunities and the chance to contribute to marketing website optimization. Remote-ready from Argentina.

Best,
Mario Aquino
you@example.com | linkedin.com/in/keyzdev""",
        "cv": CV_DIR / "main_serra_founding_engineer.pdf",
        "cover": COVER_DIR / "cover_serra_founding_engineer.pdf",
        "company": "Instawork",
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
