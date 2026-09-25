export interface SearchOptions {
  category?: string
  tag?: string
  maxResults?: string
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export function writeOutput(data: unknown): void {
  process.stdout.write(JSON.stringify(data, null, 2) + "\n")
}

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

const PH_API = "https://api.producthunt.com/v2/api/graphql"

function getToken(): string | null {
  return process.env.PRODUCT_HUNT_TOKEN || null
}

function buildQuery(opts: SearchOptions): string {
  const tag = opts.tag || opts.category || "tech"
  // GraphQL query: search posts with makers
  return JSON.stringify({
    query: `{
      posts(order: VOTES, postedAfter: "${daysAgo(30)}", first: ${parseInt(opts.maxResults || "10") * 2}) {
        edges {
          node {
            id
            name
            tagline
            description
            url
            website
            createdAt
            votesCount
            makers {
              id
              name
              twitterUsername
              websiteUrl
              linkedinUrl
              profilePicture
            }
          }
        }
      }
    }`,
  })
}

function daysAgo(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString()
}

interface PHMaker {
  id: string
  name: string
  twitterUsername?: string
  websiteUrl?: string
  linkedinUrl?: string
  profilePicture?: string
}

interface PHPost {
  id: string
  name: string
  tagline?: string
  description?: string
  url?: string
  website?: string
  createdAt?: string
  votesCount?: number
  makers?: PHMaker[]
}

async function fetchPosts(opts: SearchOptions): Promise<PHPost[]> {
  const token = getToken()
  if (!token) {
    writeError("PRODUCT_HUNT_TOKEN not set in .env", "NO_TOKEN")
    return []
  }
  const payload = buildQuery(opts)
  try {
    const resp = await fetch(PH_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "User-Agent": UA,
      },
      body: payload,
    })
    if (!resp.ok) {
      const errText = await resp.text()
      writeError(`Product Hunt API error: ${resp.status} ${errText.slice(0, 200)}`, "API_ERROR")
      return []
    }
    const data = await resp.json()
    const edges = data?.data?.posts?.edges || []
    return edges.map((e: { node: PHPost }) => e.node)
  } catch (e) {
    writeError(`Product Hunt request failed: ${e instanceof Error ? e.message : String(e)}`, "REQUEST_FAILED")
    return []
  }
}

export async function runSearch(opts: SearchOptions): Promise<number> {
  const token = getToken()
  if (!token) {
    writeError("PRODUCT_HUNT_TOKEN not set in .env. Get one at: https://www.producthunt.com/v2/oauth/applications", "NO_TOKEN")
    return 1
  }

  const posts = await fetchPosts(opts)

  const results = []
  for (const post of posts) {
    const makers = post.makers || []
    for (const maker of makers) {
      results.push({
        id: post.id,
        title: `${post.name} — ${post.tagline || post.description || "startup"}`,
        company: post.name,
        location: null as string | null,
        date: post.createdAt ? post.createdAt.slice(0, 10) : null,
        url: post.url || `https://www.producthunt.com/posts/${post.id}`,
        applyEmail: null as string | null,
        emails: [] as string[],
        author: maker.name,
        text: post.description ? post.description.slice(0, 4000) : null,
        source: "producthunt-launch",
        maker_twitter: maker.twitterUsername || null,
        maker_linkedin: maker.linkedinUrl || null,
        maker_website: maker.websiteUrl || null,
        product_website: post.website || null,
        votes: post.votesCount || 0,
      })
    }
    // If no makers listed, still include the post
    if (makers.length === 0) {
      results.push({
        id: post.id,
        title: `${post.name} — ${post.tagline || post.description || "startup"}`,
        company: post.name,
        location: null as string | null,
        date: post.createdAt ? post.createdAt.slice(0, 10) : null,
        url: post.url || `https://www.producthunt.com/posts/${post.id}`,
        applyEmail: null as string | null,
        emails: [] as string[],
        author: null as string | null,
        text: post.description ? post.description.slice(0, 4000) : null,
        source: "producthunt-launch",
        maker_twitter: null,
        maker_linkedin: null,
        maker_website: null,
        product_website: post.website || null,
        votes: post.votesCount || 0,
      })
    }
    if (results.length >= parseInt(opts.maxResults || "10")) break
  }

  writeOutput({ meta: { count: results.length }, results: results.slice(0, parseInt(opts.maxResults || "10")) })
  return 0
}
