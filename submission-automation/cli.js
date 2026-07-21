#!/usr/bin/env node
import 'dotenv/config';
import { chromium } from 'playwright';
import { getPortalGroups, getTargetJobs } from './config/jobs.js';
import { AUTOMATORS, PORTAL_LABELS } from './automators/index.js';
import { auditComputrabajo, auditLinkedIn, generateReport } from './audit.js';

const PORTALS_WITH_AUTH = ['linkedin', 'computrabajo', 'getonbrd'];

async function main() {
  const args = process.argv.slice(2);
  const flags = {};
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--portal': flags.portal = args[++i]; break;
      case '--min-score': flags.minScore = parseInt(args[++i]) || 0; break;
      case '--max-score': flags.maxScore = parseInt(args[++i]) || 100; break;
      case '--dry-run': flags.dryRun = true; break;
      case '--headless': flags.headless = args[++i] !== 'false'; break;
      case '--slow-mo': flags.slowMo = parseInt(args[++i]) || 0; break;
      case '--timeout': flags.timeout = parseInt(args[++i]) || 30000; break;
      case '--audit': flags.audit = true; break;
      case '--audit-portal': flags.auditPortal = args[++i]; break;
      case '--help':
      case '-h':
        showHelp();
        process.exit(0);
    }
  }

  // Audit mode
  if (flags.audit) {
    await runAudit(flags);
    return;
  }

  const config = {
    headless: flags.headless !== false,
    slowMo: flags.slowMo || parseInt(process.env.SLOW_MO || '0'),
    timeout: flags.timeout || parseInt(process.env.TIMEOUT || '30000'),
  };

  const minScore = flags.minScore || 0;
  const maxScore = flags.maxScore || 100;

  if (flags.portal) {
    // Single portal
    if (!AUTOMATORS[flags.portal]) {
      console.error(`Unknown portal: ${flags.portal}`);
      console.error(`Available: ${Object.keys(AUTOMATORS).join(', ')}`);
      process.exit(1);
    }
    const jobs = getTargetJobs(minScore, maxScore, flags.portal);
    if (jobs.length === 0) {
      console.log(`No jobs for portal '${flags.portal}' in score range ${minScore}-${maxScore}`);
      process.exit(0);
    }
    console.log(`\n╔══════════════════════════════════════════════╗`);
    console.log(`║  ${PORTAL_LABELS[flags.portal] || flags.portal}`);
    console.log(`║  ${jobs.length} jobs to process`);
    console.log(`╚══════════════════════════════════════════════╝\n`);

    if (flags.dryRun) {
      for (const j of jobs) {
        console.log(`  [DRY] ${j.company} - ${j.title}`);
        console.log(`        URL: ${j.url}`);
        console.log(`        CV: ${j.cvFile || 'N/A'}`);
        console.log(`        Cover: ${j.coverFile || 'N/A'}`);
      }
      console.log(`\n  Dry run complete. ${jobs.length} jobs would be submitted.`);
      return;
    }

    const hasAuth = PORTALS_WITH_AUTH.includes(flags.portal) ? checkAuth(flags.portal) : true;
    if (PORTALS_WITH_AUTH.includes(flags.portal) && !hasAuth) {
      console.log(`  ℹ Skipping ${flags.portal} — manual submission required`);
      for (const j of jobs) {
        console.log(`      ${j.company} - ${j.title} → submit manually: ${j.url}`);
      }
      return;
    }
    const Automator = AUTOMATORS[flags.portal];
    const automator = new Automator(config);
    try {
      await automator.init();
      if (automator.login && PORTALS_WITH_AUTH.includes(flags.portal) && hasAuth) {
        await automator.login();
      }
      const results = await automator.runAll(jobs);
      const report = automator.generateReport();
      printReport(report);
    } finally {
      await automator.destroy();
    }
  } else {
    // All portals
    const groups = getPortalGroups(minScore);
    console.log(`\n╔══════════════════════════════════════════════╗`);
    console.log(`║  JOB SUBMISSION AUTOMATION`);
    console.log(`║  Score range: ${minScore} - ${maxScore}`);
    console.log(`╚══════════════════════════════════════════════╝\n`);

    const portalOrder = ['linkedin', 'getonbrd', 'computrabajo', 'weworkremotely', 'themuse', 'freehire', 'jobicy', 'remotive', 'ashby', 'freshteam', 'ats_generic', 'company_site', 'other'];

    if (flags.dryRun) {
      for (const portal of portalOrder) {
        const jobs = groups[portal] || [];
        if (jobs.length === 0) continue;
        console.log(`\n── ${PORTAL_LABELS[portal] || portal} (${jobs.length}) ──`);
        for (const j of jobs) {
          console.log(`  ${j.score}  ${j.company} - ${j.title}`);
          console.log(`      CV: ${j.cvFile || 'N/A'}`);
        }
      }
      const total = Object.values(groups).reduce((a, b) => a + b.length, 0);
      console.log(`\n  Dry run complete. ${total} jobs across ${Object.keys(groups).length} portals.`);
      return;
    }

    let allResults = [];
    let totalSubmitted = 0;
    let totalFailed = 0;
    let totalManual = 0;

    for (const portal of portalOrder) {
      const jobs = groups[portal] || [];
      if (jobs.length === 0) continue;
      console.log(`\n╔══════════════════════════════════════════════╗`);
      console.log(`║  ${PORTAL_LABELS[portal] || portal}`);
      console.log(`║  ${jobs.length} jobs`);
      console.log(`╚══════════════════════════════════════════════╝\n`);

      const hasAuth = PORTALS_WITH_AUTH.includes(portal) ? checkAuth(portal) : true;
      if (PORTALS_WITH_AUTH.includes(portal) && !hasAuth) {
        console.log(`  ℹ Skipping ${portal} — manual submission required`);
        for (const j of jobs) {
          allResults.push({ ...j, status: 'manual', method: 'manual_oauth' });
        }
        totalManual = (totalManual || 0) + jobs.length;
        continue;
      }

      const Automator = AUTOMATORS[portal];
      const automator = new Automator(config);
      try {
        await automator.init();
        if (automator.login && PORTALS_WITH_AUTH.includes(portal) && hasAuth) {
          await automator.login();
        }
        const results = await automator.runAll(jobs);
        allResults.push(...results);
        const report = automator.generateReport();
        totalSubmitted += report.submitted;
        totalFailed += report.failed;
        printReport(report);
      } catch (err) {
        console.error(`  ✗ Portal error: ${err.message}`);
      } finally {
        await automator.destroy();
      }

      await new Promise(r => setTimeout(r, 5000));
    }

    console.log(`\n${'='.repeat(50)}`);
    console.log(`  ALL PORTALS COMPLETE`);
    console.log(`  Submitted: ${totalSubmitted} | Failed: ${totalFailed} | Manual: ${totalManual}`);
    console.log(`${'='.repeat(50)}\n`);

    // Write detailed results
    const dt = new Date().toISOString().replace(/[:.]/g, '-');
    const reportPath = `submission_report_${dt}.json`;
    const fs = await import('fs');
    fs.writeFileSync(reportPath, JSON.stringify(allResults, null, 2));
    console.log(`Report saved: ${reportPath}`);
  }
}

async function runAudit(flags) {
  const portal = flags.auditPortal || 'all';

  // First generate the report from tracker data
  generateReport();

  // Then open browser for visual inspection
  const browser = await chromium.launch({
    headless: false,
    args: ['--disable-blink-features=AutomationControlled'],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();
  page.setDefaultTimeout(60000);

  try {
    if (portal === 'all' || portal === 'computrabajo') {
      await auditComputrabajo(page);
    }
    if (portal === 'all' || portal === 'linkedin') {
      await auditLinkedIn(page);
    }
  } finally {
    console.log('\nAudit complete. Press Enter to close browser...');
    await new Promise(resolve => process.stdin.once('data', () => resolve()));
    await browser.close();
  }
}

function checkAuth(portal) {
  const envKey = `${portal.toUpperCase()}_EMAIL`.replace('GETONBRD', 'GETONBRD');
  const pwKey = `${portal.toUpperCase()}_PASSWORD`.replace('GETONBRD', 'GETONBRD');
  const email = process.env[envKey];
  const password = process.env[pwKey];
  // GetOnBoard uses Google OAuth — passwords not required
  if (portal === 'getonbrd' && !password) {
    console.log(`  ℹ GetOnBoard uses Google OAuth — submitting manually`);
    return false;
  }
  if (!email || !password) {
    console.error(`  ⚠ ${portal} credentials not set in .env (${envKey} / ${pwKey})`);
    console.error(`  ⚠ Create a .env file from .env.example`);
    process.exit(1);
  }
  return true;
}

function printReport(report) {
  console.log(`\n  Results:`);
  console.log(`  ├── Submitted: ${report.submitted}`);
  console.log(`  └── Failed:    ${report.failed}`);
  if (report.failed > 0) {
    for (const r of report.results.filter(r => r.status === 'failed')) {
      console.log(`      ✗ ${r.company}: ${r.error?.slice(0, 100)}`);
    }
  }
}

function showHelp() {
  console.log(`
  Job Submission Automation — CLI

  USAGE:
    node cli.js [options]

  OPTIONS:
    --portal <name>    Run only one portal (linkedin, getonbrd, computrabajo, ...)
    --min-score <n>    Minimum fit score (default: 0)
    --max-score <n>    Maximum fit score (default: 100)
    --dry-run          Show jobs without submitting
    --headless <bool>  Browser headless mode (default: true)
    --slow-mo <ms>     Slow down browser by ms
    --timeout <ms>     Page timeout in ms
    --audit            Audit submitted applications across portals
    --audit-portal <p> Audit a specific portal (computrabajo, linkedin)

  EXAMPLES:
    node cli.js --dry-run
    node cli.js --portal linkedin
    node cli.js --audit
    node cli.js --audit --audit-portal computrabajo
    node cli.js --headless false --slow-mo 500
  `);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
