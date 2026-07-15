# Job Evaluation Framework

<!-- SETUP: Skill match areas and career goals are personalized by running /setup -->

## Scoring Dimensions

Evaluate each job posting against these dimensions:

### 1. Technical Skills Match (0-100)
How well do the required/preferred skills align with the candidate's capabilities?

| Score | Meaning |
|-------|---------|
| 80-100 | Core requirements are primary skills |
| 60-79 | Most requirements match, 1-2 gaps that are learnable |
| 40-59 | Partial match, significant upskilling needed |
| 0-39 | Fundamental mismatch |

**Strong match areas:** Node.js/NestJS, TypeScript, Python (FastAPI/Django), REST/GraphQL APIs, AWS, Docker/Kubernetes, CI/CD, event-driven (Kafka/RabbitMQ), LLM automation (Ollama/LangChain/n8n), web scraping (Selenium/Puppeteer), React/Next.js
**Moderate match areas:** React Native/Expo, PHP, Java, Spring, Terraform, GraphQL at scale, data engineering
**Weak match areas:** Go (basics only), Rust, mobile-native (iOS/Android Kotlin/Swift), ML model training (uses LLMs, doesn't train them), formal data-science/statistics roles

### 2. Experience Match (0-100)
Does work history align with what they're looking for?

| Score | Meaning |
|-------|---------|
| 80-100 | Direct experience in the same domain and role type |
| 60-79 | Related experience, transferable skills clear |
| 40-59 | Adjacent experience, would need to make the case |
| 0-39 | Unrelated experience |

**Strong:** backend/full-stack engineering (Node/TS/Python), cloud-native systems on AWS, API design, AI/LLM automation, web scraping, tech mentoring
**Moderate:** frontend-lead roles, DevOps/platform engineering, legal-tech / data-acquisition, startup 0→1 product engineering
**Entry-level:** dedicated data-science/ML-research, SRE-only, senior engineering-management (has mentoring, not formal management)

### 3. Behavioral/Culture Fit (0-100)
Does the role and company culture match the behavioral profile?

| Score | Meaning |
|-------|---------|
| 80-100 | Culture strongly matches behavioral preferences |
| 60-79 | Mixed signals but mostly compatible |
| 40-59 | Some friction areas |
| 0-39 | Significant culture mismatch |

**Red flags to research:** Department disorganization, work dominated by maintenance over development, poor chemistry with leadership, culture mismatches. Check reviews, media coverage, LinkedIn connections, and network contacts for insider perspective.

### 4. Location & Logistics (Pass/Fail + Notes)
Relocation is **not** a deal-breaker for this candidate (see CLAUDE.md → Mobility). It is scored positively in dimension 8.
- Fully remote: PASS
- On-site within commute range: PASS
- On-site abroad **with relocation/visa support offered**: PASS (and boosts dimension 8)
- On-site abroad **that the candidate is willing to relocate for** (even without formal support): PASS with a FLAG (needs a relocation/visa plan — see dim 8)
- On-site somewhere the candidate cannot be and no relocation/remote option: FAIL
- Frequent international travel: FLAG (discuss with user)

### 5. Career Alignment & Motivation (0-100)
Does this role advance career goals and contain tasks that energize?

| Score | Meaning |
|-------|---------|
| 80-100 | Strongly aligned with career direction, clear growth path |
| 60-79 | Good role but only partially aligned with long-term goals |
| 40-59 | Decent job but doesn't build toward career goals |
| 0-39 | Dead end or backwards step |

**Career goals:**
- Land a strong **second income** (min 2000 / ideal 3000 USD/mo) on top of the current part-time Magnar role
- **Migrate abroad** via a role with relocation/visa sponsorship (EU, NZ, USA/Canada) — or remote-USD to self-fund it
- Grow toward senior backend/AI engineering with architectural ownership at an AI-forward company

**Motivation filter:** Evaluate not just whether Mario *can* do the tasks, but whether they will *energize* him:
- Tasks that energize: building scalable/cloud-native systems, AI/LLM automation & agents, 0→1 product work, clean-architecture refactors, mentoring
- Tasks that drain: pure maintenance/legacy-only work, bureaucratic low-autonomy process, ticket-taking with no design input
- Non-task factors: autonomy, AI-forward culture, remote flexibility, relocation/visa support

**Life situation alignment:**
- **Security**: has a part-time role (~1500 USD/mo); this search is for *additional* income, so part-time/contract is fine and the minimum band is a hard floor
- **Flexibility**: must coexist with the current Magnar part-time role → remote-friendly hours strongly preferred
- **Professional development**: wants architectural growth and a path to relocation/migration

### 6. Salary Benchmark (Optional)

If the salary lookup tool is configured (`salary_data.json` exists), look up the company:
```
python salary_lookup.py "<Company Name>" --json
```

If a city is known from the posting, add `--city "<City>"` to narrow results.

Present findings as:
```
### Salary Benchmark
| Metric | Value |
|--------|-------|
| [Category] index | XX.X (+/-X.X% vs baseline) |
| Overall index | XX.X (+/-X.X% vs baseline) |
```

Interpret results relative to the baseline defined in the data file's metadata. For index-based data, higher typically means above-market compensation.

If the salary tool is not configured, skip this section.

> Note: dimension 6 is a *company market benchmark* (context only, unweighted). The candidate's own salary
> preference is scored separately in dimension 7 below.

### 7. Compensation Fit (0-100, with a hard floor)
Score the posting's stated pay against the candidate's band in CLAUDE.md → **Compensation** (min / ideal).

| Situation | Score |
|-----------|-------|
| At or above **ideal** | 100 |
| Between **min** and **ideal** | interpolate 60→100 |
| At **min** exactly | 60 |
| Below **min** | **FAIL** (hard floor — veto, like Location FAIL) |
| No salary stated | 50 + FLAG ("salary undisclosed — confirm before/early in process") |

Normalize to the candidate's currency and period (see CLAUDE.md; monthly USD by default). For annual figures, divide by 12; for hourly/contract, estimate a monthly equivalent and note the assumption. A posting below the minimum band is vetoed regardless of other scores.

### 8. Relocation & Visa Fit (0-100)
The candidate's goal is to migrate (CLAUDE.md → Mobility). Reward postings that enable it.

| Situation | Score |
|-----------|-------|
| Offers visa sponsorship **and** a relocation package | 100 |
| Offers visa sponsorship **or** relocation support | 85 |
| Fully remote (self-relocation possible later, no barrier) | 70 |
| On-site abroad, no support, but candidate willing to relocate | 45 (FLAG: relocation cost on the candidate) |
| Local on-site, no migration path | 30 |
| Explicitly no sponsorship for a role that would require it | 15 |

Look for signals: "visa sponsorship", "relocation package/assistance", "we sponsor", country-specific schemes (EU Blue Card, NZ Accredited Employer, H-1B, etc.). Absence of a statement ≠ refusal — FLAG to verify. See `docs/visa-sponsorship.md` for the per-country scheme keywords and how the portals' `visa` hint feeds this dimension.

## Output Format

Present the evaluation as:

```
## Job Fit Evaluation: [Role] at [Company]

| Dimension | Score | Notes |
|-----------|-------|-------|
| Technical Skills | XX/100 | [brief note] |
| Experience Match | XX/100 | [brief note] |
| Behavioral Fit | XX/100 | [brief note] |
| Career Alignment | XX/100 | [brief note] |
| Compensation Fit | XX/100 or FAIL | [pay vs band] |
| Relocation & Visa Fit | XX/100 | [migration path] |
| Location | PASS/FAIL | [brief note] |

**Overall Score: XX/100** (weighted average of scored dimensions)

> A **FAIL** on Location or on Compensation Fit (pay below minimum) vetoes the job regardless of the weighted score.

### Verdict: [Strong Fit / Good Fit / Moderate Fit / Weak Fit / Poor Fit]

### Key Strengths for This Role
- [bullet points]

### Gaps to Address
- [bullet points]

### Recommendation
[1-2 sentences: apply/skip/apply with caveats]

### Company Research Checklist
- [ ] Checked company website (mission, values, recent news)
- [ ] Checked review sites (Glassdoor, Jobindex, etc.)
- [ ] Checked LinkedIn for team size, recent hires, connections
- [ ] Checked media for restructuring, growth, or workplace issues
- [ ] Identified network contacts who may know the team/manager
```

## Weighting
- Technical Skills: 25%
- Experience Match: 20%
- Behavioral Fit: 10%
- Career Alignment: 20%
- Compensation Fit: 15%
- Relocation & Visa Fit: 10%

(Weights sum to 100% across the six scored dimensions. Location is pass/fail, not weighted. Dimension 6 — company Salary Benchmark — is context only, not weighted. A FAIL on Location or Compensation Fit vetoes the job regardless of the weighted total.)

## Thresholds
- **Strong Fit** (75+): Definitely apply, tailor everything
- **Good Fit** (60-74): Apply, address gaps in cover letter
- **Moderate Fit** (45-59): Consider carefully, discuss with user
- **Weak Fit** (30-44): Probably skip unless strategic reasons
- **Poor Fit** (<30): Skip

## Pre-Application: Call the Employer (Best Practice)

Before writing the application, consider whether the candidate should call the contact person listed in the posting. **Only call if there are substantive questions** - never call just to "be remembered."

### When to Suggest Calling
- The posting has unclear or ambiguous requirements
- It's unclear which competencies are essential vs. nice-to-have
- The role description is vague about day-to-day tasks
- There's a named contact person who invites questions

### Good Questions to Ask
- "What are the primary challenges in this role?"
- "How is time typically divided across the listed responsibilities?"
- "Which competencies are most critical for success in this position?"
- "What does success look like in the first 6-12 months?"

### Rules for the Call
- Prepare a 30-second "elevator pitch" about your background in case they ask
- The call's purpose is **gathering information**, not delivering a pitch
- Take notes - use what you learn to tailor the application
- Reference the conversation naturally in the cover letter ("After speaking with [name], I was especially drawn to...")
