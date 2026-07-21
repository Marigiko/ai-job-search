export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n");
}

export function writeOutput(payload: unknown): void {
  process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
}
