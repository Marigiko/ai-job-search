#!/usr/bin/env bun
// WhatsApp job fetcher using Baileys (WhatsApp Web protocol).
//
// Personal use only. WhatsApp ToS-violating — ban risk. Use a secondary number.

import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

interface Flags {
  _: string[];
  [k: string]: string | boolean | string[];
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] };
  const alias: Record<string, string> = { t: "text", g: "groups" };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--") || a.startsWith("-")) {
      const key = alias[a.replace(/^-+/, "")] ?? a.replace(/^-+/, "");
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("-")) {
        flags[key] = true;
      } else {
        flags[key] = next;
        i++;
      }
    } else {
      (flags._ as string[]).push(a);
    }
  }
  return flags;
}

const HELP =
  "whatsapp-search CLI — fetch jobs from WhatsApp groups via Baileys\n" +
  "\n" +
  "USAGE\n" +
  "  bun run cli/src/cli.ts auth                        # QR scan to link account\n" +
  "  bun run cli/src/cli.ts listen [--groups g1,g2]     # real-time listener\n" +
  "  bun run cli/src/cli.ts parse --text '<text>'      # parse pasted text\n" +
  "\n" +
  "Personal use only (WhatsApp ToS). Ban risk — use a secondary number.\n";

async function main(): Promise<number> {
  const argv = process.argv.slice(2);
  const flags = parseFlags(argv);
  const cmd = (flags._ as string[])[0];

  if (!cmd || cmd === "help" || flags.help) {
    process.stdout.write(HELP);
    return cmd ? 0 : 1;
  }

  const { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion } = await import(
    "@whiskeysockets/baileys"
  );
  const whatsappSource = await import(resolve(here, "..", "..", "sources", "whatsapp_source.ts"));
  const sessionDir = resolve(here, "..", "..", "..", "..", "job_scraper", ".whatsapp_session");

  if (cmd === "auth") {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    makeWASocket({
      auth: state,
      printQRInTerminal: true,
      version: (await fetchLatestBaileysVersion()).version,
    }).ev.on("creds.update", saveCreds);
    console.log("Scan the QR code above. Session saved to: " + sessionDir);
    return 0;
  }

  if (cmd === "listen") {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const socket = makeWASocket({ auth: state });
    socket.ev.on("creds.update", saveCreds);
    const groupsFilter = ((flags.groups as string) || "")
      .split(",")
      .map((g) => g.trim())
      .filter(Boolean);

    socket.ev.on("messages.upsert", async (upsert) => {
      for (const msg of upsert.messages) {
        if (!msg.message || msg.key.fromMe) continue;
        const isGroup = msg.key.remoteJid?.endsWith("@g.us");
        if (!isGroup) continue;
        const body =
          msg.message.conversation ||
          msg.message.extendedTextMessage?.text ||
          msg.message.imageMessage?.caption ||
          "";
        if (!body) continue;
        const groupName = msg.pushName || msg.key.remoteJid || "unknown";
        if (groupsFilter.length && !groupsFilter.includes(groupName)) continue;
        const parsed = whatsappSource.parse(body) as Record<string, unknown>;
        parsed.id = msg.key.id;
        parsed.date = new Date(Number(msg.messageTimestamp) * 1000).toISOString();
        parsed.author = msg.pushName || null;
        parsed.group = groupName;
        parsed.source = "whatsapp";
        console.log(JSON.stringify({ event: "new_job", result: parsed }, null, 2));
      }
    });

    console.log(
      JSON.stringify({ status: "listening", groups: groupsFilter || "all", message: "Press Ctrl+C to stop." }, null, 2),
    );
    return 0;
  }

  if (cmd === "parse") {
    const text = flags.text as string;
    if (!text) {
      process.stderr.write(JSON.stringify({ error: "parse --text '<text>'", code: "NO_INPUT" }) + "\n");
      return 1;
    }
    const parsed = whatsappSource.parse(text) as Record<string, unknown>;
    parsed.source = "whatsapp";
    console.log(JSON.stringify(parsed, null, 2));
    return 0;
  }

  process.stderr.write(JSON.stringify({ error: "Unknown command: " + cmd, code: "BAD_CMD" }) + "\n");
  return 1;
}

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    process.stderr.write(JSON.stringify({ error: e?.message || String(e), code: "FATAL" }) + "\n");
    process.exit(1);
  });
