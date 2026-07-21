import BaseAutomator from './base.js';

export default class TheMuseAutomator extends BaseAutomator {
  constructor(config) {
    super('themuse', config);
  }

  async submit(job) {
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(3000);
    // The Muse shows company's own apply URL in a sidebar button
    const applyBtnSelectors = [
      'a[class*="apply"]',
      'button[class*="apply"]',
      'a[data-action="apply"]',
      'a:has-text("Apply")',
      'a[target="_blank"][href*="http"]',
      '.job-details-actions a[href*="http"]',
      'a.external-apply',
      'a.apply-button',
    ];
    let applyBtn = null;
    for (const sel of applyBtnSelectors) {
      applyBtn = await this.page.$(sel);
      if (applyBtn) break;
    }
    // If no dedicated apply button, find the first external link (company career page)
    if (!applyBtn) {
      applyBtn = await this.page.$('a[href*="careers"], a[href*="job"], a[href*="jobs"]');
    }
    if (!applyBtn) throw new Error('Apply button not found on The Muse');
    const applyHref = await applyBtn.getAttribute('href');
    const redirectUrl = applyHref && applyHref.startsWith('http') ? applyHref : null;
    if (redirectUrl) {
      await this.page.goto(redirectUrl, { waitUntil: 'domcontentloaded' });
      await this.sleep(2000);
      if (job.cvPath) {
        const fileInput = await this.page.$('input[type="file"]');
        if (fileInput) await fileInput.setInputFiles(job.cvPath);
      }
      const submitBtn = await this.page.$('input[type="submit"], button[type="submit"]');
      if (submitBtn) await submitBtn.click();
      return { applied: true, method: 'redirect_apply', redirectUrl };
    }
    return { applied: true, method: 'external_redirect', redirectUrl: applyHref || 'unknown' };
  }
}
