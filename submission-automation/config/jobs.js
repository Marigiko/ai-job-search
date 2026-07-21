import { readFileSync, readdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PROJ = path.resolve(ROOT, '..');
const CV_DIR = path.join(PROJ, 'cv');
const COVER_DIR = path.join(PROJ, 'cover_letters');
const TMP_DIR = '/tmp';

const PORTAL_MAP = {
  'linkedin.com': 'linkedin',
  'getonbrd.com': 'getonbrd',
  'freehire.dev': 'freehire',
  'arbeitnow': 'arbeitnow',
  'remoteok': 'remoteok',
  'remotive': 'remotive',
  'jobicy': 'jobicy',
  'weworkremotely': 'weworkremotely',
  'themuse': 'themuse',
  'computrabajo': 'computrabajo',
  'landing.jobs': 'landingjobs',
};

function detectPortal(url) {
  if (!url) return 'other';
  for (const [pattern, portal] of Object.entries(PORTAL_MAP)) {
    if (url.includes(pattern)) return portal;
  }
  if (url.includes('greenhouse.io') || url.includes('lever.co') || url.includes('ashbyhq.com')
    || url.includes('freshteam.com') || url.includes('breezy.hr') || url.includes('workable.com')
    || url.includes('smartrecruiters') || url.includes('icims')
    || url.includes('myworkdayjobs') || url.includes('successfactors')) return 'ats_generic';
  if (url.includes('hh.ru') || url.includes('djinni.co') || url.includes('getmatch.ru')
    || url.includes('justjoin.it')) return 'other';
  return 'company_site';
}

function normalize(s) {
  return (s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function findFiles(company, title) {
  const raw = normalize(company);
  const t = normalize(title);

  const cvs = readdirSync(CV_DIR).filter(f => f.startsWith('main_') && f.endsWith('.pdf'));
  const covers = new Set(readdirSync(COVER_DIR).filter(f => f.startsWith('cover_') && f.endsWith('.pdf')));

  // Extract the first meaningful word from company name
  const firstWord = raw.replace(/(recursoshumanos|informatica|s\.?a\.?|ltda?|inc|ltd|gmbh|corp|llc)/g, '').trim();
  const nameParts = [raw, firstWord, raw.slice(0, 10), firstWord.slice(0, 8)];
  // Also try removing common suffixes
  for (const p of [...nameParts]) {
    if (p.endsWith('sa')) nameParts.push(p.slice(0, -2));
    if (p.endsWith('srl')) nameParts.push(p.slice(0, -3));
  }

  // Score each CV by longest common substring with company name
  let bestMatch = null;
  let bestScore = 0;

  for (const f of cvs) {
    const base = f.replace('main_', '').replace('.pdf', '').toLowerCase();
    let score = 0;

    // Check if any company name part is in the filename
    for (const part of [...new Set(nameParts)]) {
      if (!part) continue;
      if (base.includes(part)) { score = Math.max(score, part.length * 2); }
      if (part.includes(base)) { score = Math.max(score, base.length); }
    }

    // Title match bonus
    if (t && base.includes(t.slice(0, 8))) score += 5;
    if (t && t.includes(base.slice(-10))) score += 3;

    if (score > bestScore) {
      bestScore = score;
      bestMatch = f;
    }
  }

  if (bestMatch) {
    const cvFile = `cv/${bestMatch}`;
    const coverName = bestMatch.replace('main_', 'cover_');
    return {
      cvFile,
      coverFile: covers.has(coverName) ? `cover_letters/${coverName}` : null,
      cvPath: path.join(CV_DIR, bestMatch),
      coverPath: covers.has(coverName) ? path.join(COVER_DIR, coverName) : null,
    };
  }

  return { cvFile: null, coverFile: null, cvPath: null, coverPath: null };
}

export function getTargetJobs(minScore = 0, maxScore = 100, portalFilter = null) {
  const shortlistedPath = path.join(TMP_DIR, 'shortlisted_120.json');
  let shortlisted;
  try { shortlisted = JSON.parse(readFileSync(shortlistedPath, 'utf-8')); } catch { shortlisted = []; }

  const results = [];
  const seenKeys = new Set();

  for (const j of shortlisted) {
    const key = j.key;
    if (seenKeys.has(key)) continue;
    seenKeys.add(key);
    const score = j.score;
    if (score < minScore || score > maxScore) continue;

    const url = j.url || '';
    const portal = detectPortal(url);
    if (portalFilter && portal !== portalFilter) continue;

    const company = (j.company || '').trim();
    const title = (j.title || '').trim();

    const { cvFile, coverFile, cvPath, coverPath } = findFiles(company, title);

    results.push({
      key, score, company, title, url, portal,
      cvFile, coverFile, cvPath, coverPath,
    });
  }
  return results;
}

export function getPortalGroups(minScore = 0) {
  const jobs = getTargetJobs(minScore);
  const groups = {};
  for (const j of jobs) {
    if (!groups[j.portal]) groups[j.portal] = [];
    groups[j.portal].push(j);
  }
  return groups;
}
