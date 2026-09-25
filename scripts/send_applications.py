#!/usr/bin/env python3
"""Send 10 job applications via Gmail SMTP."""
import smtplib, csv, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

import os; sender = os.environ.get('GMAIL_SENDER', 'you@example.com')
password = open('.env').read().split('GMAIL_APP_PASSWORD=')[1].strip()

applications = [
    {
        'to': 'jobs@curai.com',
        'subject': 'Postulacion Senior Software Engineer - Mario Aquino',
        'company': 'Curai Health',
        'body': '''Estimado equipo de Curai,

Me postulo a la posicion de Senior Software Engineer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo sistemas full-stack en produccion y un perfil especializado en plataformas integradas con IA, lo que encaja directamente con la mision de Curai de transformar la salud mediante inteligencia artificial y experiencia clinica.

- Full-stack: Python (FastAPI/Django) y Node.js/NestJS con React; microservicios en AWS con Docker, Kubernetes y CI/CD.
- Integracion con IA: orquestacion de LLM (LangChain, Ollama), flujos multi-agente, prompt engineering y automatizacion con n8n.
- Salud y datos: experiencia normalizando fuentes oficiales/legales hacia plataformas LLM, con foco en calidad y estructura de datos.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'recruiting@flocksafety.com',
        'subject': 'Postulacion Senior Software Engineer, Fullstack - Mario Aquino',
        'company': 'Flock Safety',
        'body': '''Estimado equipo de Flock Safety,

Me postulo a la posicion de Senior Software Engineer, Fullstack. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo sistemas full-stack en produccion y un perfil especializado en arquitecturas cloud-native, pipelines de datos en tiempo real y plataformas de alta confiabilidad.

- Full-stack escalable: Node.js/NestJS, Python y React; microservicios en AWS con Docker, Kubernetes y CI/CD.
- Datos a escala: event-driven architectures con Kafka/RabbitMQ; optimizacion de PostgreSQL y Redis que redujo 45% tiempos de respuesta.
- Cloud-native: disene la estrategia de infraestructura AWS y reduje 50% el tiempo de despliegue con GitHub Actions.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'recruiting@clearcaptions.com',
        'subject': 'Postulacion Web Developer - Mario Aquino',
        'company': 'ClearCaptions',
        'body': '''Estimado equipo de ClearCaptions,

Me postulo a la posicion de Web Developer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos desarrollando aplicaciones web de punta a punta, con especializacion en React, Next.js y Node.js/NestJS, y un fuerte compromiso con la accesibilidad y la experiencia de usuario.

- Web full-stack: React, Next.js, Node.js/NestJS, TypeScript; APIs REST, microservicios en AWS con Docker/Kubernetes.
- UX y accesibilidad: mejore la friccion de usuario en un 25% con mejoras de UI/UX; desarrollo consciente de WCAG y rendimiento.
- Entrega: reduje 50% el tiempo de despliegue con GitHub Actions; MVPs validados en menos de 72 horas.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'cristina.silva@impactcommerce.com',
        'subject': 'Postulacion Frontend Shopify Developer - Mario Aquino',
        'company': 'IMPACT Commerce',
        'body': '''Estimada Cristina,

Me postulo a la posicion de Frontend Shopify Developer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos desarrollando aplicaciones web de alto rendimiento, con especializacion en React, Next.js y arquitecturas e-commerce.

- Frontend y e-commerce: React, Next.js, TypeScript, HTML5, CSS3; temas Shopify personalizados y storefronts modernos.
- Full-stack: Node.js/NestJS y Python; APIs REST documentadas que redujeron un 40% los problemas de integracion.
- Entrega: reduje un 50% el tiempo de despliegue con GitHub Actions; MVPs validados en menos de 72 horas.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'okib@danskebank.dk',
        'subject': 'Application: Front-end (React) Developer - Mario Aquino',
        'company': 'Danske Bank',
        'body': '''Dear Danske Bank Team,

I am applying for the Front-end (React) Developer position for District GenAI. Please find my CV and cover letter attached.

I have over five years building AI-powered products with React in regulated environments, with specialization in cloud-native architectures and GenAI feature delivery.

- Frontend + AI: React, Next.js, TypeScript; GenAI integration (LangChain, Ollama), multi-agent workflows and prompt engineering.
- Regulated quality: API documentation that reduced integration issues by 40%; Clean Architecture (SOLID, DDD).
- Cloud-native: AWS (EKS, EC2, Lambda) with Docker, Kubernetes and CI/CD; cut deployment time by 50% with GitHub Actions.

Fully remote from Argentina, fluent in English (B2+).

Best regards,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'recruiting@crowdstrike.com',
        'subject': 'Postulacion Senior Product Security Engineer - Mario Aquino',
        'company': 'CrowdStrike',
        'body': '''Estimado equipo de CrowdStrike,

Me postulo a la posicion de Senior Product Security Engineer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo sistemas distribuidos a gran escala con un enfoque fuerte en seguridad, desarrollo cloud-native e integracion de IA.

- Arquitecturas seguras y escalables: Node.js/NestJS y Python en AWS con Docker, Kubernetes y CI/CD; event-driven systems con Kafka/RabbitMQ.
- IA productiva: orquestacion de LLM (LangChain, Ollama), flujos multi-agente, prompt engineering y automatizacion con n8n.
- Calidad y seguridad: Clean Architecture (SOLID, DDD), documentacion de APIs que redujo 40% problemas de integracion.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'steve.donahue@entrust.com',
        'subject': 'Postulacion Sr. Platform Engineer - Mario Aquino',
        'company': 'Entrust',
        'body': '''Estimado equipo de Entrust,

Me postulo a la posicion de Sr. Platform Engineer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo plataformas seguras y escalables en cloud-native, con especializacion en infraestructura AWS, Kubernetes y pipelines CI/CD.

- Plataforma y cloud: AWS (EKS, EC2, Lambda) con Docker, Kubernetes y Terraform; reduje 50% el tiempo de despliegue con GitHub Actions.
- Backend escalable: Node.js/NestJS y Python; microservicios event-driven con Kafka/RabbitMQ; optimizacion de PostgreSQL/Redis que redujo 45% tiempos de respuesta.
- Seguridad y calidad: Clean Architecture (SOLID, DDD), codificacion segura, documentacion de APIs que redujo 40% problemas de integracion.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'info@chainzeeper.io',
        'subject': 'Postulacion Full Stack Developer - Mario Aquino',
        'company': 'ChainZeeper',
        'body': '''Estimado equipo de ChainZeeper,

Me postulo a la posicion de Full Stack Developer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos desarrollando aplicaciones web y moviles de punta a punta, con especializacion en React, Next.js, Node.js/NestJS y Python, y experiencia en plataformas blockchain/DeFi y soluciones de IA.

- Full-stack: React, Next.js, Node.js/NestJS, TypeScript, Python; APIs REST/GraphQL, microservicios en AWS con Docker/Kubernetes.
- Blockchain e IA: experiencia en smart contracts, DeFi y soluciones de IA con orquestacion de LLM (LangChain, Ollama) y flujos multi-agente.
- Entrega: reduje un 50% el tiempo de despliegue con GitHub Actions; MVPs validados en menos de 72 horas.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': '-eng@cardiff.co',
        'subject': 'Postulacion Senior Full-Stack Engineer (AI-Native) - Mario Aquino',
        'company': 'Cardiff',
        'body': '''Estimado equipo de Cardiff,

Me postulo a la posicion de Senior Full-Stack Engineer (AI-Native). Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo plataformas full-stack integradas con IA, con especializacion en cloud-native (AWS, Docker, Kubernetes), pipelines de datos y sistemas de bajo riesgo.

- Full-stack + IA: Node.js/NestJS, Python y React; orquestacion de LLM (LangChain, Ollama), flujos multi-agente y prompt engineering.
- Datos y fintech: pipelines de datos normalizados hacia plataformas LLM; optimizacion de PostgreSQL/Redis que redujo 45% tiempos de respuesta.
- Cloud-native: AWS (EKS, EC2, Lambda) con Docker, Kubernetes y CI/CD; reduje 50% el tiempo de despliegue con GitHub Actions.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev
'''
    },
    {
        'to': 'hr@mrioa.com',
        'subject': 'Postulacion Remote QA Engineer - Mario Aquino',
        'company': 'Medical Review Institute',
        'body': '''Estimado equipo de Medical Review Institute,

Me postulo a la posicion de Remote Quality Assurance Engineer. Adjunto mi CV y carta de presentacion.

Tengo mas de cinco anos construyendo software confiable y compliant, con especializacion en sistemas de datos en el ambito de salud, flujos de validacion y controles de calidad.

- Calidad y compliance: experiencia normalizando fuentes oficiales hacia plataformas LLM con controles de calidad; desarrollo consciente de regulacion.
- Testing y validacion: Jest, pruebas automatizadas, documentacion de APIs que redujo 40% problemas de integracion.
- Cloud-native: AWS (EKS, EC2, Lambda) con Docker, Kubernetes y CI/CD; reduje 50% el tiempo de despliegue con GitHub Actions.

Modalidad 100% remota desde Argentina.

Quedo a disposicion.

Saludos cordiales,
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

        # Find company key for PDF files
        company_key = {
            'Curai Health': 'curai', 'Flock Safety': 'flock', 'ClearCaptions': 'clearcaptions',
            'IMPACT Commerce': 'impact', 'Danske Bank': 'danske', 'CrowdStrike': 'crowdstrike',
            'Entrust': 'entrust', 'ChainZeeper': 'chainz', 'Cardiff': 'cardiff',
            'Medical Review Institute': 'mrioa'
        }[app['company']]

        for p in [f'cv/main_{company_key}.pdf', f'cover_letters/cover_{company_key}.pdf']:
            if Path(p).exists():
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(Path(p).read_bytes())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{Path(p).name}"')
                msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo()
            s.starttls()
            s.login(sender, password)
            s.send_message(msg)

        print(f"  ENVIADO: {app['company']} -> {app['to']}")
        sent += 1
        time.sleep(2)  # avoid rate limiting
    except Exception as e:
        print(f"  ERROR: {app['company']} -> {app['to']}: {e}")

print(f"\nTOTAL ENVIADOS: {sent}/{len(applications)}")
