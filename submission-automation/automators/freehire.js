import BaseAutomator from './base.js';

export default class FreehireAutomator extends BaseAutomator {
  constructor(config) {
    super('freehire', config);
  }

  async submit(job) {
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);
    const applyBtn = await this.page.$('a[href*="apply"], a:has-text("Apply"), button:has-text("Apply"), a:has-text("apply")');
    if (!applyBtn) throw new Error('Apply button not found on freehire');
    const href = await applyBtn.getAttribute('href');
    const redirectUrl = href && href.startsWith('http') ? href : null;
    if (redirectUrl) {
      await this.page.goto(redirectUrl, { waitUntil: 'domcontentloaded' });
      await this.sleep(2000);
      const fileInput = await this.page.$('input[type="file"]');
      if (fileInput && job.cvPath) await fileInput.setInputFiles(job.cvPath);
      const submitBtn = await this.page.$('input[type="submit"], button[type="submit"]');
      if (submitBtn) await submitBtn.click();
      return { applied: true, method: 'redirect_apply', redirectUrl };
    }
    return { applied: true, method: 'external_redirect', redirectUrl: href || 'unknown' };
  }
}
