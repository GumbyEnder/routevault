"""
Ingest per-provider list prices from models.dev (community-maintained, official sources).
One row per (provider, model). Prices are USD per million tokens.
"""
import json
import urllib.request

SOURCE_URL = "https://models.dev/api.json"
USER_AGENT = "RouteVault/1.0 (https://routevault.ai)"

# Top 60 providers on models.dev by priced-model count (2026-10-17), unioned with
# the first-party inference providers we always want regardless of row count.
FOCUS_PROVIDERS = {
    # top 60 by models.dev priced rows
    "nano-gpt", "llmgateway-providers", "kilo", "openrouter", "edenai",
    "vercel", "llmgateway", "merge-gateway", "amazon-bedrock", "requesty",
    "aimlapi", "ofox", "aihubmix", "opencode", "302ai", "zenmux", "venice",
    "pioneer", "orcarouter", "abacus", "nvidia", "cortecs", "poe", "azure",
    "digitalocean", "alibaba-cn", "helicone", "azure-cognitive-services",
    "novita-ai", "huggingface", "tempr", "impossibl", "deepinfra",
    "commandcode", "crossmodel", "prime", "kenari", "empiriolabs", "jiekou",
    "google-vertex", "cloudflare-ai-gateway", "alibaba", "siliconflow",
    "neon", "opper", "nearai", "openai", "sap-ai-core", "siliconflow-cn",
    "standardcompute", "greenpt", "mistral", "fastrouter", "vivgrid",
    "github-copilot", "google", "llmtr", "opencode-go", "togetherai",
    "databricks",
    # first-party providers kept regardless of models.dev rank
    "anthropic", "xai", "deepseek", "groq", "cohere", "perplexity",
    "ollama-cloud", "fireworks-ai", "cerebras", "together-ai",
}


def fetch() -> dict:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def extract(data: dict) -> list[dict]:
    rows = []
    for provider, pv in data.items():
        models = pv.get("models") or {}
        for mid, m in models.items():
            cost = m.get("cost") or {}
            pin, pout = cost.get("input"), cost.get("output")
            if pin is None or pout is None:
                continue
            rows.append({
                "provider": provider,
                "model_id": m.get("id") or mid,
                "model_name": m.get("name") or mid,
                "input_per_m": round(float(pin), 4),
                "output_per_m": round(float(pout), 4),
                "cache_read_per_m": (round(float(cost["cache_read"]), 4)
                                     if cost.get("cache_read") is not None else None),
                "context_k": int(m["limit"]["context"] / 1000) if m.get("limit", {}).get("context") else None,
                "source_url": pv.get("docs") or pv.get("api") or "",
            })
    return rows


def rows_for_providers(data: dict, providers: set[str] | None = None) -> list[dict]:
    rows = extract(data)
    if providers:
        rows = [r for r in rows if r["provider"] in providers]
    return rows


if __name__ == "__main__":
    data = fetch()
    rows = extract(data)
    print(json.dumps(rows[:5], indent=1))
    print("total priced rows:", len(rows))
