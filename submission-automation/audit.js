#!/usr/bin/env node
import 'dotenv/config';
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const TRACKER_PATH = path.resolve(import.meta.dirname, '..', 'job_search_tracker.csv');

function readTracker() {
  if (!fs.existsSync(TRACKER_PATH)) {
    return { total: 0, applied: [], identified: [], pending: [] };
  }
  const data = fs.readFileSync(TRACKER_PATH, 'utf-8').trim().split('\n');
  const headers = data[0].split(',');
  const rows = data.slice(1).map(line => {
    const vals = line.split(',');
    const row = {};
    headers.forEach((h, i) => row[h.trim()] = (vals[i] || '').trim());
    return row;
  });

  return {
    total: rows.length,
    applied: rows.filter(r => r.status === 'applied'),
    identified: rows.filter(r => r.status === 'identified'),
    drafted: rows.filter(r => r.status === 'drafted'),
    pending: rows.filter(r => r.status === 'pending_user_action'),
  };
}

export async function auditComputrabajo(page) {
  console.log('\n=== Audit: Computrabajo ===');
  const tracker = readTracker();
  const ctApps = tracker.applied.filter(r => r.channel === 'computrabajo');

  console.log(`  ${ctApps.length} applications tracked as "applied":`);
  for (const app of ctApps) {
    console.log(`    • ${app.company.substring(0, 30)} | ${app.role.substring(0, 50)} | Score: ${app.fit_rating}`);
  }

  if (ctApps.length === 0) {
    console.log('  (no Computrabajo applications in tracker)');
  }

  console.log(`\n  Opening browser for visual inspection of "Mis postulaciones"...`);
  console.log('  ⏳ Please log in if prompted (up to 180s)...');

  await page.goto('https://ar.computrabajo.com/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 3000));

  // Check login & wait if needed
  for (let i = 0; i < 60; i++) {
    const body = await page.evaluate(() => document.body.textContent || '');
    if (body.includes('Cerrar sesión') || body.includes('Notificaciones')) break;
    await new Promise(r => setTimeout(r, 3000));
  }

  const loggedIn = await page.evaluate(() => (document.body.textContent || '').includes('Cerrar sesión'));
  console.log(`  Logged in: ${loggedIn}`);

  if (loggedIn) {
    await page.goto('https://candidato.ar.computrabajo.com/', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 5000));
    const url = page.url();
    console.log(`  Candidate URL: ${url}`);
  }
}

export async function auditLinkedIn(page) {
  console.log('\n=== Audit: LinkedIn ===');
  const tracker = readTracker();
  const liApps = tracker.applied.filter(r => r.channel === 'linkedin');

  console.log(`  ${liApps.length} applications tracked as "applied":`);
  for (const app of liApps) {
    console.log(`    • ${app.company.substring(0, 30)} | ${app.role.substring(0, 50)}`);
  }

  if (liApps.length === 0) {
    console.log('  (no LinkedIn applications in tracker)');
  }

  console.log(`\n  Opening "My Jobs → Applied" for review...`);
  console.log('  ⏳ Please log in if prompted (up to 180s)...');

  await page.goto('https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 5000));

  const title = await page.title();
  const url = page.url();
  console.log(`  URL: ${url}`);
  console.log(`  Title: ${title}`);
}

export function generateReport() {
  const tracker = readTracker();

  console.log('\n═══════════════════════════════════════════');
  console.log('  APPLICATION AUDIT REPORT');
  console.log('═══════════════════════════════════════════\n');

  console.log(`  Total in tracker: ${tracker.total}`);
  console.log(`  Applied:          ${tracker.applied.length}`);
  console.log(`  Identified:       ${tracker.identified.length}`);
  console.log(`  Drafted:          ${tracker.drafted.length}`);
  console.log(`  Pending action:   ${tracker.pending.length}\n`);

  if (tracker.applied.length > 0) {
    console.log('  ── APPLIED ──');
    for (const app of tracker.applied) {
      const channel = app.channel || '?';
      const company = (app.company || '?').substring(0, 25);
      const role = (app.role || '?').substring(0, 40);
      const score = app.fit_rating || '?';
      console.log(`    [${channel}] ${company} | ${role} (fit: ${score})`);
    }
    console.log();
  }

  if (tracker.pending.length > 0) {
    console.log('  ── NEEDS ACTION ──');
    for (const app of tracker.pending) {
      const channel = app.channel || '?';
      const company = (app.company || '?').substring(0, 25);
      const role = (app.role || '?').substring(0, 40);
      console.log(`    [${channel}] ${company} | ${role}`);
    }
    console.log();
  }

  return tracker;
}
