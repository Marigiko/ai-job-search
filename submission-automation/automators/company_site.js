import BaseAutomator from './base.js';

export default class CompanySiteAutomator extends BaseAutomator {
  constructor(config) {
    super('company_site', config);
  }

  async submit(job) {
    try {
      await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    } catch (err) {
      throw new Error(`Cannot load page: ${err.message.slice(0, 100)}`);
    }
    await this.sleep(2000);
    const selectors = [
      'a:has-text("Apply")', 'a:has-text("apply")', 'a:has-text("Apply Now")',
      'a:has-text("Careers")', 'a:has-text("careers")', 'a:has-text("Join Us")',
      'a[href*="career"]', 'a[href*="job"]', 'a[href*="apply"]',
      'button:has-text("Apply")', 'button:has-text("apply")',
    ];
    for (const sel of selectors) {
      const btn = await this.page.$(sel);
      if (btn) {
        const href = await btn.getAttribute('href');
        if (href && href.startsWith('http')) {
          await this.page.goto(href, { waitUntil: 'domcontentloaded' });
          await this.sleep(2000);
        } else if (href && !href.startsWith('#')) {
          await btn.click();
          await this.sleep(2000);
        } else {
          await btn.click();
          await this.sleep(2000);
        }
        break;
      }
    }
    if (job.cvPath) {
      for (const sel of ['input[type="file"]', 'input[accept*="pdf"]', 'input[aria-label*="resume" i]', 'input[name*="resume"]', 'input[name*="cv"]']) {
        const input = await this.page.$(sel);
        if (input) { await input.setInputFiles(job.cvPath); break; }
      }
    }
    return { applied: true, method: 'company_site_apply' };
  }
}
