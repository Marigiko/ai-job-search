import { expect, test, describe } from "bun:test"
import { toResult, detectVisa, isoDate, extractJobs, htmlToText, type RemotiveRaw } from "../src/helpers.ts"

const sample: RemotiveRaw = {
  id: 2091062,
  url: "https://remotive.com/remote-jobs/software-development/senior-product-engineer-2091062",
  title: "Senior Product Engineer",
  company_name: "Clipster",
  category: "Software Development",
  tags: ["fullstack", "react"],
  job_type: "full_time",
  publication_date: "2026-07-13T07:05:10",
  candidate_required_location: "Europe, UK",
  salary: "$90k - $120k",
  description: "<p>We offer visa sponsorship.</p>",
}

describe("toResult", () => {
  test("maps the contract; remote always true", () => {
    const r = toResult(sample)
    expect(r.id).toBe("2091062")
    expect(r.title).toBe("Senior Product Engineer")
    expect(r.company).toBe("Clipster")
    expect(r.location).toBe("Europe, UK")
    expect(r.date).toBe("2026-07-13")
    expect(r.remote).toBe(true)
    expect(r.visa).toBe("sponsor")
    expect(r.salaryText).toBe("$90k - $120k")
    expect(r.source).toBe("remotive")
  })

  test("empty salary -> null", () => {
    expect(toResult({ ...sample, salary: "" }).salaryText).toBeNull()
  })
})

describe("helpers", () => {
  test("extractJobs skips meta keys", () => {
    expect(extractJobs({ "0-legal-notice": "x", jobs: [sample] }).length).toBe(1)
    expect(extractJobs({ nope: 1 }).length).toBe(0)
  })
  test("detectVisa / isoDate / htmlToText", () => {
    expect(detectVisa({ description: "relocation package" })).toBe("relocation")
    expect(detectVisa({ description: "none" })).toBeNull()
    expect(isoDate("2026-07-13T07:05:10")).toBe("2026-07-13")
    expect(isoDate(undefined)).toBeNull()
    expect(htmlToText("<p>hi &amp; bye</p>")).toContain("hi & bye")
  })
})
