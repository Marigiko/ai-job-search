---
name: linkedin-deep-research
version: 1.0.0
description: >
  Research a company, role, or recruiter on LinkedIn using the native LinkedIn MCP
  tools (linkedin_get_company_profile, linkedin_get_person_profile, linkedin_get_company_employees,
  linkedin_search_jobs, linkedin_search_posts, linkedin_get_feed). Use this BEFORE writing
  a cover letter to find verified, up-to-date company data — never rely on memory or the
  job posting alone. Requires Chrome running with remote debugging on port 9222 and active
  login to LinkedIn (run scripts/start-chrome-debug.bat on Windows first). Trigger phrases:
  research company on linkedin, linkedin company lookup, who works at <company>, find
  recruiter profile, linkedin research for application.
---

# LinkedIn Deep Research

Research companies, roles, and recruiters on LinkedIn using the native MCP tools. This
replaces the manual WebSearch + WebFetch step in `/apply` with structured, verified data.

## Prerequisites

Chrome must be running on Windows with `--remote-debugging-port=9222` and the user logged
into LinkedIn. Check with:

```bash
bash scripts/check-chrome-debug.sh
```

If the check fails, the user must:

1. Run `scripts\start-chrome-debug.bat` on Windows
2. Log into linkedin.com in the Chrome window that opens
3. Keep Chrome running (do not close it)

The LinkedIn MCP server connects to this Chrome instance to scrape data.

## When to Use

- **Before writing a cover letter**: get the company's mission, size, recent posts,
  employees, and culture to write a specific, verified "why this company" paragraph.
- **When the posting is anonymous** (recruiter post without company name): search LinkedIn
  posts and people to identify the real employer.
- **Before an interview**: research the interviewers' profiles and career paths.
- **Salary/role benchmarking**: search current employees with the same title.

## Available Tools

| Tool | What it returns | Use when |
|------|-----------------|----------|
| `linkedin_get_company_profile` | Company about, specialties, website, size | Always, for the target company |
| `linkedin_get_company_employees` | List of employees (name, title, location) | To find team size, hiring patterns |
| `linkedin_search_jobs` | Open jobs at the company | To see what else they're hiring for |
| `linkedin_search_posts` | Recent posts by/about the company | To find news, product launches, culture |
| `linkedin_get_person_profile` | Full profile of a person | For interviewer/recruiter research |
| `linkedin_search_people` | People matching keywords | To find recruiters or hiring managers |
| `linkedin_get_feed` | Authenticated user's feed | To find recent activity from connections |

## Workflow

1. **Check prerequisites**: run `bash scripts/check-chrome-debug.sh`. If it fails, stop
   and ask the user to launch Chrome.
2. **Get company profile**: `linkedin_get_company_profile` with the company name.
   Extract: mission, specialties, company size, industry, website, LinkedIn URL.
3. **Get recent posts**: `linkedin_search_posts` with the company name or relevant
   keywords. Look for: product launches, funding news, culture posts, hiring announcements.
4. **Get employees** (optional): `linkedin_get_company_employees` to understand team
   structure and size.
5. **Return structured findings**: summarize in a format the cover letter drafter can use.

## Output Format

```
## LinkedIn Research: [Company Name]

### Company Overview
- **Mission**: [from about page, 1 sentence]
- **Size**: [employees on LinkedIn]
- **Industry**: [from profile]
- **Specialties**: [from profile]

### Recent Activity (last 30 days)
- [post 1: key point]
- [post 2: key point]

### Key People
- [name, title, relevant background]

### Cover Letter Angles
- [verified specific to reference in the letter — must cite source]
- [another angle]

### Cautions
- [any red flags: layoffs, restructuring, negative reviews]
```

## Rules

- **Never fabricate.** If the MCP tools return nothing, say "no data found on LinkedIn"
  rather than guessing.
- **Cite sources.** Every claim must trace back to a specific tool result.
- **Respect rate limits.** LinkedIn aggressively rate-limits scraping. If a tool fails,
  wait and retry once. Do not loop.
- **Use the posting's language.** If the posting is in Spanish, search Spanish keywords too.

## Integration with /apply

This skill replaces the "Research the Company" step in the `/apply` workflow. Instead of
WebSearch + WebFetch, the drafter should:

1. Run `/linkedin-deep-research <company name>` to get verified data.
2. Use the "Cover Letter Angles" section to write the motivation paragraph.
3. Use the "Cautions" section to avoid敏感 topics.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "browser open on profile" error | Stale Chrome session | Close all Chrome windows, re-run start-chrome-debug.bat |
| "login required" / empty results | Not logged into LinkedIn | Log into linkedin.com in the debug Chrome |
| 403 / rate limit | Too many requests | Wait 60s, retry once. Do not loop. |
| Timeout on person profile | Slow network or large profile | Increase `--timeout` or skip that profile |
