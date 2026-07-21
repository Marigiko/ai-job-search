import BaseAutomator from './base.js';

export default class RemotiveAutomator extends BaseAutomator {
  constructor(config) {
    super('remotive', config);
  }

  async submit(job) {
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);
    const applyBtn = await this.page.$('a[href*="apply"], a:has-text("Apply"), a:has-text("apply")');
    if (!applyBtn) {
      const externalBtn = await this.page.$('a[target="_blank"][rel*="noopener"]');
      if (!externalBtn) throw new Error('Apply button not found on Remotive');
      const href = await externalBtn.getAttribute('href');
      return { applied: true, method: 'external_redirect', redirectUrl: href || 'unknown' };
    }
    const href = await applyBtn.getAttribute('href');
    return { applied: true, method: 'external_redirect', redirectUrl: href || 'unknown' };
  }
}
