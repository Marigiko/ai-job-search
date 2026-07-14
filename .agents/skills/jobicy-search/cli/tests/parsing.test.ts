import { expect, test, describe } from "bun:test"
import {
  toResult,
  detectVisa,
  isoDate,
  extractJobs,
  monthlyEstimate,
  htmlToText,
  type JobicyRaw,
} from "../src/helpers.ts"

const sample: JobicyRaw = {
  id: 149243,
  url: "https://jobicy.com/jobs/149243-senior-backend-developer",
  jobSlug: "senior-backend-developer",
  jobTitle: "Senior Backend Developer",
  companyName: "Mindrift",
  jobIndustry: ["Software Engineering"],
  jobType: ["Full-Time"],
  jobGeo: "USA",
  jobLevel: "Senior",
  jobExcerpt: "Great role.",
  jobDescription: "<p>We offer visa sponsorship.</p>",
  pubDate: "2026-07-13T14:26:05+00:00",
  salaryMin: 120000,
  salaryMax: 180000,
  salaryCurrency: "USD",
  salaryPeriod: "yearly",
}

describe("toResult", () => {
  test("maps the contract; remote always true; salary bands", () => {
    const r = toResult(sample)
    expect(r.id).toBe("149243")
    expect(r.title).toBe("Senior Backend Developer")
    expect(r.company).toBe("Mindrift")
    expect(r.location).toBe("USA")
    expect(r.date).toBe("2026-07-13")
    expect(r.remote).toBe(true)
    expect(r.visa).toBe("sponsor")
    expect(r.salaryMin).toBe(120000)
    expect(r.salaryMax).toBe(180000)
    expect(r.salaryCurrency).toBe("USD")
    expect(r.level).toBe("Senior")
    expect(r.source).toBe("jobicy")
  })
})

describe("monthlyEstimate", () => {
  test("annual/12; monthly as-is; null when unknown", () => {
    expect(monthlyEstimate(toResult(sample))).toBe(15000) // 180000/12
    expect(monthlyEstimate(toResult({ ...sample, salaryPeriod: "monthly", salaryMax: 4000 }))).toBe(4000)
    expect(monthlyEstimate(toResult({ ...sample, salaryMax: 0 }))).toBeNull()
  })
})

describe("helpers", () => {
  test("extractJobs / detectVisa / isoDate / htmlToText", () => {
    expect(extractJobs({ jobs: [sample] }).length).toBe(1)
    expect(extractJobs({}).length).toBe(0)
    expect(detectVisa({ jobDescription: "relocation package" })).toBe("relocation")
    expect(detectVisa({ jobDescription: "none" })).toBeNull()
    expect(isoDate("2026-07-13T14:26:05+00:00")).toBe("2026-07-13")
    expect(htmlToText("<p>a &amp; b</p>")).toContain("a & b")
  })
})
