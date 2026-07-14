import { expect, test, describe } from "bun:test"
import { toResult, matchesQuery, detectVisa, isoDate, htmlToText, type MuseRaw } from "../src/helpers.ts"

const sample: MuseRaw = {
  id: 21610367,
  name: "Senior Backend Engineer",
  company: { name: "Bank of America" },
  locations: [{ name: "New York, NY" }, { name: "Jersey City, NJ" }],
  categories: [{ name: "Software Engineering" }],
  levels: [{ name: "Senior Level" }],
  publication_date: "2026-07-07T19:16:09Z",
  contents: "<p>Great role. Visa sponsorship available.</p>",
  refs: { landing_page: "https://www.themuse.com/jobs/bankofamerica/senior-backend-engineer-b39f5b" },
}

const remoteSample: MuseRaw = { ...sample, locations: [{ name: "Flexible / Remote" }] }

describe("toResult", () => {
  test("maps the contract; joins locations; picks first level/category", () => {
    const r = toResult(sample)
    expect(r.id).toBe("21610367")
    expect(r.title).toBe("Senior Backend Engineer")
    expect(r.company).toBe("Bank of America")
    expect(r.location).toBe("New York, NY | Jersey City, NJ")
    expect(r.date).toBe("2026-07-07")
    expect(r.url).toContain("themuse.com/jobs")
    expect(r.level).toBe("Senior Level")
    expect(r.category).toBe("Software Engineering")
    expect(r.visa).toBe("sponsor")
    expect(r.remote).toBe(false)
    expect(r.source).toBe("themuse")
  })

  test("Flexible / Remote location marks remote", () => {
    expect(toResult(remoteSample).remote).toBe(true)
  })
})

describe("matchesQuery / detectVisa / isoDate / htmlToText", () => {
  test("behaviors", () => {
    expect(matchesQuery(sample, "backend engineer")).toBe(true)
    expect(matchesQuery(sample, "backend rust")).toBe(false)
    expect(detectVisa({ contents: "relocation package" })).toBe("relocation")
    expect(detectVisa({ contents: "nothing" })).toBeNull()
    expect(isoDate("2026-07-07T19:16:09Z")).toBe("2026-07-07")
    expect(htmlToText("<p>a &amp; b</p>")).toContain("a & b")
  })
})
