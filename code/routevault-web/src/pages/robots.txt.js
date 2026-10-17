export function GET() {
  return new Response('User-agent: *\nAllow: /\nSitemap: https://routevault.ai/sitemap.xml\n', { headers: { 'content-type': 'text/plain' } });
}
