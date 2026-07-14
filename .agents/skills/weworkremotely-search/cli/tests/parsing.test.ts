import { expect, test, describe } from "bun:test"
import {
  parseItems,
  toResult,
  matchesQuery,
  detectVisa,
  isoDate,
  htmlToText,
  feedUrl,
} from "../src/helpers.ts"

const RSS = `<?xml version="1.0"?><rss><channel>
<item>
  <title>Acme: Senior Backend Developer</title>
  <link>https://weworkremotely.com/remote-jobs/acme-senior-backend-developer</link>
  <guid>https://weworkremotely.com/remote-jobs/acme-senior-backend-developer</guid>
  <pubDate>Tue, 30 Jun 2026 20:31:08 +0000</pubDate>
  <region>Anywhere in the World</region>
  <category>Back-End Programming</category>
  <description>&lt;p&gt;We offer visa sponsorship &amp;amp; relocation.&lt;/p&gt;</description>
</item>
<item>
  <title>Plain Title Without Company</title>
  <link>https://weworkremotely.com/remote-jobs/plain-title</link>
  <guid>https://weworkremotely.com/remote-jobs/plain-title</guid>
  <pubDate>Mon, 29 Jun 2026 10:00:00 +0000</pubDate>
  <region>USA Only</region>
  <category>Design</category>
  <description>&lt;p&gt;A design role.&lt;/p&gt;</description>
</item>
</channel></rss>`

describe("parseItems", () => {
  test("splits items and pulls fields", () => {
    const items = parseItems(RSS)
    expect(items.length).toBe(2)
    expect(items[0].title).toBe("Acme: Senior Backend Developer")
    expect(items[0].region).toBe("Anywhere in the World")
  })
})

describe("toResult", () => {
  test("splits 'Company: Position' and maps the contract", () => {
    const r = toResult(parseItems(RSS)[0])
    expect(r.company).toBe("Acme")
    expect(r.title).toBe("Senior Backend Developer")
    expect(r.location).toBe("Anywhere in the World")
    expect(r.date).toBe("2026-06-30")
    expect(r.remote).toBe(true)
    expect(r.visa).toBe("relocation")
    expect(r.id).toBe("acme-senior-backend-developer")
    expect(r.source).toBe("weworkremotely")
  })

  test("title without 'Company:' leaves company null", () => {
    const r = toResult(parseItems(RSS)[1])
    expect(r.company).toBeNull()
    expect(r.title).toBe("Plain Title Without Company")
  })
})

describe("matchesQuery", () => {
  test("AND semantics across fields", () => {
    const items = parseItems(RSS)
    expect(matchesQuery(items[0], "backend visa")).toBe(true)
    expect(matchesQuery(items[0], "backend python")).toBe(false)
  })
})

describe("detectVisa / isoDate / htmlToText / feedUrl", () => {
  test("helpers behave", () => {
    expect(detectVisa("we sponsor visas")).toBe("sponsor")
    expect(detectVisa("nothing here")).toBeNull()
    expect(isoDate("Tue, 30 Jun 2026 20:31:08 +0000")).toBe("2026-06-30")
    expect(isoDate("garbage")).toBeNull()
    expect(htmlToText("&lt;p&gt;hi &amp;amp; bye&lt;/p&gt;")).toContain("hi & bye")
    expect(feedUrl("front-end")).toContain("remote-front-end-programming-jobs.rss")
    expect(feedUrl("unknown-cat")).toContain("remote-programming-jobs.rss")
  })
})
