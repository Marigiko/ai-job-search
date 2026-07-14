import { expect, test, describe } from "bun:test"
import { parseCards, parseDetailDescription, relativeToIso, detectVisa } from "../src/helpers.ts"

const BASE = "https://ar.computrabajo.com"

const CARD = `
<article class="box_offer sel outstanding" data-id='078A0FE8E97E91FF61373E686DCF3405' id="078A0FE8E97E91FF61373E686DCF3405">
  <h2 class="fs18 fwB prB">
    <a class="js-o-link fc_base" href="/ofertas-de-trabajo/oferta-de-trabajo-de-desarrollador-java-en-san-nicolas-078A0FE8E97E91FF61373E686DCF3405#lc=x">
      Desarrollador Java SR y SSR
    </a>
  </h2>
  <p class="dFlex vm_fx fs16 fc_base mt5"><span class="fx_none mr10"><span class="fwB">4,2</span></span>
    <a class="fc_base t_ellipsis" href="https://ar.computrabajo.com/cys" target='_blank' offer-grid-article-company-url> C&amp;S inform&#xE1;tica s.a. </a>
  </p>
  <p class="fs16 fc_base mt5"><span class="mr10"> San Nicol&#xE1;s, Capital Federal </span></p>
  <div class="fs13 mt15"><span class="dIB mr10"><span class="icon i_home_office"></span> Presencial y remoto </span></div>
  <p class="fs13 fc_aux mt15"> Hace 2 d&#xED;as </p>
</article>`

describe("parseCards", () => {
  const cards = parseCards(CARD, BASE)
  test("extracts one card with all fields", () => {
    expect(cards.length).toBe(1)
    const c = cards[0]
    expect(c.id).toBe("078A0FE8E97E91FF61373E686DCF3405")
    expect(c.title).toBe("Desarrollador Java SR y SSR")
    expect(c.company).toBe("C&S informática s.a.")
    expect(c.location).toBe("San Nicolás, Capital Federal")
    expect(c.url).toBe(BASE + "/ofertas-de-trabajo/oferta-de-trabajo-de-desarrollador-java-en-san-nicolas-078A0FE8E97E91FF61373E686DCF3405")
    expect(c.remote).toBe(true) // "Presencial y remoto"
    expect(c.posted).toBe("Hace 2 días")
    expect(c.source).toBe("computrabajo")
  })
})

describe("parseDetailDescription", () => {
  test("pulls text under the description header", () => {
    const html = `<h3 class="fwB">Descripción de la oferta</h3><div class="mbB"><span class="tag">A convenir</span></div><p class="mbB">Buscamos Java Semi Senior en CABA.</p><h3>Otra seccion</h3>`
    const d = parseDetailDescription(html)
    expect(d).toContain("Buscamos Java Semi Senior")
  })
})

describe("relativeToIso / detectVisa", () => {
  test("relative dates and visa hints", () => {
    expect(relativeToIso("Hace 1 hora")).toBe(new Date().toISOString().slice(0, 10))
    expect(relativeToIso("ayer")).toBe(new Date(Date.now() - 86400000).toISOString().slice(0, 10))
    expect(relativeToIso("Hace 3 días")).toBe(new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10))
    expect(relativeToIso("desconocido")).toBeNull()
    expect(detectVisa("ofrecemos relocación")).toBe("relocation")
    expect(detectVisa("nada")).toBeNull()
  })
})
