import { expect, test, describe } from "bun:test"
import {
  extractEmails,
  activityIdFromUrl,
  dateFromActivityId,
  buildFromHtml,
  buildFromText,
} from "../src/helpers.ts"

describe("extractEmails", () => {
  test("plain, obfuscated, and entity-encoded addresses", () => {
    expect(extractEmails("send CV to hr@reqroots.com now")).toEqual(["hr@reqroots.com"])
    expect(extractEmails("mail jobs [at] luftborn [dot] com")).toEqual(["jobs@luftborn.com"])
    expect(extractEmails("x hr&#64;acme.io y")).toEqual(["hr@acme.io"])
    expect(extractEmails("careers (at) foo (dot) co")).toEqual(["careers@foo.co"])
  })
  test("ignores asset filenames and infra domains", () => {
    expect(extractEmails("logo@2x.png a@licdn.com real@company.com")).toEqual(["real@company.com"])
  })
  test("dedupes case-insensitively", () => {
    expect(extractEmails("A@B.com a@b.com")).toEqual(["A@B.com"])
  })
})

describe("activity id + date", () => {
  test("extracts the id and decodes an ISO date", () => {
    const url =
      "https://www.linkedin.com/posts/luftborn_luftborn-hiring-activity-7109551926001754112-wlsG"
    const id = activityIdFromUrl(url)
    expect(id).toBe("7109551926001754112")
    const date = dateFromActivityId(id)
    expect(date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(date!.startsWith("2023")).toBe(true)
  })
  test("bad id -> null", () => {
    expect(dateFromActivityId("123")).toBeNull()
    expect(dateFromActivityId(null)).toBeNull()
  })
})

describe("buildFromHtml", () => {
  const html = `
    <meta property="og:title" content="#luftborn #hiring | Luftborn" />
    <meta property="og:description" content="We are hiring a Software Tester. Send your CV to rec@luftborn.com to apply." />
    <body>...</body>`
  const url = "https://www.linkedin.com/posts/luftborn_luftborn-hiring-activity-7109551926001754112-wlsG"
  test("maps author/company, text, email, date", () => {
    const r = buildFromHtml(html, url)
    expect(r.author).toBe("Luftborn")
    expect(r.text).toContain("Software Tester")
    expect(r.applyEmail).toBe("rec@luftborn.com")
    expect(r.id).toBe("7109551926001754112")
    expect(r.date!.startsWith("2023")).toBe(true)
    expect(r.source).toBe("linkedin-post")
  })
})

describe("buildFromText", () => {
  test("parses pasted post text for the email", () => {
    const r = buildFromText("Backend dev wanted. Apply: talent@startup.io")
    expect(r.applyEmail).toBe("talent@startup.io")
    expect(r.title.length).toBeGreaterThan(0)
  })
})
