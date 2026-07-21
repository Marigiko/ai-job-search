import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';

export default class BaseAutomator {
  constructor(portalName, config = {}) {
    this.portalName = portalName;
    this.headless = config.headless !== false;
    this.slowMo = config.slowMo || 0;
    this.timeout = config.timeout || 30000;
    this.browser = null;
    this.context = null;
    this.page = null;
    this.results = [];
  }

  async init() {
    this.browser = await chromium.launch({
      headless: this.headless,
      slowMo: this.slowMo,
      args: ['--disable-blink-features=AutomationControlled'],
    });
    this.context = await this.browser.newContext({
      viewport: { width: 1280, height: 800 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    });
    this.page = await this.context.newPage();
    this.page.setDefaultTimeout(this.timeout);
  }

  async destroy() {
    if (this.browser) await this.browser.close();
  }

  async sleep(ms) {
    await new Promise(r => setTimeout(r, ms));
  }

  async submit(job) {
    throw new Error(`submit() not implemented for ${this.portalName}`);
  }

  async runAll(jobs) {
    this.results = [];
    for (const job of jobs) {
      try {
        console.log(`\n[${this.portalName}] Applying to: ${job.company} - ${job.title}`);
        const result = await this.submit(job);
        this.results.push({ ...job, status: 'submitted', error: null, ...result });
        console.log(`  ✓ Submitted: ${job.company}`);
      } catch (err) {
        console.error(`  ✗ Failed: ${job.company} - ${err.message}`);
        this.results.push({ ...job, status: 'failed', error: err.message });
      }
      await this.sleep(2000 + Math.random() * 3000);
    }
    return this.results;
  }

  async uploadFile(inputSelector, filePath) {
    if (!filePath || !fs.existsSync(filePath)) {
      console.warn(`  ⚠ File not found: ${filePath}`);
      return false;
    }
    const input = await this.page.$(inputSelector);
    if (!input) {
      console.warn(`  ⚠ Upload input not found: ${inputSelector}`);
      return false;
    }
    await input.setInputFiles(filePath);
    return true;
  }

  async typeSlow(selectorOrPage, text, delay = 30) {
    const p = selectorOrPage._type ? selectorOrPage : this.page;
    if (typeof selectorOrPage === 'string') {
      await p.fill(selectorOrPage, text);
    } else if (typeof text === 'string') {
      await p.keyboard.type(text, { delay });
    }
  }

  generateReport() {
    const submitted = this.results.filter(r => r.status === 'submitted').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    return {
      portal: this.portalName,
      total: this.results.length,
      submitted,
      failed,
      results: this.results,
    };
  }
}
