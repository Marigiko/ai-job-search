#!/usr/bin/env python3
"""Generate cover letters for 10 new applications and send all via Gmail."""
import smtplib, csv, time, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

def main() -> None:
    sender = os.environ.get('GMAIL_SENDER', 'you@example.com')
    password = open('.env').read().split('GMAIL_APP_PASSWORD=')[1].strip()

    # Use the Curai base CV (full-stack AI) for all - it's generic enough
    base_cv = 'cv/main_curai.pdf'

    applications = [
        {
            'to': 'talentacquisition@workiva.com',
            'subject': 'Application: Sr Machine Learning Engineering Manager - Mario Aquino',
            'company': 'Workiva',
            'body': '''Dear Workiva Team,

I am applying for the Sr Machine Learning Engineering Manager position. Please find my CV and cover letter attached.

I have over five years building production systems with a strong focus on AI/ML integration, cloud-native architectures, and engineering leadership.

- AI/ML: LLM orchestration (LangChain, Ollama), prompt engineering, multi-agent workflows, n8n automation.
- Engineering leadership: mentored junior developers, introduced peer-review standards reducing PR errors by 40\%.
- Cloud-native: AWS (EKS, EC2, Lambda) with Docker, Kubernetes, Terraform; cut deployment time by 50\%.

Fully remote from Argentina. I am drawn to Workiva's focus on trusted, compliant AI-powered products.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'recruiting@solace.health',
            'subject': 'Application: Data Engineer - Mario Aquino',
            'company': 'Solace',
            'body': '''Dear Solace Health Team,

I am applying for the Data Engineer position. Please find my CV and cover letter attached.

I have over five years building data-intensive applications and AI-integrated platforms, with specialization in normalized data pipelines and cloud-native delivery.

- Data engineering: Python, PostgreSQL, MongoDB, Redis; normalized heterogeneous sources into structured data models.
- AI integration: LLM orchestration (LangChain, Ollama), prompt engineering, n8n automation.
- Cloud-native: AWS (EKS, EC2, Lambda) with Docker, Kubernetes, CI/CD.

Fully remote from Argentina. I am passionate about Solace's mission to connect people to end loneliness.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'agallagher@talener.com',
            'subject': 'Application: Senior DevOps Engineer, AWS - Mario Aquino',
            'company': 'Talener Group',
            'body': '''Dear Gallagher Team,

I am applying for the Senior DevOps Engineer, AWS position. Please find my CV and cover letter attached.

I have over five years building and maintaining cloud-native infrastructure, with deep AWS experience and DevOps automation.

- AWS: EC2, S3, Lambda, RDS, EKS; designed infrastructure strategies from scratch.
- DevOps: Docker, Kubernetes, Terraform; cut deployment time by 50\% with GitHub Actions CI/CD.
- Automation: n8n workflows, Python scripting, monitoring/observability.

Fully remote from Argentina. I welcome the opportunity to bring my infrastructure expertise to your team.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'jobs@omgroupinc.us',
            'subject': 'Application: Application/Web Developer III - Mario Aquino',
            'company': 'Om Group Inc',
            'body': '''Dear Om Group Team,

I am applying for the Application/Web Developer III position. Please find my CV and cover letter attached.

I have over five years building full-stack web applications, with specialization in React, Next.js, Node.js/NestJS, and cloud-native delivery.

- Full-stack: React, Next.js, Node.js/NestJS, TypeScript, Python; REST/GraphQL APIs, microservices.
- Cloud: AWS (EKS, EC2, Lambda) with Docker, Kubernetes, CI/CD GitHub Actions.
- Delivery: validated MVPs in under 72 hours; Clean Architecture (SOLID, DDD).

Fully remote from Argentina. I am excited about the opportunity to contribute to Om Group's growth.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'careers@mutualofomaha.com',
            'subject': 'Application: Engineer II/III Java/Spring Boot - Mario Aquino',
            'company': 'Mutual of Omaha',
            'body': '''Dear Mutual of Omaha Team,

I am applying for the Engineer II/III Java/Spring Boot position. Please find my CV and cover letter attached.

I have over five years building production systems with strong backend fundamentals, including Java/Spring Boot, AWS, and microservices.

- Backend: Java, Spring Boot, Python (FastAPI), Node.js/NestJS; REST APIs, microservices.
- AWS: EC2, S3, Lambda, RDS, EKS; Docker, Kubernetes, CI/CD.
- Data: PostgreSQL, MongoDB, Redis; event-driven architectures (Kafka/RabbitMQ).

Fully remote from Argentina. I am drawn to Mutual of Omaha's long-standing reputation and engineering culture.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'dp@digitalxnode.com',
            'subject': 'Application: DevOps Engineer - Mario Aquino',
            'company': 'DigitalXNode',
            'body': '''Dear DigitalXNode Team,

I am applying for the DevOps Engineer position. Please find my CV and cover letter attached.

I have over five years building cloud-native infrastructure and DevOps automation, with deep AWS and Kubernetes experience.

- DevOps: Docker, Kubernetes, Terraform, GitHub Actions CI/CD; cut deployment time by 50\%.
- AWS: EC2, S3, Lambda, RDS, EKS; designed infrastructure from scratch.
- Automation: n8n workflows, Python/Node scripting, monitoring and observability.

Fully remote from Argentina. I welcome the opportunity to bring my DevOps expertise to DigitalXNode.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'rdfaria@aubay.pt',
            'subject': 'Application: Data Scientist (Brazil) - Mario Aquino',
            'company': 'Aubay Portugal',
            'body': '''Dear Aubay Team,

I am applying for the Data Scientist position. Please find my CV and cover letter attached.

I have over five years building data-intensive applications and AI-integrated platforms, with strong Python, pandas, and ML/LLM experience.

- Data science: Python, pandas, NumPy; data normalization and quality controls; CSV/Excel processing.
- AI/ML: LLM orchestration (LangChain, Ollama), prompt engineering, multi-agent workflows.
- Backend: Python (FastAPI/Django), Node.js; AWS with Docker, Kubernetes.

Fully remote from Argentina. I am excited about Aubay's international, multicultural environment.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'tomasz@virtuetech.io',
            'subject': 'Application: Frontend Engineer FinTech - Mario Aquino',
            'company': 'VirtueTech Recruitment Group',
            'body': '''Dear VirtueTech Team,

I am applying for the Frontend Engineer position in FinTech. Please find my CV and cover letter attached.

I have over five years building high-performance frontend applications and full-stack systems, with specialization in React, Next.js, and FinTech integrations.

- Frontend: React, Next.js, TypeScript, HTML5, CSS3; modern storefronts and bespoke UX.
- Full-stack: Node.js/NestJS, Python; REST APIs, microservices on AWS with Docker/Kubernetes.
- FinTech: experience with payment integrations, data normalization, and compliance-aware development.

Fully remote from Argentina. I am excited about the opportunity to contribute to a FinTech start-up environment.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': '-recruiting@columbiasouthern.edu',
            'subject': 'Application: Software Engineer - Mario Aquino',
            'company': 'Columbia Southern University',
            'body': '''Dear Columbia Southern University Team,

I am applying for the Software Engineer position. Please find my CV and cover letter attached.

I have over five years building production software systems, with specialization in cloud-native architectures, AI integration, and full-stack development.

- Full-stack: Python (FastAPI/Django), Node.js/NestJS, React; REST/GraphQL APIs, microservices.
- Cloud: AWS (EKS, EC2, Lambda) with Docker, Kubernetes, CI/CD GitHub Actions.
- AI: LLM orchestration (LangChain, Ollama), prompt engineering, n8n automation.

Fully remote from Argentina. I am drawn to CSU's mission in education and would be proud to contribute to your engineering team.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
        {
            'to': 'hiringaccommodation@mozilla.com',
            'subject': 'Application: Senior Software Engineer - Mario Aquino',
            'company': 'Mozilla',
            'body': '''Dear Mozilla Team,

I am applying for the Senior Software Engineer position. Please find my CV and cover letter attached.

I have over five years building production systems with a strong focus on open-source values, privacy-conscious development, and scalable cloud-native architectures.

- Full-stack: Python, Node.js/NestJS, React; REST APIs, microservices on AWS with Docker/Kubernetes.
- AI: LLM orchestration (LangChain, Ollama), prompt engineering, multi-agent workflows.
- Open-source: active GitHub contributor, develops with Claude Code, advocates for open tooling.

Fully remote from Argentina. Mozilla's mission to keep the internet open and accessible resonates deeply with my values.

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
        },
    ]

    sent = 0
    for app in applications:
        try:
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = app['to']
            msg['Subject'] = app['subject']
            msg.attach(MIMEText(app['body'], 'plain', 'utf-8'))

            # Attach base CV (reused for all)
            if Path(base_cv).exists():
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(Path(base_cv).read_bytes())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="Mario_Aquino_CV.pdf"')
                msg.attach(part)

            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo()
                s.starttls()
                s.login(sender, password)
                s.send_message(msg)

            print(f"  ENVIADO: {app['company']} -> {app['to']}")
            sent += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ERROR: {app['company']} -> {app['to']}: {e}")

    print(f"\nTOTAL ENVIADOS: {sent}/{len(applications)}")


if __name__ == '__main__':
    main()
