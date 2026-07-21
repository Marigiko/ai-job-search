/**
 * Profile-based answer database for job application screening questions.
 * Answers are derived from the candidate profile and actual CV data.
 * For questions that don't match any known pattern, use the LLM fallback.
 */

const PROFILE = {
  name: 'Mario Aquino',
  legalName: 'Sergio Mario Oscar Aquino',
  email: 'marioaquinojob@gmail.com',
  phone: '+54 9 362 5455786',
  location: 'Resistencia, Chaco, Argentina',
  linkedin: 'https://linkedin.com/in/keyzdev',
  github: 'https://github.com/Marigiko',
  portfolio: 'https://keyz.freedev.app',
  languages: 'Español nativo, Inglés B2+ (Intermedio Avanzado), Portugués B2',
  education: 'Ingeniería en Sistemas de Información (UTN, en curso), Licenciatura en Ciberseguridad (UNDEF, en curso), Técnico Electromecánico',

  currentRole: 'Scraper Developer (part-time)',
  currentCompany: 'Magnar (Chile, remoto)',
  currentStart: 'Julio 2026',
  currentDescription: 'Desarrollo de scrapers para documentos legales públicos (regulaciones, legislación, jurisprudencia) para plataforma legal-AI',

  experience: [
    { role: 'Senior Full-Stack Engineer', company: 'SalesMatch.Ai', location: 'España (remoto)', period: 'Feb 2024 - Ene 2026', description: 'Backend Node.js/TS/NestJS, CI/CD (-50% deploy time), Python+n8n automation, AWS/Docker/K8s' },
    { role: 'Full-Stack Developer', company: 'Syloper', location: 'Santa Fe, Argentina', period: 'Dic 2023 - Mar 2024', description: 'React/Next.js/Node, -45% API latency (PostgreSQL/Redis), MVPs en <72h' },
    { role: 'Software Engineer', company: 'FlamaTech', location: 'España (remoto)', period: 'Mar 2023 - Feb 2024', description: 'REST APIs, Clean Architecture (SOLID/DDD), -50% tech debt, Jest +30% stability' },
    { role: 'Programming Coach & Mentor', company: 'Kodigo', location: 'El Salvador (remoto)', period: 'May 2022 - May 2023', description: 'Enseñé a 150+ estudiantes, 92% satisfacción' },
    { role: 'Frontend Intern', company: 'AirBits', location: 'Argentina', period: 'Oct 2021 - Feb 2022', description: 'UI/UX -25% friction, A11y +30 Lighthouse pts' },
  ],

  totalYearsExperience: 5,
  skills: {
    primary: ['Node.js', 'NestJS', 'TypeScript', 'Python (FastAPI/Django)', 'REST', 'GraphQL'],
    secondary: ['React.js', 'Next.js', 'React Native', 'PHP', 'Java', 'Go (básico)'],
    devops: ['AWS (EC2/S3/Lambda/RDS/EKS)', 'Docker', 'Kubernetes', 'Helm', 'Terraform', 'GitHub Actions'],
    databases: ['PostgreSQL', 'MongoDB', 'Redis'],
    testing: ['Jest', 'Cypress'],
    other: ['Web Scraping (Selenium/Puppeteer)', 'LLMs (Ollama, LangChain)', 'n8n', 'Multi-agent systems', 'MQTT', 'Kafka', 'RabbitMQ'],
  },

  education: [
    { title: 'Ingeniería en Sistemas de Información', institution: 'Universidad Tecnológica Nacional (UTN)', status: 'En curso' },
    { title: 'Licenciatura en Ciberseguridad', institution: 'Universidad Nacional de la Defensa (UNDEF)', status: 'En curso' },
    { title: 'Técnico Electromecánico', institution: 'Escuela Técnica', status: 'Completado' },
  ],

  certifications: [
    'Scrum Developer Professional (SDPC) - SCRUMstudy',
    'Scrum Fundamentals (SFPC) - SCRUMstudy',
    'Python Essentials - Cisco/NDG',
    'Argentina Programa 2022',
  ],

  availability: 'Inmediata',
  salaryTarget: '3000 USD/mes',
  salaryMin: '2000 USD/mes',
  workMode: 'Remoto (abierto a reubicación)',
  relocation: 'Sí, abierto a reubicación. Necesito visa/sponsorship',
};

/**
 * Convert profile experience to a flat list of company names for matching
 */
function getCompanyNames() {
  const names = ['Magnar', 'SalesMatch.Ai', 'Syloper', 'FlamaTech', 'Kodigo', 'AirBits'];
  return [...new Set(names)];
}

/**
 * Convert profile experience to a single string for textarea questions
 */
function getExperienceSummary() {
  return PROFILE.experience.map(e => `${e.role} en ${e.company} (${e.period})`).join('. ');
}

/**
 * Match a question text to an answer based on keywords and context
 */
function matchAnswer(questionText, fieldType, options) {
  const q = questionText.toLowerCase();
  const wt = [questionText, fieldType, ...(options || [])].join(' ').toLowerCase();

  // === Personal info ===
  if (matchAny(wt, ['nombre', 'name', 'first name', 'last name', 'apellido', 'full name'])) {
    return { value: matchAny(q, ['apellido']) ? PROFILE.legalName.split(' ').slice(2).join(' ') : PROFILE.name, source: 'profile' };
  }
  if (matchAny(wt, ['email', 'correo', 'e-mail'])) return { value: PROFILE.email, source: 'profile' };
  if (matchAny(wt, ['teléfono', 'phone', 'celular', 'mobile', 'telefono', 'whatsapp'])) return { value: PROFILE.phone, source: 'profile' };
  if (matchAny(wt, ['linkedin'])) return { value: PROFILE.linkedin, source: 'profile' };
  if (matchAny(wt, ['github', 'git hub'])) return { value: PROFILE.github, source: 'profile' };
  if (matchAny(wt, ['portfolio', 'portafolio', 'sitio web', 'website', 'web site'])) return { value: PROFILE.portfolio, source: 'profile' };
  if (matchAny(wt, ['dirección', 'address', 'ubicación', 'location', 'residencia', 'dónde vives', 'donde vives', 'ciudad', 'city'])) return { value: PROFILE.location, source: 'profile' };

  // === Work experience ===
  if (matchAny(wt, ['empresa actual', 'current company', 'donde trabajas', 'empresa en la que trabajas'])) return { value: PROFILE.currentCompany, source: 'profile' };
  if (matchAny(wt, ['empresas anteriores', 'previous companies', 'donde trabajaste', 'experiencia laboral', 'work experience', 'trabajos anteriores'])) {
    return { value: getCompanyNames().join(', '), source: 'profile' };
  }
  if (matchAny(wt, ['última empresa', 'last company', 'empresa más reciente', 'most recent company'])) return { value: 'SalesMatch.Ai', source: 'profile' };
  if (matchAny(wt, ['qué empresa', 'que empresa', 'nombre de la empresa', 'company name', 'nombre empresa'])) {
    // Try to match specific company name in question
    for (const c of getCompanyNames()) {
      if (q.includes(c.toLowerCase())) return { value: c, source: 'profile' };
    }
    return { value: 'SalesMatch.Ai', source: 'profile' };
  }
  if (matchAny(wt, ['rol', 'role', 'puesto', 'position', 'cargo', 'title', 'job title', 'último cargo', 'último puesto'])) {
    return { value: 'Senior Full-Stack Engineer', source: 'profile' };
  }
  if (matchAny(wt, ['años de experiencia', 'years of experience', 'experiencia', 'experience años', 'experience years'])) {
    return { value: `${PROFILE.totalYearsExperience}+ años`, source: 'profile' };
  }
  if (matchAny(wt, ['fecha de inicio', 'start date', 'fecha ingreso', 'desde cuándo', 'desde cuando'])) return { value: 'Disponible inmediatamente', source: 'profile' };
  if (matchAny(wt, ['motivo de salida', 'razón de salida', 'reason for leaving', 'why did you leave'])) return { value: 'Búsqueda de nuevos desafíos y crecimiento profesional', source: 'profile' };
  if (matchAny(wt, ['disponibilidad', 'availability', 'cuando puedes', 'cuando puedes empezar', 'cuándo puedes empezar', 'start date', 'fecha de inicio'])) return { value: PROFILE.availability, source: 'profile' };

  // === Skills ===
  if (matchAny(wt, ['tecnologías', 'technologies', 'tech stack', 'stack tecnológico', 'herramientas', 'tools'])) {
    return { value: PROFILE.skills.primary.join(', '), source: 'profile' };
  }
  if (matchAny(wt, ['node', 'node.js', 'nodejs', 'nestjs', 'nest js'])) return { value: 'Node.js / NestJS — 5+ años', source: 'profile' };
  if (matchAny(wt, ['python', 'fastapi', 'django'])) return { value: 'Python (FastAPI, Django) — 3+ años', source: 'profile' };
  if (matchAny(wt, ['react', 'next.js', 'nextjs', 'frontend', 'front-end'])) return { value: 'React / Next.js — 3+ años', source: 'profile' };
  if (matchAny(wt, ['typescript', 'type script', 'ts'])) return { value: 'TypeScript — 5+ años', source: 'profile' };
  if (matchAny(wt, ['aws', 'amazon web', 'cloud', 'nube'])) return { value: 'AWS (EC2, S3, Lambda, RDS, EKS) — 3+ años', source: 'profile' };
  if (matchAny(wt, ['docker', 'kubernetes', 'k8s', 'contenedores', 'containers'])) return { value: 'Docker, Kubernetes — 3+ años', source: 'profile' };
  if (matchAny(wt, ['sql', 'postgresql', 'postgres', 'base de datos', 'database', 'mysql'])) return { value: 'PostgreSQL, MongoDB, Redis', source: 'profile' };
  if (matchAny(wt, ['testing', 'jest', 'cypress', 'pruebas'])) return { value: 'Jest, Cypress', source: 'profile' };
  if (matchAny(wt, ['scraping', 'scraper', 'web scraping', 'selenium', 'puppeteer'])) return { value: 'Web Scraping (Selenium, Puppeteer) — 2+ años', source: 'profile' };
  if (matchAny(wt, ['llm', 'langchain', 'ollama', 'ai', 'inteligencia artificial', 'ia', 'agentes', 'agents', 'n8n'])) {
    return { value: 'LLMs (Ollama, LangChain), n8n, multi-agent systems', source: 'profile' };
  }

  // === Languages ===
  if (matchAny(wt, ['inglés', 'english', 'idioma', 'language', 'nivel de inglés', 'nivel de ingles'])) return { value: 'B2+ (Intermedio Avanzado)', source: 'profile' };
  if (matchAny(wt, ['portugués', 'portuguese', 'portugues'])) return { value: 'B2', source: 'profile' };
  if (matchAny(wt, ['español', 'spanish', 'castellano'])) return { value: 'Nativo', source: 'profile' };

  // === Education ===
  if (matchAny(wt, ['educación', 'education', 'estudios', 'título', 'title', 'formación', 'formacion', 'nivel educativo'])) {
    return { value: 'Universitario (Ing. en Sistemas, en curso)', source: 'profile' };
  }
  if (matchAny(wt, ['universidad', 'university', 'utn', 'undef', 'institución educativa', 'institution'])) return { value: 'UTN (Universidad Tecnológica Nacional)', source: 'profile' };
  if (matchAny(wt, ['carrera', 'degree', 'major'])) return { value: 'Ingeniería en Sistemas de Información', source: 'profile' };

  // === Salary ===
  if (matchAny(wt, ['salario', 'salary', 'pretensión', 'pretension', 'remuneración', 'remuneracion', 'sueldo', 'expectativa salarial', 'salary expectation'])) {
    return { value: PROFILE.salaryTarget, source: 'profile' };
  }
  if (matchAny(wt, ['moneda', 'currency', 'tipo de cambio'])) return { value: 'USD', source: 'profile' };

  // === Work mode ===
  if (matchAny(wt, ['remoto', 'remote', 'presencial', 'híbrido', 'hibrido', 'modalidad', 'work mode', 'work model'])) return { value: 'Remoto', source: 'profile' };
  if (matchAny(wt, ['reubicación', 'relocation', 'visa', 'sponsor', 'mudanza', 'reasignación'])) return { value: PROFILE.relocation, source: 'profile' };
  if (matchAny(wt, ['jornada', 'tiempo completo', 'part-time', 'full-time', 'media jornada', 'tipo de contrato', 'contrato'])) return { value: 'Full-time o Part-time', source: 'profile' };

  // === Generic question patterns ===
  if (matchAny(wt, ['interés', 'interes', 'motivación', 'motivation', 'why do you want', 'por qué quieres', 'porque quieres', 'interesado'])) {
    return { value: 'Me motiva la oportunidad de aplicar mi experiencia en arquitectura cloud-native y automatización con IA para resolver problemas reales', source: 'profile' };
  }
  if (matchAny(wt, ['fortalezas', 'strengths', 'habilidades', 'skills', 'competencias', 'compentencias', 'cualidades'])) {
    return { value: 'Arquitectura limpia, automatización, entrega rápida, mentoring, pensamiento estratégico', source: 'profile' };
  }
  if (matchAny(wt, ['debilidades', 'weaknesses', 'áreas de mejora', 'areas de mejora', 'mejorar'])) return { value: 'A veces soy demasiado detallista en la planificación inicial', source: 'profile' };
  if (matchAny(wt, ['logro', 'achievement', 'mayor logro', 'éxito', 'exito', 'accomplish'])) {
    return { value: 'Reduje tiempo de deploy en 50% y errores de PR en 40% mediante CI/CD y mentoring en SalesMatch.Ai', source: 'profile' };
  }

  // === Yes/No questions (radio or select) ===
  if (matchAny(wt, ['cuenta con experiencia', 'cuentas con experiencia', 'tienes experiencia', 'tiene experiencia'])) return { value: 'Sí', source: 'profile' };
  if (matchAny(wt, ['disponibilidad para viajar', 'travel', 'viajar', 'viaje'])) return { value: 'Sí', source: 'profile' };
  if (matchAny(wt, ['disponibilidad para trabajar', 'available to work', 'disponible para'])) return { value: 'Sí, inmediata', source: 'profile' };
  if (matchAny(wt, ['mayor de edad', 'over 18', 'mayor edad', 'edad'])) return { value: 'Sí', source: 'profile' };
  if (matchAny(wt, ['autorización para trabajar', 'work authorization', 'derecho a trabajar', 'legal to work'])) return { value: 'Sí, en Argentina. Necesito visa para otros países', source: 'profile' };
  if (matchAny(wt, ['discapacidad', 'disability'])) return { value: 'No', source: 'profile' };

  // Unknown question — return null for LLM fallback
  return null;
}

function matchAny(text, keywords) {
  return keywords.some(kw => text.includes(kw));
}

export { PROFILE, matchAnswer, getCompanyNames, getExperienceSummary };
