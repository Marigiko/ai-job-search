import BaseAutomator from './base.js';

export default class GetOnBoardAutomator extends BaseAutomator {
  constructor(config) {
    super('getonbrd', config);
    this.email = process.env.GETONBRD_EMAIL;
    this.password = process.env.GETONBRD_PASSWORD;
  }

  async login() {
    if (!this.password) {
      console.log('  ℹ GetOnBoard uses Google OAuth — skipping login');
      return;
    }
    await this.page.goto('https://www.getonbrd.com/users/sign_in', { waitUntil: 'domcontentloaded' });
    await this.page.fill('#user_email', this.email);
    await this.page.fill('#user_password', this.password);
    await this.page.click('input[type="submit"]');
    await this.page.waitForURL('**/dashboard**', { timeout: 15000 }).catch(() => {});
    console.log('  ✓ Logged in to GetOnBoard');
  }

  async submit(job) {
    // GetOnBoard uses Google OAuth only — cannot automate with password.
    // Must submit manually via browser at https://www.getonbrd.com
    if (!this.password) {
      console.log('  ⚠ GetOnBoard uses Google OAuth — skipping (submit manually)');
      console.log(`    URL: ${job.url}`);
      return { applied: false, method: 'manual_oauth' };
    }
    const isLoggedIn = this.page.url().includes('getonbrd');
    if (!isLoggedIn || this.page.url().includes('sign_in')) await this.login();
    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);
    const applyBtn = await this.page.$('a[data-behavior="apply_button"], a[data-action="apply"], a:has-text("Postular")');
    if (!applyBtn) {
      const directApply = await this.page.$('a[href*="/apply"], button:has-text("Apply")');
      if (!directApply) throw new Error('Apply button not found');
      await directApply.click();
    } else {
      await applyBtn.click();
    }
    await this.sleep(3000);
    if (job.cvPath) {
      const fileInput = await this.page.$('input[type="file"]');
      if (fileInput) await fileInput.setInputFiles(job.cvPath);
    }
    const submitBtn = await this.page.$('input[type="submit"], button[type="submit"], button:has-text("Enviar"), button:has-text("Apply")');
    if (submitBtn) {
      await submitBtn.click();
      await this.sleep(2000);
    }
    return { applied: true, method: 'web_apply' };
  }
}
