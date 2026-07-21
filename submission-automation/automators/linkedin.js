import BaseAutomator from './base.js';
import { matchAnswer, PROFILE } from '../config/profile_answers.js';

export default class LinkedInAutomator extends BaseAutomator {
  constructor(config) {
    super('linkedin', config);
    this.email = process.env.LINKEDIN_EMAIL;
    this.password = process.env.LINKEDIN_PASSWORD;
  }

  normalizeUrl(url) {
    return url.replace(/\/\/[a-z]{2}\.linkedin\.com\//, '//www.linkedin.com/');
  }

  async login() {
    await this.page.goto('https://www.linkedin.com/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log('  ⏳ Please log in to LinkedIn in the browser window...');
    console.log('     Waiting up to 120s for you to complete login...');
    try {
      await this.page.waitForURL('**/feed**', { timeout: 120000 });
      console.log('  ✓ Detected LinkedIn login complete');
    } catch {
      const currentUrl = this.page.url();
      if (currentUrl.includes('linkedin.com') && !currentUrl.includes('login')) {
        console.log('  ✓ Detected LinkedIn login (redirected to', currentUrl, ')');
      } else {
        throw new Error('LinkedIn login not detected within 120s timeout');
      }
    }
  }

  async isLoggedIn() {
    const url = this.page.url();
    return url.includes('linkedin.com') && !url.includes('login') && !url.includes('/auth/');
  }

  async answerEasyApplyFields() {
    // Find and fill all visible form fields in the Easy Apply modal
    const fields = await this.page.evaluate(() => {
      const modal = document.querySelector('.jobs-easy-apply-modal, [data-test-modal]');
      if (!modal) return [];

      return Array.from(modal.querySelectorAll('input:not([type="hidden"]):not([type="email"]):not([type="password"]):not([type="search"]), select, textarea'))
        .filter(f => f.offsetParent !== null)
        .map(f => {
          const label = f.closest('.fb-form-element, .artdeco-text-input--container, .artdeco-select, li, div');
          const labelText = label ? (label.textContent || '').trim().substring(0, 300) : '';
          const forLabel = document.querySelector(`label[for="${f.id}"]`);
          return {
            id: f.id,
            name: f.name,
            type: f.getAttribute('type') || f.type || f.tagName.toLowerCase(),
            placeholder: f.getAttribute('placeholder') || '',
            tag: f.tagName.toLowerCase(),
            required: f.required,
            labelText: forLabel ? (forLabel.textContent || '').trim() : labelText,
            ariaLabel: f.getAttribute('aria-label') || '',
          };
        });
    });

    if (fields.length === 0) return;

    console.log(`  ℹ Filling ${fields.length} Easy Apply field(s)`);

    for (const field of fields) {
      const questionText = [field.labelText, field.ariaLabel, field.placeholder, field.name, field.id]
        .filter(Boolean)
        .join(' | ');

      // Get select options if applicable
      let options = [];
      if (field.tag === 'select') {
        options = await this.page.evaluate((name) => {
          const sel = document.querySelector(`select[name="${name}"], select[id="${name}"]`);
          if (!sel) return [];
          return Array.from(sel.options).filter(o => o.value).map(o => o.text);
        }, field.name || field.id);
      }

      const result = matchAnswer(questionText, field.type, options);

      if (result) {
        console.log(`    ✓ "${questionText.substring(0, 50)}..." → "${result.value}"`);
        await this.fillEasyApplyField(field, result.value);
      }
    }
  }

  async fillEasyApplyField(field, value) {
    const selector = `#${CSS.escape(field.id)}`;

    switch (field.tag) {
      case 'select': {
        const select = await this.page.$(selector);
        if (!select) break;
        const opts = await select.evaluate(el => Array.from(el.options).filter(o => o.value).map(o => ({ value: o.value, text: o.text.toLowerCase() })));
        const valLower = value.toLowerCase();
        const match = opts.find(o => o.text.includes(valLower) || valLower.includes(o.text));
        if (match) {
          await select.selectOption(match.value);
        } else if (opts.length > 0) {
          await select.selectOption(opts[opts.length - 1].value);
        }
        break;
      }
      case 'textarea': {
        const ta = await this.page.$(selector);
        if (!ta) break;
        await ta.fill(value);
        break;
      }
      default: {
        if (field.type === 'radio') {
          const radios = await this.page.$$(`input[name="${CSS.escape(field.name)}"]`);
          for (const r of radios) {
            const text = await r.evaluate(el => (el.parentElement?.textContent || '').toLowerCase());
            if (text.includes(value.toLowerCase().substring(0, 3))) {
              await r.check();
              break;
            }
          }
        } else if (field.type === 'checkbox') {
          if (value.toLowerCase().startsWith('sí') || value.toLowerCase() === 'yes' || value.toLowerCase() === 'si') {
            const cb = await this.page.$(selector);
            if (cb && !(await cb.isChecked())) await cb.check();
          }
        } else {
          const input = await this.page.$(selector);
          if (!input) break;
          await input.fill(value);
        }
      }
    }
  }

  async submit(job) {
    if (!this.email || !this.password) throw new Error('LINKEDIN_EMAIL and LINKEDIN_PASSWORD required');
    if (!(await this.isLoggedIn())) await this.login();
    const normalizedUrl = this.normalizeUrl(job.url);
    await this.page.goto(normalizedUrl, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(3000);

    // Try Easy Apply first
    const easyApplyBtn = await this.page.$('button.jobs-apply-button');
    if (easyApplyBtn) {
      await easyApplyBtn.click();
      await this.sleep(2000);
      let step = 0;
      const maxSteps = 10;
      while (step < maxSteps) {
        step++;

        // Answer any form fields before proceeding
        await this.answerEasyApplyFields();

        const nextBtn = await this.page.$('button[aria-label="Continue to next step"]');
        const reviewBtn = await this.page.$('button[aria-label="Review your application"]');
        const submitBtn = await this.page.$('button[aria-label="Submit application"]');
        const doneBtn = await this.page.$('button[aria-label="Dismiss"]');
        if (submitBtn) {
          if (job.cvPath) await this.uploadFile('input[type="file"]', job.cvPath);
          await submitBtn.click();
          await this.sleep(3000);
          break;
        }
        if (reviewBtn) {
          await reviewBtn.click();
          await this.sleep(1500);
          continue;
        }
        if (nextBtn) {
          await nextBtn.click();
          await this.sleep(1500);
          continue;
        }
        if (doneBtn) {
          await doneBtn.click();
          break;
        }
        await this.sleep(1000);
      }
      return { applied: true, method: 'Easy Apply' };
    }

    // Fallback: external apply — look for the "Apply" link that opens external site
    const externalApplySelectors = [
      'a.jobs-apply-button--nondashboard',
      'a.jobs-apply-button[href*="http"]',
      'a[data-control-name="apply_job"]',
      'a:has-text("Apply")',
      'button:has-text("Apply")',
      'a:has-text("Postular")',
      'button:has-text("Postular")',
      'a:has-text("Solicitar")',
      'button:has-text("Solicitar")',
      'a:has-text("Candidat")',
      'button:has-text("Candidat")',
      '[data-job-id] a[href*="http"]:not([href*="linkedin"])',
    ];
    for (const sel of externalApplySelectors) {
      const btn = await this.page.$(sel);
      if (btn) {
        const href = await btn.getAttribute('href');
        if (href && href.startsWith('http')) {
          await this.page.goto(href, { waitUntil: 'domcontentloaded' });
          await this.sleep(2000);
          if (job.cvPath) {
            const fileInput = await this.page.$('input[type="file"]');
            if (fileInput) await fileInput.setInputFiles(job.cvPath);
          }
          const submitBtn = await this.page.$('input[type="submit"], button[type="submit"]');
          if (submitBtn) await submitBtn.click();
          return { applied: true, method: 'external_redirect', redirectUrl: href };
        }
        await btn.click();
        await this.sleep(3000);
        return { applied: true, method: 'external_apply' };
      }
    }

    const pageText = await this.page.evaluate(() => document.body?.innerText?.substring(0, 500) || '');
    const pageTitle = await this.page.title();
    console.log(`  ⚠ Page title: "${pageTitle}", body preview: "${pageText.substring(0, 200).replace(/\n/g, ' ')}"`);
    throw new Error('No apply button found on LinkedIn page');
  }
}
