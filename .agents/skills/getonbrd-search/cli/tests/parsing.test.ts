import { expect, test, describe } from "bun:test"
import {
  toResult,
  detectVisa,
  isoDate,
  htmlToText,
  seniorityLabel,
  type GobJob,
} from "../src/helpers.ts"

const job: GobJob = {
  id: "senior-backend-developer-acme-santiago-e811",
  attributes: {
    title: "Senior Backend Developer",
    description: "<p>Great role with <strong>relocation</strong> support.</p><ul><li>Python</li></ul>",
    remote: true,
    remote_modality: "remote_local",
    countries: ["Remote"],
    min_salary: 2700,
    max_salary: 2900,
    published_at: 1700000000,
    category_name: "Programming",
    seniority: { data: { id: 4, type: "seniority" } },
    company: { data: { id: 19970, type: "company" } },
  },
  links: { public_url: "https://www.getonbrd.com/jobs/senior-backend-developer-acme-santiago-e811" },
}

const seniorityMap = new Map<string, string>([
  ["1", "Sin experiencia"],
  ["4", "Senior"],
])

describe("toResult", () => {
  test("maps the contract with monthly-USD salary and resolved labels", () => {
    const r = toResult(job, "Acme Inc", seniorityLabel(job.attributes!.seniority, seniorityMap))
    expect(r.id).toBe(job.id)
    expect(r.title).toBe("Senior Backend Developer")
    expect(r.company).toBe("Acme Inc")
    expect(r.location).toBe("Remote")
    expect(r.date).toBe("2023-11-14")
    expect(r.url).toBe(job.links!.public_url)
    expect(r.remote).toBe(true)
    expect(r.salaryMin).toBe(2700)
    expect(r.salaryMax).toBe(2900)
    expect(r.seniority).toBe("Senior")
    expect(r.category).toBe("Programming")
    expect(r.source).toBe("getonbrd")
  })

  test("unresolved company/seniority null; zero salary null", () => {
    const bare: GobJob = { id: "x", attributes: { title: "T", min_salary: 0, max_salary: 0 } }
    const r = toResult(bare, null, null)
    expect(r.company).toBeNull()
    expect(r.seniority).toBeNull()
    expect(r.salaryMin).toBeNull()
    expect(r.salaryMax).toBeNull()
    expect(r.location).toBeNull()
    expect(r.url).toContain("/jobs/x")
  })
})

describe("detectVisa", () => {
  test("flags relocation / sponsorship from attributes text", () => {
    expect(detectVisa(job.attributes!)).toBe("relocation")
    expect(detectVisa({ description: "we sponsor visas" })).toBe("sponsor")
    expect(detectVisa({ description: "nothing" })).toBeNull()
  })
})

describe("seniorityLabel", () => {
  test("resolves via the catalog map, null when missing", () => {
    expect(seniorityLabel({ data: { id: 4 } }, seniorityMap)).toBe("Senior")
    expect(seniorityLabel({ data: { id: 99 } }, seniorityMap)).toBeNull()
    expect(seniorityLabel(undefined, seniorityMap)).toBeNull()
  })
})

describe("isoDate / htmlToText", () => {
  test("helpers behave", () => {
    expect(isoDate(1700000000)).toBe("2023-11-14")
    expect(isoDate(undefined)).toBeNull()
    expect(htmlToText("<p>hi &amp; bye</p>")).toContain("hi & bye")
  })
})
