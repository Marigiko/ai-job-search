import BaseAutomator from './base.js';

export default class WeWorkRemotelyAutomator extends BaseAutomator {
  constructor(config) {
    super('weworkremotely', config);
  }

  async submit(job) {
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);
    const applyLinks = await this.page.$$('a[href*="apply"], a[href*="application"], a:has-text("Apply"), a:has-text("apply")');
    let applyUrl = null;
    for (const link of applyLinks) {
      const href = await link.getAttribute('href');
      if (href && !href.startsWith('#')) { applyUrl = href; break; }
    }
    if (!applyUrl) {
      const scriptingLink = await this.page.$('a[href*="scripting"]');
      if (scriptingLink) applyUrl = await scriptingLink.getAttribute('href');
    }
    if (!applyUrl) {
      const allLinks = await this.page.$$('a');
      for (const link of allLinks) {
        const text = (await link.textContent()).toLowerCase().trim();
        if (text === 'apply' || text === 'apply now' || text === 'apply for this job') {
          applyUrl = await link.getAttribute('href');
          break;
        }
      }
    }
    if (!applyUrl) throw new Error('Apply link not found on WeWorkRemotely page');
    if (applyUrl.startsWith('/')) applyUrl = `https://weworkremotely.com${applyUrl}`;
    if (applyUrl.startsWith('http')) {
      await this.page.goto(applyUrl, { waitUntil: 'domcontentloaded' });
      await this.sleep(2000);
      if (job.cvPath) {
        const fileInput = await this.page.$('input[type="file"]');
        if (fileInput) await fileInput.setInputFiles(job.cvPath);
      }
      const submitBtn = await this.page.$('input[type="submit"], button[type="submit"]');
      if (submitBtn) await submitBtn.click();
      return { applied: true, method: 'redirect_apply', redirectUrl: applyUrl };
    }
    return { applied: true, method: 'external_redirect', redirectUrl: applyUrl };
  }
}
