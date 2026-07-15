---
name: apply
description: >
  Two-agent job application workflow: parse a job posting, evaluate fit, draft a tailored CV and cover
  letter, spawn a reviewer agent to critique, revise, compile PDFs and inspect layout, run ATS keyword
  check, and present with verification checklist. For email-apply postings, prepares a Gmail draft.
  Triggers on: /apply, apply, postulación, postular, job application, cv for job, job posting url
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts *), Bash(lualatex *), Bash(xelatex *), Bash(pdftotext *), Bash(python salary_lookup.py *), Bash(python3 salary_lookup.py *), WebFetch, WebSearch, Agent
---

# Apply

---

You are orchestrating a two-agent job application workflow. The user provides a job posting URL or pasted text.

Follow these steps **exactly in order**. Do not skip steps.

**Token-efficiency rules for this workflow:**
- Never re-Read a file whose contents are already in your context from an earlier step. If you read it in Step 1, it is still available in Step 2.
- When dispatching the reviewer agent, pass draft content **inline in the agent prompt** rather than asking the agent to Read files you already have in memory.
- Run the full verification checklist exactly once, at the end (Step 6). The reviewer focuses on content critique, not verification.
- Step 5 (compile and inspect PDFs) is mandatory and non-skippable — LaTeX page-break decisions are unpredictable, and `.tex` files that look fine often produce broken PDFs (orphaned entry titles, cover letters spilling to page 2, bullet fonts mismatching).

---

## Step 0: Parse Input

- If the user provides a URL, use `WebFetch` to retrieve the job posting content.
  - **LinkedIn post URL** (`linkedin.com/posts/...`): don't WebFetch it directly — run
    `bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts extract "<url>" --format json`
    and use the returned `text` as the posting and `applyEmail` as the apply address.
- If the user provides pasted text, use it directly. If the text is a recruiter post, you may run the same
  `linkedin-posts-search parse --text "<text>"` to pull out the `applyEmail`.
- Extract: **company name**, **role title**, **department** (if mentioned), **location**, **language** of the posting, and — if present — the **apply-by-email address** (from `applyEmail`, a `mailto:` link, or a "send your CV to …" line).
- Store these for use throughout the workflow. If an apply email is present, set an **`applyByEmail`** flag — after Step 6 you will run the **Email application path** below instead of just handing back files.

---

## Step 1: DRAFTER - Evaluate Fit

Read the evaluation framework:
- `.claude/skills/job-application-assistant/04-job-evaluation.md`
- `.claude/skills/job-application-assistant/01-candidate-profile.md`

Using the framework from `04-job-evaluation.md`, evaluate the job posting against the candidate's profile. If the salary lookup tool is configured, run:

```bash
python salary_lookup.py "<Company Name>" --json
```

If the posting specifies a city, add `--city "<City>"` to narrow results. Parse the JSON output and include the salary benchmark in the evaluation. If the tool is not configured or returns an error, skip the salary benchmark.

Present the evaluation to the user with:

1. **Skills match** - which required/preferred skills match vs. gaps
2. **Experience match** - how work history maps to the role
3. **Behavioral/culture match** - how behavioral profile fits the role/company culture
4. **Salary benchmark** - salary index for the company (if available)
5. **Overall fit score** and recommendation (strong fit / moderate fit / weak fit)

After presenting the evaluation, ask the user:
> "Should I proceed with drafting the CV and cover letter for this role?"

**If the user says no, stop here.** If yes, continue to Step 2.

---

## Step 2: DRAFTER - Draft CV + Cover Letter

You already have `01-candidate-profile.md` and `04-job-evaluation.md` in context from Step 1. **Do not re-read them.**

Read only the reference files you do not yet have:
- `.claude/skills/job-application-assistant/03-writing-style.md`
- `.claude/skills/job-application-assistant/05-cv-templates.md`
- `.claude/skills/job-application-assistant/06-cover-letter-templates.md`

Also read the most recent existing CV and cover letter files for concrete structural reference (one of each is enough):
- Read any existing `cv/main_*.tex` file as a LaTeX template reference
- Read any existing `cover_letters/cover_*.tex` or `cover_letters/Cover_*.tex` file as a template reference

### CV (`cv/main_<company>.tex`)
- Always in **English**
- Follow the moderncv/banking format from `05-cv-templates.md`
- Tailor the profile statement and experience bullets to the specific role
- Reframe skills and achievements to match job requirements
- Keep to 2 pages

### Cover Letter (`cover_letters/cover_<company>_<role>.tex`)
- **Match the language of the job posting** (Danish posting -> Danish cover letter, English posting -> English cover letter)
- Follow the structure from `06-cover-letter-templates.md`
- Use the `cover.cls` template
- Tailor the opening paragraph to the specific role and company
- Address to a named person if available in the posting, otherwise "Dear Hiring Manager" (or equivalent in posting language)
- Keep to approximately one page
- Any mention of agentic coding or AI tooling must reference **Claude Code** by name

Write both files to disk. Keep the exact text of both drafts in working memory — you will pass them inline to the reviewer in Step 3 and revise them in Step 4 without re-reading.

---

## Step 3: REVIEWER - Research & Critique

Use the **Agent tool** to spawn a `general-purpose` reviewer agent. The reviewer gets a fresh context, so pass the drafts **inline in the prompt** below (do not make the reviewer Read them). Scope the reviewer's file reads to content-critique essentials only — the reviewer does not need the LaTeX template files (`05`, `06`) to critique content, since those govern structural/LaTeX concerns the drafter already applied.

Replace `<COMPANY>`, `<ROLE>`, `<INSERT_JOB_POSTING_TEXT_HERE>`, `<INSERT_CV_DRAFT_HERE>`, and `<INSERT_COVER_LETTER_DRAFT_HERE>` with actual values before dispatching.

```
You are a hiring manager proxy reviewing a job application. Your job is to make the application as targeted and compelling as possible.

## Your Tasks

### 1. Research the Company
Use WebSearch and WebFetch to research:
- The company's website, mission, and recent news
- The specific department or team (if mentioned in the posting)
- Any recent projects, press releases, or strategic initiatives relevant to the role
- Company culture and values

### 2. Read Reference Materials (content-critique only)
Read these four files — and only these — to ground your critique:
- `.claude/skills/job-application-assistant/01-candidate-profile.md`
- `.claude/skills/job-application-assistant/02-behavioral-profile.md` — use this specifically to check whether the cover letter's voice matches the candidate's natural register. A "Collaborator" PI profile, for example, should not be given a combative, solo-hero tone; a "Persuader" profile should not be given over-hedged, apologetic phrasing.
- `.claude/skills/job-application-assistant/03-writing-style.md`
- `.claude/skills/job-application-assistant/04-job-evaluation.md`

Do NOT read `05-cv-templates.md` or `06-cover-letter-templates.md` — those govern LaTeX structure the drafter already applied and are not needed for content critique.

### 3. Drafts to Review
Both drafts are provided inline below. Do NOT use the Read tool on the draft files — use these exact texts.

<CV_DRAFT file="cv/main_<COMPANY>.tex">
<INSERT_CV_DRAFT_HERE>
</CV_DRAFT>

<COVER_LETTER_DRAFT file="cover_letters/cover_<COMPANY>_<ROLE>.tex">
<INSERT_COVER_LETTER_DRAFT_HERE>
</COVER_LETTER_DRAFT>

### 4. Job Posting
<JOB_POSTING>
<INSERT_JOB_POSTING_TEXT_HERE>
</JOB_POSTING>

### 5. Produce Feedback

Return your feedback in **two parts**:

**Part A — Structured edits (preferred format whenever possible):**
A JSON array of concrete edits the drafter can apply directly without re-reading the files. Each edit is an object:
```json
{
  "file": "cv/main_<COMPANY>.tex" | "cover_letters/cover_<COMPANY>_<ROLE>.tex",
  "old_string": "<exact text currently in the draft>",
  "new_string": "<replacement text>",
  "reason": "<one-line rationale: keyword match / company angle / reframing / style>"
}
```
Only use this format when you can quote the exact `old_string` from the drafts above. Make `old_string` unique — include enough surrounding context so it matches exactly once per file.

**Part B — Narrative suggestions (for judgment calls that are not mechanical edits):**
Prose suggestions grouped by category. Produce each category even if your finding is "no issues" — silence on a category can be mistaken for skipping it.
- **Missed keywords/requirements** — what to add and roughly where, if it cannot be expressed as a clean string replacement
- **Company/department-specific angles** — connections between experience and the company's strategic priorities, based on your research
- **Action-oriented reframing** — identify passive, generic, or low-energy statements and suggest action-oriented rewrites. Use this category especially for structural weakness that doesn't fit a single-sentence swap.
- **Tone and style issues** — check against `03-writing-style.md` AND `02-behavioral-profile.md`. Flag any issues with tone, formality, or voice.

**CRITICAL RULE:** All suggestions must be grounded in actual profile data. Do NOT suggest fabricating skills, experience, or achievements.

Do **not** run a verification checklist — the drafter will do that in the final step. Focus on content critique.

Return Part A and Part B together as a single structured message.
```

---

## Step 4: DRAFTER - Revise Based on Feedback

Once the reviewer agent returns its feedback:

1. **Apply Part A (structured edits) directly with the Edit tool.** Do NOT re-read the draft files — you already have them in context from Step 2, and the reviewer's `old_string` values were quoted from that same text. For each edit in the JSON array, call `Edit` with the given `file`, `old_string`, and `new_string`. Skip any whose rationale would require fabricating content.
2. **Apply Part B (narrative suggestions)** using judgment. These need interpretation, not mechanical replacement. Walk through every Part B category the reviewer returned and address it:
   - **Missed keywords/requirements:** add the keyword or capability where it fits naturally in the CV or cover letter. Prefer the experience bullets (concrete evidence) over the profile statement (abstract claim).
   - **Company/department-specific angles:** weave the reviewer's research into the cover letter opening or motivation paragraph. Verify every company claim via WebFetch/WebSearch before including it — do not trust reviewer research at face value.
   - **Action-oriented reframing:** rewrite passive or generic phrasing (CV profile statement, cover letter opening, bullet leads). Structural weakness that the reviewer flagged without a clean JSON edit lives here.
   - **Tone and style issues:** apply the writing-style-guide fixes (no em-dashes, no cliches, no apologetic hedging, consistent first-person active voice).
   Use Edit for targeted changes; only re-read a file if an edit fails because the surrounding text has shifted.
3. Do NOT incorporate any suggestion that would fabricate skills or experience. If a posting requirement is a genuine gap, acknowledge it honestly and frame adjacent experience instead.

After all edits are applied, the two files on disk are the final drafts.

---

## Step 5: DRAFTER - Compile & Inspect PDFs (MANDATORY)

**Never skip this step.** The `.tex` files looking fine is not sufficient — LaTeX page-break decisions are unpredictable and commonly produce broken layouts (orphaned job titles separated from their bullets, cover letters spilling to 2 pages, bullet fonts not matching body text). Compile both documents and visually verify the PDFs before presenting.

### 5a. Compile

- CV uses **lualatex** — pdflatex fails on modern MiKTeX with fontawesome5 font-expansion errors. lualatex handles the same sources cleanly.
- Cover letter uses **xelatex** — cover.cls requires fontspec.

If either compile fails, fix the error and re-compile until clean.

### 5b. Inspect layout

Read both PDFs via the Read tool and verify:

**CV (`cv/main_<company>.pdf`):**
- [ ] Exactly 2 pages (not 1, not 3)
- [ ] No orphaned `\cventry` titles — a job/education title line must never sit alone at the bottom of page 1 with its bullets on page 2. This is the most common failure.
- [ ] Section headings are not isolated at the top of page 2 with only 1-2 lines below
- [ ] No awkward whitespace gaps

**Cover letter (`cover_letters/cover_<company>_<role>.pdf`):**
- [ ] Exactly 1 page
- [ ] Signature block visible, not cut off or pushed to a second page
- [ ] Bullet list font matches surrounding body text (both should be Raleway-Medium)

### 5c. Iterate until clean

If the layout has problems, edit the `.tex` files and recompile. Common fixes (see `05-cv-templates.md` and `06-cover-letter-templates.md` for full details):

- **Orphaned CV entry title:** `\usepackage{needspace}` in preamble, then `\needspace{5\baselineskip}` immediately before the problematic `\cventry`
- **CV spills to page 3 with only a trailing section:** `\enlargethispage{2-3\baselineskip}` before a late section
- **Substantial content on page 3:** cut content using **relevance-weighted cutting** (see `05-cv-templates.md`). Score each candidate line by (a) relevance to THIS posting's keywords and responsibilities, (b) uniqueness, (c) narrative load. Cut the lowest-total-score line first, regardless of section.
- **Cover letter itemize breaks compile or uses wrong font:** close `\lettercontent{}` before the list, wrap the list in `{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont \begin{itemize}...\end{itemize}\par}`
- **Cover letter spills to 2 pages:** trim using the same relevance-weighted logic. First cut: sentences that restate what a bullet already said. Second cut: a bullet that does not hit posting keywords. Last resort: a bullet that does hit posting keywords. Never reduce geometry or line spacing.

Do not proceed to Step 6 until both PDFs pass inspection.

### 5d. ATS & keyword verification (CV)

An ATS parser reads the PDF's embedded **text layer**, not the rendered page — a CV that passed visual inspection can still extract as garbage. This step verifies what a parser actually sees. It applies to the **CV only**.

**Availability check:** run `pdftotext -v`. `pdftotext` (poppler) is an optional dependency. If it is missing, print a one-line warning that the mechanical parse check is skipped, do the keyword-coverage check against your visual Read of the PDF instead, and note the degraded mode in the Step 6 report.

**1. Extract the text layer:**

Extract the text and read it. **2. Parseability checks** on the extracted text:

- [ ] **Text extracted at all**, with no garbage runs: no `(cid:NNN)` markers, no replacement characters, no stretches of missing text that are visible in the PDF
- [ ] **Email and phone survive as literal text.** Icon fonts extract as glyph names — that noise is harmless, but the actual address and digits must be present. A contact detail carried only by an icon or a hyperlink target is invisible to an ATS.
- [ ] **Reading order matches the visual order** — section headings appear in the same sequence as on the page. The stock banking template is single-column and safe; custom templates registered via the `add-template` skill with sidebars or multi-column layouts are where this breaks.
- [ ] **Dates recognizable** — each role and degree has its years present in the extraction.

Failures here are template-level problems: fix them in the `.tex`, then re-run 5a–5c and re-extract.

**3. Keyword coverage.** Reuse the required/preferred keyword list you extracted in Step 1. Match each keyword against the extracted text, **in the posting's language**. Report a table:

| Keyword | Priority | Status | Note |
|---------|----------|--------|------|
| ... | required/preferred | covered / synonym-only / missing (have it) / missing (gap) | where it appears, or why absent |

- **covered** — the term appears (verbatim or trivial inflection).
- **synonym-only** — the concept is present under a different term. If the posting's exact term is truthfully applicable, prefer the posting's term.
- **missing (have it)** — the candidate genuinely has this skill but the CV never says it: add it where it fits naturally, preferring experience bullets over the profile statement, then re-run 5a–5c.
- **missing (gap)** — a genuine gap: leave it missing. **Never stuff keywords.**

**4. Clean up:** delete the extracted `.txt` file.

### 5e. Clean up build artifacts

After the final clean compile, delete the `.aux`, `.log`, `.out` files (keep the `.tex` and `.pdf`).

---

## Step 6: Present Final Output

Run the full verification checklist from `CLAUDE.md` now — this is the **only** verification pass in the workflow. Re-read both files once here to verify final state on disk matches your mental model after the Step 4 and Step 5 edits.

### Verification Checklist
Report pass/fail for each item in the CLAUDE.md verification checklist (factual accuracy, targeting, consistency, quality).

### Key Tailoring Decisions
Summarize 3-5 key decisions made to tailor the application:
- What was emphasized and why
- What company-specific angles were incorporated
- What the reviewer suggested that was most impactful
- Any gaps that were acknowledged or reframed

### Files Created
List the files written:
- `cv/main_<company>.tex`
- `cover_letters/cover_<company>_<role>.tex`

Tell the user: "Both files are ready for your review."

### Record the draft in the tracker
Append a row to `job_search_tracker.csv` so the funnel is complete and the dashboard can see drafted-but-not-yet-submitted applications:
- `status` = `drafted`
- `date` = today, `company`, `role`, `role_type` (matched to CLAUDE.md → Target Roles), `sector`
- `fit_rating` = the overall score from Step 1
- `salary_expected` = candidate min/ideal band; `salary_offered` = the posting's stated pay if any
- `relocation_visa` = `sponsor` / `relocation` / `remote` / `none` / `unknown` from the Step 1 evaluation
- `source` = posting URL; `application_url` = apply link or `mailto:` if known
- `cv_file` / `cover_letter_file` = the paths just written
If a row for this company+role already exists, update it in place instead of duplicating.

### Next Steps
- **Submitted?** Run the `outcome` skill for that company to move the row from `drafted` to `applied`.
- **Interview scheduled?** Run the `interview` skill to build a stage-specific prep pack.

---

## Email application path (only if `applyByEmail` was set in Step 0)

When the role is applied to **by email**, finish by preparing a ready-to-send Gmail draft. **Never send automatically** — you prepare, the user sends.

1. **Draft the email body.** Short and specific (6–10 lines): greeting to the named contact (or "Dear Hiring Manager"), one line on the role + where you saw it, 3–4 lines mapping your strongest matches to the posting (grounded in the profile — never fabricate), a line on availability/relocation-or-remote per CLAUDE.md → Mobility, and a sign-off with your name and contact details. Match the posting's language (Spanish/English). Reference **Claude Code** by name only if agentic-coding experience is genuinely relevant.
2. **Subject line:** `Application: <Role> — <Your Name>` (localize if the posting is in Spanish, e.g. `Postulación: <Rol> — <Nombre>`).
3. **Attachments:** the compiled PDFs from Step 5 (CV always; cover letter if the post expects one). Read each PDF and base64-encode it for the Gmail draft.
4. **Preview + explicit confirmation (MANDATORY).** Show the user the full email before touching Gmail. Ask: **"Create this as a Gmail draft for you to review and send?"** Do nothing until the user confirms.
5. **On confirmation, create a Gmail draft** via the appropriate email MCP tool.
6. **Record it in the tracker**: set `channel = email`, `application_url = mailto:<applyEmail>`, `status = drafted`.

**Guardrails:** never create the draft before the user confirms the preview; never invent an email address (use only the one parsed in Step 0); if no PDF compiled, fix Step 5 before drafting the email.
