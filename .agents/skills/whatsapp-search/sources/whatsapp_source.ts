// TypeScript version of the WhatsApp parser for the bun CLI to import.
import { parseJobText } from "../../job-scraper/sources/shared_parser.js";

export function parse(text: string): Record<string, unknown> {
  return parseJobText(text);
}
