import BaseAutomator from './base.js';
import { matchAnswer, PROFILE } from '../config/profile_answers.js';

export default class ComputrabajoAutomator extends BaseAutomator {
  constructor(config) {
    super('computrabajo', config);
    this.email = process.env.COMPUTRABAJO_EMAIL;
    this.password = process.env.COMPUTRABAJO_PASSWORD;
  }

  async login() {
    // This is used for the initial session on ar.computrabajo.com.
    // The Postular button always initiates a separate OIDC login flow
    // on secure.computrabajo.com, which we handle via handleLoginRedirect().
    await this.page.goto('https://www.computrabajo.com.ar/login', { waitUntil: 'domcontentloaded' });
    await this.sleep(3000);
    console.log('  ⏳ Please log in to Computrabajo in the browser window...');
    console.log('     Waiting up to 120s for you to complete login...');
    try {
      await this.page.waitForFunction(() => {
        const url = window.location.href;
        return !url.includes('/login') && !url.includes('/connect/authorize');
      }, { timeout: 120000 });
      console.log('  ✓ Detected Computrabajo login');
    } catch {
      throw new Error('Computrabajo login not detected within 120s timeout');
    }
  }

  async isLoggedIn() {
    const url = this.page.url();
    return url.includes('computrabajo.com') && !url.includes('/login') && !url.includes('/connect/authorize');
  }

  async handleLoginRedirect() {
    if (!this.page.url().toLowerCase().includes('login')) return false;

    console.log('  ⚠ Redirigido a login — autocompletando credenciales...');
    await this.sleep(2000);

    // Step 1: Fill email
    const hasEmail = await this.page.$('#Email');
    if (hasEmail) {
      await hasEmail.fill(this.email);
      await this.sleep(300);
    }

    // Step 1b: Click "Continuar" if present (two-step flow)
    const hasContinueBtn = await this.page.evaluate(() => {
      const btn = document.querySelector('#continueWithMailButton');
      return btn && btn.offsetParent !== null;
    });
    if (hasContinueBtn) {
      console.log('    → Two-step: clicking "Continuar"...');
      await this.page.evaluate(() => {
        const btn = document.querySelector('#continueWithMailButton');
        if (btn) btn.dispatchEvent(new Event('click', { bubbles: true }));
      });
      await this.sleep(2000);
    }

    // Step 2: Fill password
    const hasPassword = await this.page.$('#password');
    if (hasPassword) {
      await hasPassword.fill(this.password);
      await this.sleep(300);
    }

    // Step 3: Click "Iniciar sesión"
    console.log('    → Clicking "Iniciar sesión"...');
    await this.page.evaluate(() => {
      const btn = document.querySelector('#btnSubmitPass');
      if (btn) btn.dispatchEvent(new Event('click', { bubbles: true }));
    });

    // Wait for redirect
    try {
      await this.page.waitForLoadState('domcontentloaded', { timeout: 20000 });
    } catch {}
    await this.sleep(3000);

    // If still on login page, try once more
    if (this.page.url().toLowerCase().includes('login')) {
      console.log('    → Still on login, retrying once...');
      await this.sleep(3000);
      try {
        await this.page.waitForLoadState('domcontentloaded', { timeout: 15000 });
      } catch {}
      await this.sleep(3000);
    }

    console.log(`    → URL after login: ${this.page.url().substring(0, 100)}`);
    return true;
  }

  async answerScreeningQuestions() {
    await this.sleep(2000);

    // Check if there are any visible form fields (screening questions)
    const fields = await this.page.evaluate(() => {
      return Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="email"]):not([type="password"]):not([type="search"]), select, textarea'))
        .filter(f => f.offsetParent !== null)
        .map(f => ({
          id: f.id,
          name: f.name,
          type: f.getAttribute('type') || f.type || f.tagName.toLowerCase(),
          placeholder: f.getAttribute('placeholder') || '',
          tag: f.tagName.toLowerCase(),
          required: f.required,
          className: (f.className || '').substring(0, 60),
          // Get question text from nearest label
          labelText: (() => {
            const label = f.closest('.field, .form-group, [class*="question"], [class*="pregunta"], li, .row, div, fieldset');
            if (label) return (label.textContent || '').trim().substring(0, 300);
            return '';
          })(),
          // Get explicit label
          forLabel: (() => {
            const lbl = document.querySelector(`label[for="${f.id}"]`);
            return lbl ? (lbl.textContent || '').trim() : '';
          })(),
        }));
    });

    if (fields.length === 0) {
      console.log('  ℹ No screening questions found');
      return;
    }

    console.log(`  ℹ Found ${fields.length} screening questions`);

    for (const field of fields) {
      // Combine all text sources for matching
      const questionText = [field.forLabel, field.labelText, field.placeholder, field.name, field.id]
        .filter(Boolean)
        .join(' | ');

      // Get available options for select/radio
      let options = [];
      if (field.tag === 'select') {
        options = await this.page.evaluate((name) => {
          const sel = document.querySelector(`select[name="${name}"], select[id="${name}"]`);
          if (!sel) return [];
          return Array.from(sel.options).filter(o => o.value).map(o => o.text);
        }, field.name || field.id);
      }

      // Match answer using profile database
      const result = matchAnswer(questionText, field.type, options);

      if (result) {
        console.log(`    ✓ "${questionText.substring(0, 60)}..." → "${result.value}" (${result.source})`);
        await this.fillField(field, result.value);
      } else {
        console.log(`    ? "${questionText.substring(0, 60)}..." → sin coincidencia, dejando vacío`);
      }
    }

    await this.sleep(1000);
  }

  async fillField(field, value) {
    const selector = field.id ? `#${field.id}` : `[name="${field.name}"]`;

    switch (field.tag) {
      case 'select': {
        const select = await this.page.$(selector);
        if (!select) break;
        const opts = await select.evaluate(el => Array.from(el.options).filter(o => o.value).map(o => ({ value: o.value, text: o.text.toLowerCase() })));
        // Try to find matching option, else pick first
        const valLower = value.toLowerCase();
        const match = opts.find(o => o.text.includes(valLower) || valLower.includes(o.text));
        if (match) {
          await select.selectOption(match.value);
        } else if (opts.length > 0) {
          // Pick last option (often most senior/positive)
          await select.selectOption(opts[opts.length - 1].value);
        }
        break;
      }
      case 'textarea': {
        const ta = await this.page.$(selector);
        if (!ta) break;
        await ta.fill('');
        await ta.fill(value);
        break;
      }
      default: {
        // input[type="text"], input[type="tel"], input[type="number"], etc.
        if (field.type === 'radio') {
          const radios = await this.page.$$(`input[name="${field.name}"]`);
          for (const r of radios) {
            const text = await r.evaluate(el => (el.parentElement?.textContent || '').toLowerCase());
            if (text.includes(value.toLowerCase().substring(0, 3))) {
              await r.check();
              break;
            }
          }
        } else if (field.type === 'checkbox') {
          if (value.toLowerCase().startsWith('sí') || value.toLowerCase() === 'si' || value.toLowerCase() === 'yes') {
            const cb = await this.page.$(selector);
            if (cb && !(await cb.isChecked())) await cb.check();
          }
        } else {
          const input = await this.page.$(selector);
          if (!input) break;
          await input.fill('');
          await input.fill(value);
        }
      }
    }
  }

  async submit(job) {
    if (!this.email || !this.password) throw new Error('COMPUTRABAJO_EMAIL and COMPUTRABAJO_PASSWORD required');
    if (!(await this.isLoggedIn())) await this.login();

    await this.page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: this.timeout });
    await this.sleep(2000);

    // Click "Postularme"
    let postularBtn = await this.page.$('a.b_primary.big, a[data-href-offer-apply]');
    if (!postularBtn) throw new Error('Postular button not found');
    await postularBtn.evaluate(el => el.dispatchEvent(new Event('click', { bubbles: true })));
    await this.sleep(3000);

    // Handle login redirect (if session not yet established on candidato. subdomain)
    await this.handleLoginRedirect();

    // If we're back on the job page (login completed but Postular stays), click again
    if (this.page.url().includes(job.url.split('/').pop())) {
      console.log('  → Postular still present, clicking again...');
      postularBtn = await this.page.$('a.b_primary.big, a[data-href-offer-apply]');
      if (postularBtn) {
        await postularBtn.evaluate(el => el.dispatchEvent(new Event('click', { bubbles: true })));
        await this.sleep(3000);
        await this.handleLoginRedirect();
      }
    }

    // After login redirects, we land on either:
    //   /match/?oi=...  (new application, may have screening questions)
    //   /apply/?oi=...&idapp=...  (already applied)
    const currentUrl = this.page.url();

    if (currentUrl.includes('/apply/') && currentUrl.includes('idapp=')) {
      console.log('  ℹ Ya postulado anteriormente');
      return { applied: true, method: 'already_applied' };
    }

    if (currentUrl.includes('/match')) {
      // Answer screening questions on match page
      await this.answerScreeningQuestions();

      // Click confirm/submit
      const confirmBtn = await this.page.$('button:has-text("Confirmar"), button:has-text("Enviar"), input[type="submit"]');
      if (confirmBtn) {
        await confirmBtn.click();
        await this.sleep(3000);
      }

      // Upload CV if needed
      if (job.cvPath) {
        const fileInput = await this.page.$('input[type="file"]');
        if (fileInput) await fileInput.setInputFiles(job.cvPath);
      }
    }

    return { applied: true, method: 'web_apply' };
  }
}
