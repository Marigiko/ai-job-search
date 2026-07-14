import { expect, test, describe } from "bun:test"
import {
  toResult,
  matchesQuery,
  detectVisa,
  htmlToText,
  isoDate,
  type ArbeitnowRaw,
} from "../src/helpers.ts"

const sample: ArbeitnowRaw = {
  slug: "backend-developer-remote-berlin-123",
  company_name: "Acme GmbH",
  title: "Backend Developer (Remote)",
  description: "<p>We offer <strong>visa sponsorship</strong> and relocation support.</p><ul><li>Python</li></ul>",
  remote: true,
  url: "https://www.arbeitnow.com/jobs/companies/acme-gmbh/backend-developer-remote-berlin-123",
  tags: ["Python", "Backend"],
  job_types: ["Full Time"],
  location: "Berlin",
  created_at: 1_700_000_000,
}

describe("toResult", () => {
  test("maps to the portal contract with all required fields", () => {
    const r = toResult(sample)
    expect(r.id).toBe(sample.slug)
    expect(r.title).toBe(sample.title)
    expect(r.company).toBe("Acme GmbH")
    expect(r.location).toBe("Berlin")
    expect(r.url).toBe(sample.url)
    expect(r.date).toBe("2023-11-14")
    expect(r.remote).toBe(true)
    expect(r.source).toBe("arbeitnow")
  })

  test("nulls missing values rather than omitting them", () => {
    const r = toResult({ ...sample, company_name: "", location: "" })
    expect(r.company).toBeNull()
    expect(r.location).toBeNull()
  })
})

describe("detectVisa", () => {
  test("flags relocation and sponsorship from text", () => {
    expect(detectVisa(sample)).toBe("relocation")
    expect(detectVisa({ ...sample, description: "We sponsor a work visa." })).toBe("sponsor")
    expect(detectVisa({ ...sample, description: "No perks listed.", tags: [] })).toBeNull()
  })
})

describe("matchesQuery", () => {
  test("AND semantics across title/company/tags/description", () => {
    expect(matchesQuery(sample, "backend python")).toBe(true)
    expect(matchesQuery(sample, "backend java")).toBe(false)
    expect(matchesQuery(sample, undefined)).toBe(true)
  })
})

describe("htmlToText", () => {
  test("strips tags and decodes entities, keeping breaks", () => {
    const t = htmlToText("<p>Line&nbsp;one</p><li>bullet &amp; more</li>")
    expect(t).toContain("Line one")
    expect(t).toContain("bullet & more")
    expect(t).not.toContain("<")
  })
})

describe("isoDate", () => {
  test("converts unix seconds; guards bad input", () => {
    expect(isoDate(1_700_000_000)).toBe("2023-11-14")
    expect(isoDate(0)).toBeNull()
    expect(isoDate(NaN)).toBeNull()
  })
})
