---
name: setup
description: >
  Profile onboarding for the AI Job Search framework — collect professional info and populate all profile
  files (candidate profile, behavioral, CV templates, interview prep, search queries) so the apply workflow
  works out of the box. Three paths: documents folder, single CV import, interview mode.
  Triggers on: /setup, setup, configure profile, update profile, onboarding, profile setup, configure
allowed-tools: Read, Write, Edit, Glob, Grep, WebFetch, WebSearch
---

# Setup

---

You are running the onboarding setup for the AI Job Search framework. Your goal is to collect the user's professional information and populate all profile files so the `apply` workflow works out of the box.

There are three paths into setup. Step 0 picks the right one; all three converge on Step 3 (file generation) and Step 4 (confirmation).

---

## Step 0: Welcome & Choose Path

If the user's message contains `--section <name>`, skip directly to that section in Path C for an update-only flow. Do not run the path-selection prompt below.

Otherwise, before greeting the user, scan the `documents/` folder. Use Glob with `documents/**/*` and count files per subfolder (`cv/`, `linkedin/`, `diplomas/`, `references/`, `applications/`).

Then welcome the user with a single message that lists three paths. The wording changes based on what was found.

**If `documents/` has files** in one or more subfolders, lead with Path A:

> **Welcome to the AI Job Search setup!**
>
> I'll help you build your professional profile so Claude can evaluate job postings, tailor CVs, write cover letters, and prepare you for interviews.
>
> I see files in your `documents/` folder: [list per subfolder]. Three ways to start:
>
> **Path A: Read my documents folder** (recommended for what you have) — I'll read everything in `documents/`, cross-reference for consistency, and build your profile from real source materials. Idempotent and safe to re-run as you add more documents.
>
> **Path B: Single CV import** — Paste or @-mention a single CV/resume here. I'll extract it and ask follow-up questions for what's missing.
>
> **Path C: Interview mode** — I'll walk you through structured questions section by section.
>
> Which would you like?

**If `documents/` is empty or missing**, surface Path A as a "do this if you have materials" option:

> **Welcome to the AI Job Search setup!**
>
> I'll help you build your professional profile so Claude can evaluate job postings, tailor CVs, write cover letters, and prepare you for interviews.
>
> Three ways to start:
>
> **Path A: Documents folder** (best signal if you have several materials) — Drop your CV / LinkedIn export / diplomas / reference letters in the `documents/` folder, then say "go". I'll read everything and build your profile from it. See `documents/README.md` for the folder layout.
>
> **Path B: Single CV import** — Paste or @-mention a single CV/resume here. I'll extract it and ask follow-up questions for what's missing.
>
> **Path C: Interview mode** — I'll walk you through structured questions section by section. Good if you're starting from scratch.
>
> Which would you like?

Wait for the user's choice. If they pick A but the folder is still empty, tell them what to add (point at `documents/README.md`) and stop.

---

## Path A: Documents Folder

Reads structured documents in `documents/`, cross-references them for consistency, and merges extracted data into the seven profile skill files. Read-before-write and idempotent: changes already present will not be proposed again.

Follow these steps **exactly in order**.

### Step A1: Inventory

Use Glob with `documents/**/*` to scan the full tree. Print:

```
## Documents Found

**cv/**: [list files, or "(empty)"]
**linkedin/**: [list files, or "(empty)"]
**diplomas/**: [list files, or "(empty)"]
**references/**: [list files, or "(empty)"]
**applications/**: [list subfolders with their files, or "(empty)"]

I will read these and cross-reference before proposing any changes.
```

If every subfolder is empty, stop and tell the user to populate the folder. Point at `documents/README.md` for the layout.

### Step A2: Read Existing Skill Files

Read these in parallel before extracting anything. You must know what is already there to make the merge intelligent.

- `.claude/skills/job-application-assistant/01-candidate-profile.md`
- `.claude/skills/job-application-assistant/02-behavioral-profile.md`
- `.claude/skills/job-application-assistant/03-writing-style.md`
- `.claude/skills/job-application-assistant/04-job-evaluation.md`
- `.claude/skills/job-application-assistant/05-cv-templates.md`
- `.claude/skills/job-application-assistant/06-cover-letter-templates.md`
- `.claude/skills/job-application-assistant/07-interview-prep.md`

Hold this content in context throughout Path A. Do not re-read.

### Step A3: Parse Documents

Read each document found in Step A1. Process subfolders in this order: `cv/`, `linkedin/`, `diplomas/`, `references/`, `applications/`.

**`cv/` documents:** name, contact (email, phone, LinkedIn, GitHub), education (degree, institution, dates, thesis), work experience (title, company, dates, location, bullets), skills, publications, awards, profile/summary.

**`linkedin/` documents:** About/summary section (full text, used for behavioral inference), work experience, education, skills and endorsements, certifications, volunteer work, publications, recommendations received (full text). If multiple LinkedIn exports are present, use the most recently modified file.

**`diplomas/` documents:** official degree title and level, institution name (official spelling), graduation date, grade or distinction or GPA if visible.

**`references/` documents:** referee name, title, organization; full text of the letter (extract specific quotes); competency language used.

**`applications/<company>_<role>/` subfolders:**
- `job_posting.md`: role title, company, required skills, experience level, sector, role type
- `cover_letter.tex`: opening structure, body structure, bullet style, closing, recurring phrases
- `cv_draft.tex`: profile statement, section ordering, framing for this role type
- `outcome.md`: status, interview stages, notes. Skip `in_progress` applications for calibration.

After reading, proceed to Step A4 without intermediate output. The user sees a complete picture in Step A6.

### Step A4: Cross-Reference Check

Before mapping anything to skill files, check for inconsistencies:

- Date mismatches between CV / LinkedIn / diploma
- Title mismatches across documents for the same role
- Education mismatches (degree name, graduation date)
- Employer name variations

If inconsistencies are found, present them as a numbered list and wait for the user to resolve each one before continuing. If no inconsistencies, state "No cross-reference issues found." and continue.

### Step A5: Build Change Sets

For each skill file, compare extracted document content against the current file content from Step A2. Build two buckets.

**Additive changes:** entirely new content not in the skill file in any form.

**Conflicting changes:** content that touches something already in a skill file but disagrees.

**Inference rules** (apply when populating from inferred sources):

- **`02-behavioral-profile.md`:** Source is LinkedIn About + recommendation letters. Extract recurring themes, adjectives, phrases. Add only to "Strongest Behavioral Traits", "How [Candidate] Works Best", or "Management Style Preferences" sections. Always label inferred additions: *[Inferred from LinkedIn About / Reference letter — review before relying on this]*
- **`03-writing-style.md`:** Source is `cover_letter.tex` files. Extract recurring patterns. Add as observations under "## Patterns Observed in Past Applications".
- **`04-job-evaluation.md`:** Source is `job_posting.md` + `outcome.md` pairs. Add findings under "## Calibration from Past Applications".
- **`05-cv-templates.md`:** Source is `cv_draft.tex` files. Extract profile statements. Label with: *[Used for: <company>_<role>]*
- **`06-cover-letter-templates.md`:** Source is `cover_letter.tex` files. Extract opening patterns, bullet structures, closing formulations.
- **`07-interview-prep.md`:** Identify achievements not yet covered by an existing STAR example. Do NOT draft full STAR examples. Add stubs under "## STAR Candidates (Complete Manually)".

### Step A6: Present and Confirm Changes

Present the full change set before writing anything. Ask the user to confirm additive changes (all or skip-listed) and resolve conflicting changes one at a time.

### Step A7: Write Confirmed Changes and Fill Gaps

Apply the confirmed changes with the Edit tool. Make targeted edits only. Do not rewrite entire files. State which changes were applied per file.

Documents cover skills, experience, education, references, and behavioral signal. They do not cover everything `apply` and `scrape` need. After the writes, ask follow-up questions for gaps:

- Career goals and target role types
- What excites the user in their next role
- Deal-breakers and must-haves
- Salary expectations / baseline
- Commute or location constraints
- Job search configuration (use the questions from Path C Section 9 below)

Then proceed to Step 3. Step 3 will detect that the seven skill files are already populated and skip those substeps.

---

## Path B: Single CV Import

If the user provides a single CV/resume:

1. Read the document thoroughly.
2. Extract all structured information: name, contact, education, experience, skills, publications, awards.
3. Present a summary of what was extracted.
4. Ask follow-up questions for gaps (behavioral profile, career goals, deal-breakers, salary expectations, references).
5. Proceed to Step 3 (file generation).

---

## Path C: Interview Mode

Walk through each section conversationally. Ask questions naturally, not as a form.

### Section 1: Identity & Contact
Full name, location, phone, email, LinkedIn, GitHub, languages, employment status, constraints.

### Section 2: Education
For each degree: level, field, institution, years, thesis. Also certifications.

### Section 3: Professional Experience
For each role: title, company, dates, location, key responsibilities, achievements, technologies. Also independent projects.

### Section 4: Technical Skills
Languages + proficiency, ML/AI frameworks, domain expertise, platforms, other skills.

### Section 5: Publications & Awards (optional)

### Section 6: Behavioral Profile (optional)
If they have a formal assessment, ask for results. If not, ask behavioral questions and synthesize.

### Section 7: Career Goals & Preferences
- **Target roles (canonical list):** collect 2-5 role types in priority order. These become `### Target Roles` in CLAUDE.md and `01-candidate-profile.md`.
- What excites you in work
- Deal-breakers and must-haves
- **Compensation band (required):** min acceptable, ideal target, currency/period. Persist to `### Compensation`.
- **Mobility (relocation & visa):** open to relocation? need visa? remote acceptable? Persist to `### Mobility`. Relocation is scored positively, never a deal-breaker.

### Section 8: References (optional)

### Section 9: Job Search Configuration
This section generates the search queries that power `scrape`.

Ask about:
- **Role titles to search for** (3-8 specific titles)
- **Key skills as search terms** (3-5 distinctive skills)
- **Target companies** (optional)
- **Geographic scope** (cities/regions)
- **Job portals** (built-in Danish tools vs. alternatives for non-Danish markets)

**Important:** Suggest role types the user may not have considered based on their skill profile.

---

## Step 3: Generate Profile Files

Once data collection is complete, generate or finish populating the following files. **For Path A**, the seven skill files are already populated by Step A7; check each before writing and skip if its content is no longer placeholder text.

### 1. Update `CLAUDE.md`
Replace all `[PLACEHOLDER]` tokens with the user's actual information. Keep the structure, workflow, and verification checklist intact. Fill `### Target Roles`, `### Compensation`, and `### Mobility` from Section 7.

### 2. Populate `01-candidate-profile.md` *(Path B and C; skip if Path A populated it)*
Write the full candidate profile with structured sections: Identity, Job Search Preferences (Target Roles, Compensation, Mobility — mirror CLAUDE.md), Education, Professional Experience, Independent Projects, Technical Skills, Publications, Awards, References.

### 3. Populate `02-behavioral-profile.md` *(Path B and C; skip if Path A populated it)*

### 4. Update `04-job-evaluation.md` *(Path B and C; skip if Path A populated it)*
Replace skill match areas, career goals, motivation filters with actual data.

### 5. Update `05-cv-templates.md` *(Path B and C; skip if Path A populated it)*

### 6. Update `07-interview-prep.md` *(Path B and C; skip if Path A populated it)*
Create STAR examples from actual experience (at least 3-4). Path A leaves STAR stubs — mention them in Step 4.

### 7. Update `cv/main_example.tex`
Replace placeholder personal data with actual info, add education and most recent experience entries.

### 8. Generate `.claude/skills/job-scraper/search-queries.md`
Populate from Section 9 (or Path A's Step A7). Keep priority tiers keyed to `### Target Roles`. Replace remaining tokens with actual skills, location, salary band, mobility filter.

---

## Step 4: Confirm & Next Steps

Present a summary:

> **Setup complete!** Here's what was generated:
>
> - `CLAUDE.md` — Your full candidate profile
> - `.claude/skills/job-application-assistant/01-candidate-profile.md` — Structured profile
> - `.claude/skills/job-application-assistant/02-behavioral-profile.md` — Behavioral assessment
> - `.claude/skills/job-application-assistant/04-job-evaluation.md` — Personalized evaluation framework
> - `.claude/skills/job-application-assistant/05-cv-templates.md` — CV templates with your profile statements
> - `.claude/skills/job-application-assistant/07-interview-prep.md` — STAR examples from your experience
> - `cv/main_example.tex` — Your LaTeX CV template
> - `.claude/skills/job-scraper/search-queries.md` — Job search queries
>
> **Try it out:**
> - Run the `scrape` skill to search for matching jobs right now
> - Run the `apply` skill with a job posting URL to see the full application workflow
> - Run `setup --section search` later to update your search queries as your priorities evolve

If Path A left any STAR stubs in `07-interview-prep.md`, also note them.

---

## Design Principles

- Three onboarding paths converge on the same skill files. Step 0 picks the right path. Steps 3 and 4 are shared.
- Path A is read-before-write and idempotent.
- Path A labels inferred additions so the user can review them critically.
- Each section in Path C is a natural conversation, not a form.
- Synthesize answers into structured formats (the user does not need to know markdown or LaTeX).
- Can be re-run with `--section <name>` to update specific sections.
- Proactively suggest role types the user may not have considered.
- At the end, suggest running `scrape` and `apply` with a test job posting.
