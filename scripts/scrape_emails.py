#!/usr/bin/env python3
"""Scrapea APIs públicas y extrae ofertas con email (regex relajado)."""
import urllib.request, urllib.parse, json, re, sys, time, html

from env_loader import load_env
load_env()

HEADERS = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == retries-1: return None
            time.sleep(1)

def fetch_text(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode()
        except Exception as e:
            if i == retries-1: return None
            time.sleep(1)

# Relaxed email regex - any valid email in description
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
GENERIC = {'linkedin','example','yourname','gmail.com','yahoo.com','email.com','domain.com','company.com','mine.com','sentry','visualstudio','mozilla','chromium','google.com','microsoft.com','apple.com','amazon.com','facebook.com','twitter.com','weworkremotely.com','remoteok.com','jobicy.com','arbeitnow.com','landingjobs.co','stackoverflow.com','github.com','angel.co','wellfound.com','greenhouse.io','lever.co','workday.com','myworkdayjobs.com','smartrecruiters.com','icims.com','taleo.net','workable.com','ashbyhq.com','recruitee.com','personio.de','bamboohr.com','workable.com','zoho.com','breezy.hr','teamtailor.com','hireology.com','jobvite.com','phenom.com','eightfold.ai','beamery.com','icims.com','cornerstonondemand.com','jibe.com','yello.com','handshake.com','symplicity.com','graduway.com','peopleadmin.com','neogov.com','governmentjobs.com','governmentjobs.com','usajobs.gov','federalgovernmentjobs.us','federalgovernmentjobs.us'}
DEV_KW = ['developer','engineer','dev','software','full stack','backend','frontend','python','node','react','web developer','sre','architect','automation','qa','data scientist','ml engineer','machine learning','ai engineer','devops','cloud','programmer','coder','technical lead','tech lead','scrum master','product manager','engineering manager']
FOUNDER_KW = ['founding','co-founder','cofounder','first engineer','early employee','founding engineer','technical founder','founder','staff engineer','principal engineer']
US_TLDS = {'.us', '.com', '.io', '.ai', '.co', '.dev', '.app', '.tech', '.nyc', '.sf'}
US_LOCATIONS = {'usa', 'united states', 'us', 'remote', 'san francisco', 'new york', 'seattle', 'austin', 'boston', 'chicago', 'los angeles', 'denver', 'miami', 'portland', 'san diego', 'dc', 'washington', 'atlanta', 'detroit', 'minneapolis', 'phoenix', 'dallas', 'houston', 'remote/us', 'remote usa'}

def extract_emails(desc):
    if not desc: return []
    desc = html.unescape(re.sub(r'<[^>]+>', ' ', desc))
    emails = EMAIL_RE.findall(desc)
    valid = []
    for e in emails:
        e = e.lower().strip().rstrip('.')
        if any(g in e for g in GENERIC): continue
        if '.' not in e.split('@')[-1]: continue
        if len(e.split('@')[-1]) < 3: continue
        if e.count('@') != 1: continue
        if e.startswith('-') or e.startswith('.'): continue
        valid.append(e)
    return list(set(valid))

def is_dev(role):
    rl = role.lower()
    return any(k in rl for k in DEV_KW)

jobs = []

# 1. RemoteOK API
print("1. RemoteOK...", flush=True)
data = fetch("https://remoteok.com/api")
if data and isinstance(data, list):
    for row in data[1:] if len(data)>1 else []:
        if not isinstance(row, dict) or not row.get('position'): continue
        desc = row.get('description','')
        emails = extract_emails(desc)
        if emails and is_dev(row['position']):
            jobs.append({'company': row.get('company',''), 'role': row['position'],
                'salary': f"${row.get('salary_min',0)//1000}-${row.get('salary_max',0)//1000}k/yr" if row.get('salary_max') else None,
                'emails': emails, 'url': row.get('url',''), 'source': 'remoteok', 'location': row.get('location','remote')})

# 2. Jobicy API
print("2. Jobicy...", flush=True)
data = fetch("https://jobicy.com/api/v2/remote-jobs?count=100&tag=developer")
if data and isinstance(data, dict):
    for j in data.get('jobs',[]):
        desc = j.get('description','') or ''
        emails = extract_emails(desc)
        if emails and is_dev(j.get('title','')):
            jobs.append({'company': j.get('company_name',''), 'role': j.get('title',''),
                'salary': None, 'emails': emails, 'url': j.get('url',''), 'source': 'jobicy', 'location': 'remote'})

# 3. Landing.jobs API
print("3. Landing.jobs...", flush=True)
data = fetch("https://landing.jobs/api/v1/jobs?limit=100&offset=0")
if data and isinstance(data, dict):
    for j in data.get('jobs',[]) or data.get('results',[]):
        desc = j.get('description','') or ''
        emails = extract_emails(desc)
        if emails and is_dev(j.get('title','')):
            co = (j.get('company') or {}).get('name','') if isinstance(j.get('company'),dict) else j.get('company_name','')
            jobs.append({'company': co, 'role': j.get('title',''),
                'salary': None, 'emails': emails, 'url': j.get('url','') or j.get('apply_url',''), 'source': 'landingjobs', 'location': 'remote/eu'})

# 4. Arbeitnow API
print("4. Arbeitnow...", flush=True)
data = fetch("https://arbeitnow.com/api/jobs?visa=true&category=engineering&page=1")
if data and isinstance(data, list):
    for j in data:
        desc = j.get('description','') or ''
        emails = extract_emails(desc)
        if emails and is_dev(j.get('title','')):
            jobs.append({'company': j.get('company',''), 'role': j.get('title',''),
                'salary': None, 'emails': emails, 'url': j.get('url',''), 'source': 'arbeitnow', 'location': 'remote/eu'})

# 5. WeWorkRemotely RSS
print("5. WeWorkRemotely...", flush=True)
try:
    xml = fetch_text("https://weworkremotely.com/remote-jobs.rss")
    if xml:
        for m in re.finditer(r'<item>(.*?)</item>', xml, re.S):
            item = m.group(1)
            title = re.search(r'<title>(.*?)</title>', item, re.S)
            desc = re.search(r'<description>(.*?)</description>', item, re.S)
            link = re.search(r'<link>(.*?)</link>', item, re.S)
            if title and desc:
                t = html.unescape(title.group(1).strip())
                d = html.unescape(desc.group(1).strip())
                emails = extract_emails(d)
                if emails and is_dev(t):
                    jobs.append({'company': t.split(':')[0] if ':' in t else 'unknown',
                        'role': t.split(':')[-1] if ':' in t else t,
                        'salary': None, 'emails': emails, 'url': link.group(1).strip() if link else '',
                        'source': 'weworkremotely', 'location': 'remote'})
except Exception as e:
    print(f"  WWR failed: {e}", flush=True)

# 6. GitHub Jobs (deprecated but try)
print("6. GitHub Jobs...", flush=True)
try:
    xml = fetch_text("https://jobs.github.com/positions.atom?description=developer&location=remote")
    if xml:
        for m in re.finditer(r'<entry>(.*?)</entry>', xml, re.S):
            entry = m.group(1)
            title = re.search(r'<title>(.*?)</title>', entry, re.S)
            content = re.search(r'<content[^>]*>(.*?)</content>', entry, re.S)
            link = re.search(r'<link[^>]*href="([^"]+)"', entry, re.S)
            if title and content:
                t = html.unescape(title.group(1).strip())
                d = html.unescape(content.group(1).strip())
                emails = extract_emails(d)
                if emails and is_dev(t):
                    jobs.append({'company': 'via GitHub', 'role': t,
                        'salary': None, 'emails': emails, 'url': link.group(1) if link else '',
                        'source': 'github', 'location': 'remote'})
except Exception as e:
    print(f"  GitHub failed: {e}", flush=True)

# 7. StackOverflow Jobs RSS
print("7. StackOverflow...", flush=True)
try:
    xml = fetch_text("https://stackoverflow.com/jobs/feed?r=true&tl=developer+engineer+python+node+react")
    if xml:
        for m in re.finditer(r'<item>(.*?)</item>', xml, re.S):
            item = m.group(1)
            title = re.search(r'<title>(.*?)</title>', item, re.S)
            desc = re.search(r'<description>(.*?)</description>', item, re.S)
            if title and desc:
                t = html.unescape(title.group(1).strip())
                d = html.unescape(desc.group(1).strip())
                emails = extract_emails(d)
                if emails and is_dev(t):
                    jobs.append({'company': 'via StackOverflow', 'role': t,
                        'salary': None, 'emails': emails, 'url': '', 'source': 'stackoverflow', 'location': 'remote'})
except Exception as e:
    print(f"  SO failed: {e}", flush=True)

# Dedup by company+role
seen = set()
unique = []
for j in jobs:
    key = (j['company'].lower().strip(), j['role'].lower().strip())
    if key not in seen and j['company'] and j['role']:
        seen.add(key)
        unique.append(j)

# --- US + Startup filtering ---
def is_founder_role(role):
    rl = role.lower()
    return any(k in rl for k in FOUNDER_KW)

def is_us_startup(job):
    """Heuristic: US startup if location is US or remote, and company looks like a startup."""
    loc = job.get('location', '').lower()
    if any(us_loc in loc for us_loc in US_LOCATIONS):
        return True
    # If salary is in USD or equity mentioned, likely US
    salary = str(job.get('salary', '') or '')
    if 'usd' in salary or '$' in salary:
        return True
    return False

# Tag founder roles and US startups
for j in unique:
    j['is_founder_role'] = is_founder_role(j['role'])
    j['is_us_startup'] = is_us_startup(j)

# Prioritize: US startups with founder roles first
unique.sort(key=lambda j: (j.get('is_us_startup', False), j.get('is_founder_role', False)), reverse=True)

with open('/tmp/jobs_scraped.json','w') as f:
    json.dump(unique, f, indent=2, ensure_ascii=False)

print(f"\nTOTAL con email + dev: {len(unique)}")
us_count = sum(1 for j in unique if j.get('is_us_startup'))
founder_count = sum(1 for j in unique if j.get('is_founder_role'))
print(f"  US startups: {us_count} | Founder roles: {founder_count}")
print(f"\n--- TOP LEADS (US startup + founder role) ---")
for j in unique[:30]:
    if j.get('is_us_startup'):
        tag = " [FOUNDER]" if j.get('is_founder_role') else ""
        print(f"  [{j['source']}] {j['company'][:30]:<30} | {j['role'][:40]:<40} | {j['emails'][0]}{tag}")
