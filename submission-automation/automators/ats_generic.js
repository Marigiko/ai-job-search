import BaseAutomator from './base.js';

export default class ATSGenericAutomator extends BaseAutomator {
  constructor(config) {
    super('ats_generic', config);
  }

  async submit(job) {
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);
    const applyBtn = await this.page.$('a:has-text("Apply"), a:has-text("apply"), button:has-text("Apply"), a:has-text("Apply Now"), a[class*="apply"], button[class*="apply"]');
    if (!applyBtn) throw new Error('Apply button not found on ATS page');
    const href = await applyBtn.getAttribute('href');
    if (href && href.startsWith('http')) {
      await this.page.goto(href, { waitUntil: 'domcontentloaded' });
      await this.sleep(2000);
    } else if (href && !href.startsWith('http') && !href.startsWith('#')) {
      await applyBtn.click();
      await this.sleep(2000);
    } else {
      await applyBtn.click();
      await this.sleep(2000);
    }
    if (job.cvPath) {
      for (const sel of ['input[type="file"]', 'input[accept*="pdf"]', 'input[name*="resume"]', 'input[name*="cv"]']) {
        const input = await this.page.$(sel);
        if (input) { await input.setInputFiles(job.cvPath); break; }
      }
    }
    return { applied: true, method: 'ats_apply' };
  }
}
