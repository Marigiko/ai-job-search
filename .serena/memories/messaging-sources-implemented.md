Messaging platform job sources implemented (2026-07-15):

New skills in .agents/skills/:
- telegram-search: Telethon MTProto (fetch history + real-time listener). Auth via TELEGRAM_API_ID + TELEGRAM_API_HASH env vars.
- discord-search: discord.py bot (fetch channels + listener). Auth via DISCORD_BOT_TOKEN.
- whatsapp-search: Baileys (QR scan auth + real-time listener). Session in job_scraper/.whatsapp_session/. Ban risk — use secondary number.
- image-ocr: rapidocr (primary, no binary) + pytesseract (fallback). CLI: ocr_cli.py {ocr,extract,batch,parse}.

All sources discovered automatically by /scrape (reads .agents/skills/*/SKILL.md).
Shared parser: job-scraper/sources/shared_parser.py + shared_parser.ts (both platforms).
Image flow: jobs_images/{source}/*.png → batch OCR → parse → /apply.
