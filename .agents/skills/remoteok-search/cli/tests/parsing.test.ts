import { expect, test, describe } from "bun:test"
import {
  toResult,
  matchesQuery,
  detectVisa,
  isJob,
  isoDate,
  htmlToText,
  type RemoteOkRaw,
} from "../src/helpers.ts"

const legal = { last_updated: 1784030675, legal: "API Terms of Service: link back…" }

const sample: RemoteOkRaw = {
  id: "1134769",
  slug: "remote-backend-developer-acme-1134769",
  epoch: 1783951039,
  date: "2026-07-13T13:57:19+00:00",
  company: "Acme",
  position: "Backend Developer",
  tags: ["python", "backend", "visa"],
  description: "<p>Great role. Relocation available.</p>",
  location: "Worldwide",
  url: "https://remoteok.com/remote-jobs/remote-backend-developer-acme-1134769",
  apply_url: "https://remoteok.com/remote-jobs/remote-backend-developer-acme-1134769",
  salary_min: 60000,
  salary_max: 90000,
}

describe("isJob", () => {
  test("rejects the legal/metadata header, accepts real jobs", () => {
    expect(isJob(legal)).toBe(false)
    expect(isJob(sample)).toBe(true)
    expect(isJob({})).toBe(false)
  })
})

describe("toResult", () => {
  test("maps to the portal contract with required fields", () => {
    const r = toResult(sample)
    expect(r.id).toBe("1134769")
    expect(r.title).toBe("Backend Developer")
    expect(r.company).toBe("Acme")
    expect(r.date).toBe("2026-07-13")
    expect(r.remote).toBe(true)
    expect(r.salaryMin).toBe(60000)
    expect(r.salaryMax).toBe(90000)
    expect(r.source).toBe("remoteok")
  })

  test("zero salaries normalize to null; missing company nulls", () => {
    const r = toResult({ ...sample, salary_min: 0, salary_max: 0, company: "" })
    expect(r.salaryMin).toBeNull()
    expect(r.salaryMax).toBeNull()
    expect(r.company).toBeNull()
  })
})

describe("detectVisa", () => {
  test("flags relocation and sponsorship", () => {
    expect(detectVisa(sample)).toBe("relocation")
    expect(detectVisa({ ...sample, description: "we sponsor visas", tags: [] })).toBe("sponsor")
    expect(detectVisa({ ...sample, description: "nothing", tags: [] })).toBeNull()
  })
})

describe("matchesQuery", () => {
  test("AND semantics", () => {
    expect(matchesQuery(sample, "backend python")).toBe(true)
    expect(matchesQuery(sample, "backend rust")).toBe(false)
  })
})

describe("isoDate", () => {
  test("prefers ISO date, falls back to epoch", () => {
    expect(isoDate(sample)).toBe("2026-07-13")
    expect(isoDate({ epoch: 1700000000 })).toBe("2023-11-14")
    expect(isoDate({})).toBeNull()
  })
})

describe("htmlToText", () => {
  test("strips tags", () => {
    expect(htmlToText("<p>hello &amp; bye</p>")).toContain("hello & bye")
  })
})
