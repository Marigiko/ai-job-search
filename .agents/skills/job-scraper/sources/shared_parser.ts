// TypeScript port of the shared job-text parser.
// Valid TLDs for email boundary detection (longer/compound first)
const VALID_TLDS: string[] = [
  "com.ar", "com.mx", "com.co", "com.br", "com.pe", "com.uy", "com.cl",
  "com.bo", "com.ec", "com.pa", "com.py", "co.uk", "org.uk",
  "com", "net", "org", "io", "co", "info", "biz", "me", "us", "uk",
  "es", "ar", "mx", "cl", "pe", "br", "uy", "py", "bo", "ec", "ai",
  "tech", "app", "dev", "agency", "online", "store", "site", "cloud",
];

export function parseJobText(text: string): Record<string, string | null> {
  return {
    title: extractField(text, [
      /(?:title|puesto|vacante|rol|position|role)[:\s]*([^\n]+)/i,
      /(?:buscamos|seeking|looking for)[:\s]*([^\n]+)/i,
    ]),
    company: extractField(text, [
      /(?:empresa|compa[iñ]ía|company|organizaci[oó]n)[:\s]*([^\n]+)/i,
      /(?:@|en)\s+([A-Z][\w&.\- ]{1,40})(?:\s|$)/,
    ]),
    location: extractField(text, [
      /(?:ubicaci[oó]n|location|locaci[oó]n|ciudad|modalidad|place)[:\s]*([^\n]+)/i,
    ]),
    salary: extractField(text, [
      new RegExp("(?:salario|salary|remuneraci[oó]n|pago|pay|compensaci[oó]n)[:\\s]*([$\\d.,\\s\\-/]+(?:USD|EUR|ARS|(?:\\w+[/\\/]\\w+))?[^\\n]*)", "i"),
    ]),
    apply_email: extractEmail(text),
    description: text.trim().slice(0, 4000),
    url: extractUrl(text),
  };
}

function extractField(text: string, patterns: RegExp[]): string | null {
  for (const p of patterns) {
    const m = text.match(p);
    if (m && m[1]?.trim()) {
      return m[1].trim();
    }
  }
  return null;
}

function extractEmail(text: string): string | null {
  if (!text) return null;

  // Deobfuscation
  let d = text.replace(/\s*[\[\(]\s*at\s*[\]\)]\s*/gi, "@");
  d = d.replace(/\s*[\[\(]\s*dot\s*[\]\)]\s*/gi, ".").replace(/&#64;/g, "@");

  // Find all @ positions
  const candidates: string[] = [];
  const atRegex = /@/g;
  let match;
  while ((match = atRegex.exec(d)) !== null) {
    const pos = match.index;

    // Expand left (local part)
    let left = pos - 1;
    while (left >= 0 && /[a-zA-Z0-9._%+~-]/.test(d[left])) {
      left--;
    }
    left++;

    // Expand right (domain part)
    let right = pos + 1;
    while (right < d.length && /[a-zA-Z0-9.-]/.test(d[right])) {
      right++;
    }

    const raw = d.slice(left, right).trim().replace(/^[.,;:!?]+|[.,;:!?]+$/g, "");
    const cleaned = truncateAtValidTld(raw);
    if (cleaned && cleaned.includes("@") && cleaned.split("@")[1].includes(".")) {
      candidates.push(cleaned);
    }
  }

  // Return first valid candidate
  for (const c of candidates) {
    if (/^[a-zA-Z0-9._%+\-]{2,64}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(c)) {
      return c;
    }
  }

  return null;
}

function truncateAtValidTld(email: string): string {
  if (!email.includes("@")) return email;

  let bestMatch: string | null = null;
  let bestTldLen = 0;

  for (const tld of VALID_TLDS) {
    const idx = email.toLowerCase().indexOf(`.${tld}`);
    if (idx >= 0) {
      const afterTld = idx + tld.length + 1;
      if (afterTld <= email.length) {
        const before = email.slice(0, idx);
        if (/[a-zA-Z0-9._%+\-]+$/.test(before)) {
          if (tld.length > bestTldLen) {
            bestTldLen = tld.length;
            bestMatch = email.slice(0, afterTld);
          }
        }
      }
    }
  }

  return bestMatch ?? email;
}

function extractUrl(text: string): string | null {
  const m = text.match(/https?:\/\/[^\s"'<>]+/);
  return m ? m[0].replace(/[).,;]+$/, "") : null;
}
