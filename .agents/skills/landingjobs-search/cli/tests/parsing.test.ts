import { expect, test, describe } from "bun:test"
import {
  toResult,
  matchesQuery,
  detectVisa,
  companyFromUrl,
  isoDate,
  composeDescription,
  type LjRaw,
} from "../src/helpers.ts"

const sample: LjRaw = {
  id: 19066,
  title: "Senior Java Software Developer",
  url: "https://landing.jobs/at/inscale/senior-java-software-developer-in-lisbon-2025",
  remote: false,
  relocation_paid: true,
  type: "Full-time",
  currency_code: "EUR",
  gross_salary_low: 50000,
  gross_salary_high: 67000,
  published_at: "2025-02-26T09:38:38.127Z",
  tags: ["Java", "Spring Boot"],
  locations: [{ city: "Lisbon", country_code: "PT" }],
  role_description: "<p>Build services.</p>",
  main_requirements: "<ul><li>Java</li></ul>",
}

describe("toResult", () => {
  test("maps the contract; derives company from url; joins location", () => {
    const r = toResult(sample)
    expect(r.id).toBe("19066")
    expect(r.title).toBe("Senior Java Software Developer")
    expect(r.company).toBe("Inscale")
    expect(r.location).toBe("Lisbon, PT")
    expect(r.date).toBe("2025-02-26")
    expect(r.salaryLow).toBe(50000)
    expect(r.salaryHigh).toBe(67000)
    expect(r.currency).toBe("EUR")
    expect(r.visa).toBe("relocation") // relocation_paid true
    expect(r.source).toBe("landingjobs")
  })

  test("remote-only with no locations -> location 'Remote'; zero salary null", () => {
    const r = toResult({ ...sample, remote: true, locations: [], gross_salary_low: 0, gross_salary_high: 0 })
    expect(r.location).toBe("Remote")
    expect(r.salaryLow).toBeNull()
    expect(r.salaryHigh).toBeNull()
  })
})

describe("detectVisa", () => {
  test("relocation_paid wins; else text hints", () => {
    expect(detectVisa(sample)).toBe("relocation")
    expect(detectVisa({ relocation_paid: false, role_description: "we sponsor visas" })).toBe("sponsor")
    expect(detectVisa({ relocation_paid: false, role_description: "nothing" })).toBeNull()
  })
})

describe("matchesQuery", () => {
  test("AND semantics across fields", () => {
    expect(matchesQuery(sample, "java spring")).toBe(true)
    expect(matchesQuery(sample, "java rust")).toBe(false)
  })
})

describe("helpers", () => {
  test("companyFromUrl / isoDate / composeDescription", () => {
    expect(companyFromUrl("https://landing.jobs/at/some-company/role-x")).toBe("Some Company")
    expect(companyFromUrl("https://landing.jobs/no-at-segment")).toBeNull()
    expect(isoDate("2025-02-26T09:38:38.127Z")).toBe("2025-02-26")
    expect(isoDate(undefined)).toBeNull()
    const desc = composeDescription(sample)
    expect(desc).toContain("Build services.")
    expect(desc).toContain("Requirements:")
  })
})
