const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

const YC_JOB_RE = /https?:\/\/www\.workatastartup\.com\/jobs\/[^\s"'<>]+/g;
const YC_COMPANY_RE = /https?:\/\/www\.workatastartup\.com\/companies\/[^\s"'<>]+/g;

function buildQuery(role, remote, batch) {
  const parts = [`site:workatastartup.com/jobs`, `"${role}"`];
  if (remote) parts.push("remote");
  if (batch) parts.push(`"${batch}"`);
  return parts.join(" ");
}

async function searchDuckDuckGo(query, maxResults) {
  const encoded = encodeURIComponent(query);
  const url = `https://html.duckduckgo.com/html/?q=${encoded}`;
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html" },
    });
    if (!resp.ok) return [];
    const html = await resp.text();
    const links = new Set();
    const jobMatches = html.match(YC_JOB_RE) || [];
    const companyMatches = html.match(YC_COMPANY_RE) || [];
    for (const m of [...jobMatches, ...companyMatches]) {
      links.add(m);
    }
    const redirectMatches = html.match(/uddg=([^&]+)/g) || [];
    for (const rm of redirectMatches) {
      const decoded = decodeURIComponent(rm.replace("uddg=", ""));
      if (decoded.includes("workatastartup.com")) {
        links.add(decoded);
      }
    }
    return [...links].slice(0, maxResults);
  } catch (e) {
    console.error("DuckDuckGo error:", e.message);
    return [];
  }
}

async function searchBing(query, maxResults) {
  const encoded = encodeURIComponent(query);
  const url = `https://www.bing.com/search?q=${encoded}&count=${maxResults * 2}`;
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html" },
    });
    if (!resp.ok) return [];
    const html = await resp.text();
    const links = new Set();
    const jobMatches = html.match(YC_JOB_RE) || [];
    const companyMatches = html.match(YC_COMPANY_RE) || [];
    for (const m of [...jobMatches, ...companyMatches]) {
      links.add(m);
    }
    return [...links].slice(0, maxResults);
  } catch (e) {
    console.error("Bing error:", e.message);
    return [];
  }
}

function parseJobSlug(url) {
  const slug = url.split("/").pop() || "";
  const decoded = slug.replace(/-/g, " ");
  const atMatch = decoded.match(/(.+?)\s+at\s+(.+)/i);
  if (atMatch) {
    return { title: atMatch[1].trim(), company: atMatch[2].trim() };
  }
  return { title: decoded, company: "" };
}

async function runSearch({ role, remote, batch, maxResults, engine }) {
  maxResults = parseInt(maxResults || "10", 10);
  const query = buildQuery(role, remote, batch);
  console.error(`Query: ${query} | Engine: ${engine || "duckduckgo->bing"}`);

  let urls = [];
  if (engine === "google" || !engine) {
    urls = await searchDuckDuckGo(query, maxResults);
  }
  if (urls.length === 0) {
    urls = await searchBing(query, maxResults);
  }
  if (urls.length === 0) {
    urls = await searchDuckDuckGo(query, maxResults);
  }

  const results = urls.map((url) => {
    const { title, company } = parseJobSlug(url);
    return {
      id: url.split("/").pop() || url,
      title: title || "YC Startup Job",
      company: company || "",
      location: null,
      date: null,
      url: url.split("?")[0],
      applyEmail: null,
      emails: [],
      author: null,
      text: null,
      source: "yc-startup-job",
    };
  });

  console.log(JSON.stringify({ meta: { count: results.length, query, engine: engine || "duckduckgo->bing" }, results }, null, 2));
  return 0;
}

// Parse args
const args = process.argv.slice(2);
const opts = {};
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith("--") && args[i + 1] && !args[i + 1].startsWith("--")) {
    opts[arg.slice(2)] = args[++i];
  } else if (arg === "--remote") {
    opts.remote = "true";
  }
}

runSearch({
  role: opts.role,
  remote: opts.remote === "true",
  batch: opts.batch,
  maxResults: opts.maxResults,
  engine: opts.engine,
});
