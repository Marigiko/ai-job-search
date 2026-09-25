#!/usr/bin/env python3
"""Send 3 job applications via Gmail SMTP_SSL with PDF attachments."""
import smtplib, time
from email.message import EmailMessage
from pathlib import Path

import os
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_loader import get_sender

sender = get_sender()
import re
_env = open('.env', encoding='utf-8').read()
_password_match = re.search(r'GMAIL_APP_PASSWORD=(\S+)', _env)
password = _password_match.group(1) if _password_match else ''

applications = [
    {
        'to': 'gbellen.rrhh@gmail.com',
        'subject': 'Application: Software Engineer Python (AI) - Mario Aquino',
        'company': 'Python AI (via G. Bellenin)',
        'body': '''Estimado equipo de contratacion,

Mi nombre es Mario Aquino, soy desarrollador de software con mas de 5 anos 
de experiencia construyendo sistemas backend en produccion con Python 
(FastAPI/Django) y Node.js (NestJS), y experiencia real en sistemas de IA: 
pipelines RAG, orquestacion de agentes, workflows de evaluacion LLM y 
herramientas de prompt, sobre una base solida de infraestructura cloud-native 
(AWS, Docker, Kubernetes).

Me interesa especialmente este rol porque combina backend con IA en produccion, 
exactamente el espacio donde mas he crecido los ultimos dos anos, incluyendo 
mi trabajo actual construyendo pipelines de datos para una plataforma legal-IA.

Construyo con Claude Code y valido el codigo generado antes de integrarlo, 
manteniendo criterio sobre arquitectura y seguridad.

Expectativa salarial: 2500 a 3000 USD mensuales netos, en modalidad 
contractor remota.

Adjuntos: CV y cover letter.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev | github.com/Marigiko
''',
        'cv': 'cv/main_pythonai_arg.pdf',
        'cl': 'cover_letters/cover_pythonai_arg.pdf',
    },
    {
        'to': 'mpassarotti@gmail.com',
        'subject': 'Application: FullStack Developer SSR/SR - Mario Aquino',
        'company': 'HealthTech (via M. Passarotti)',
        'body': '''Estimada Mariana,

Mi nombre es Mario Aquino, soy desarrollador full-stack con mas de 5 anos 
de experiencia construyendo aplicaciones web escalables: frontend en JavaScript, 
backend en Node.js/NestJS, APIs REST e infraestructura cloud-native en AWS 
con Docker y Kubernetes.

Integro IA en el ciclo de desarrollo: construyo con Claude Code, orquesto 
LLMs (LangChain, Ollama) y aplico fluidez en IA a lo largo del proceso. 
Ingles conversacional (B2+ profesional), trabajo en remoto desde 2022 con 
equipos de Espana, Chile y El Salvador, comodo con horario de Mexico.

Me interesa especialmente esta oportunidad por el sector HealthTech y la 
modalidad 100% remota.

Expectativa salarial: 2500 a 3000 USD mensuales netos, en modalidad 
contractor remota.

Adjuntos: CV y cover letter.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev | github.com/Marigiko
''',
        'cv': 'cv/main_healthtech_latam.pdf',
        'cl': 'cover_letters/cover_healthtech_latam.pdf',
    },
    {
        'to': 'talentoit@tecnosoftware.com',
        'subject': 'Postulacion: Desarrollador Frontend / DevOps SSR - Mario Aquino',
        'company': 'Tecnosoftware',
        'body': '''Estimado equipo de Tecnosoftware,

Mi nombre es Mario Aquino, soy desarrollador de software con mas de 5 anos 
de experiencia construyendo aplicaciones web escalables: React.js y Next.js 
en frontend, Node.js/NestJS en backend, APIs REST e infraestructura 
cloud-native en AWS con Docker y Kubernetes.

Integro IA en el desarrollo con Claude Code y automatizacion (n8n, LLMs). 
Experiencia en equipos agiles (Scrum/Kanban), pipelines CI/CD y colaboracion 
cross-funcional. Trabajo en remoto desde 2022 con equipos de Espana, Chile 
y El Salvador.

Me interesa especialmente Tecnosoftware por los proyectos desafiantes con 
clientes de primera linea y la cultura orientada a buenas practicas y 
crecimiento constante.

Expectativa salarial: 2500 a 3000 USD mensuales netos, en modalidad 
contractor remota.

Adjuntos: CV y cover letter.

Quedo a disposicion.

Saludos cordiales,
Mario Aquino
you@example.com | +00 0 000 000000
linkedin.com/in/keyzdev | github.com/Marigiko
''',
        'cv': 'cv/main_tecnosoftware.pdf',
        'cl': 'cover_letters/cover_tecnosoftware.pdf',
    },
]

sent = 0
for app in applications:
    try:
        msg = EmailMessage()
        msg['From'] = sender
        msg['To'] = app['to']
        msg['Subject'] = app['subject']
        msg.set_content(app['body'])

        for p in [app['cv'], app['cl']]:
            if Path(p).exists():
                data = Path(p).read_bytes()
                msg.add_attachment(data, maintype='application', subtype='pdf', filename=Path(p).name)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, password)
            s.send_message(msg)

        print(f"  ENVIADO: {app['company']} -> {app['to']}")
        sent += 1
        time.sleep(2)
    except Exception as e:
        print(f"  ERROR: {app['company']} -> {app['to']}: {e}")

print(f"\nTOTAL ENVIADOS: {sent}/{len(applications)}")
