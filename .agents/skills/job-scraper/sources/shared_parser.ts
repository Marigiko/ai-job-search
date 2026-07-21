// TypeScript port of the shared job-text parser.
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
  let d = text.replace(/\s*[\[\(]\s*at\s*[\]\)]\s*/gi, "@");
  d = d.replace(/\s*[\[\(]\s*dot\s*[\]\)]\s*/gi, ".").replace(/&#64;/g, "@");
  d = d.replace(/\s+at\s+(?=[a-z0-9.-]+\.[a-z]{2,})/gi, "@");
  d = d.replace(/\s+dot\s+/gi, ".");
  const m = d.match(/[\w.+-]+@[\w-]+\.[\w.]+/);
  return m ? m[0] : null;
}

function extractUrl(text: string): string | null {
  const m = text.match(/https?:\/\/[^\s"'<>]+/);
  return m ? m[0].replace(/[).,;]+$/, "") : null;
}
