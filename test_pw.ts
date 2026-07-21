import { chromium } from "playwright"
const b = await chromium.launch({ headless: true })
const p = await b.newPage()
await p.goto('https://example.com', { timeout: 15000 })
console.log('title:', await p.title())
await b.close()
console.log('OK')
