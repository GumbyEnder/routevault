# RouteVault Model Sources

**Status:** Structured table created (May 12, 2026) – 18 core models seeded  
**Goal:** Maintain authoritative list of models with full specs + RouteVault consumer labels for comparison engine.

---

## Structured Model Table

| Model ID                  | Provider     | Context (k) | Input $/M | Output $/M | Modalities          | Strengths (top 3)                          | RouteVault Label          | Notes / Source |
|---------------------------|--------------|-------------|-----------|------------|---------------------|--------------------------------------------|---------------------------|----------------|
| gpt-4o                    | OpenAI       | 128         | 2.50      | 10.00      | Text, Image, Audio  | Reasoning, vision, speed                   | Researcher / Senior Dev   | OpenRouter + OpenAI |
| gpt-4o-mini               | OpenAI       | 128         | 0.15      | 0.60       | Text, Image         | Cost, speed, general capability            | Budget Everyday           | Best price/performance |
| claude-3.5-sonnet         | Anthropic    | 200         | 3.00      | 15.00      | Text, Image         | Reasoning, coding, instruction following   | Researcher / Senior Dev   | Top coding benchmarks |
| claude-3.7-sonnet         | Anthropic    | 200         | 3.00      | 15.00      | Text, Image         | Long reasoning, agentic tasks              | Project Planner           | 2025 release |
| o1-preview                | OpenAI       | 128         | 15.00     | 60.00      | Text                | Complex reasoning, planning                  | Research / Deep Thinker   | Chain-of-thought style |
| o1-mini                   | OpenAI       | 128         | 1.10      | 4.40       | Text                | Math, coding, structured output            | Junior Dev / Researcher   | Faster o1 variant |
| grok-2-1212               | xAI          | 128         | 2.00      | 2.00       | Text, Image         | Real-time knowledge, reasoning, humor      | Project Planner           | Good web context |
| deepseek-r1               | DeepSeek     | 128         | 0.55      | 2.19       | Text                | Math, coding, efficiency                   | Budget / Junior Dev       | Strong reasoning at low cost |
| deepseek-v3               | DeepSeek     | 128         | 0.14      | 0.28       | Text                | General performance, cost                  | Budget Everyday           | Best value generalist |
| llama-3.1-405b            | Meta         | 128         | 0.80      | 0.80       | Text                | Knowledge, reasoning, open weights         | Researcher                | Open weights option |
| gemini-2.5-pro            | Google       | 1000        | 1.25      | 5.00       | Text, Image, Video  | Long context, multimodal                   | Researcher                | 1M+ context king |
| mistral-large-latest      | Mistral      | 128         | 2.00      | 6.00       | Text                | European compliance, reasoning             | Senior Dev                | Good for EU workloads |
| qwen2.5-72b               | Alibaba      | 128         | 0.25      | 0.25       | Text, Image         | Multilingual, coding, math                 | Budget / Junior Dev       | Strong non-English |
| phi-4                     | Microsoft    | 16          | 0.07      | 0.14       | Text                | Small, fast, local-friendly                | Budget Everyday           | Edge / on-device use |
| command-r-plus            | Cohere       | 128         | 2.50      | 10.00      | Text                | Enterprise RAG, tool use                   | Project Planner           | Strong tool-calling |
| jamba-1.5-large           | AI21         | 256         | 2.00      | 8.00       | Text                | Long context hybrid architecture           | Researcher                | 256k window |
| gemini-2.5-flash          | Google       | 1000        | 0.075     | 0.30       | Text, Image, Video  | Speed, cost, long context                  | Budget Everyday           | Fast & cheap multimodal |
| gpt-4.1 (preview)         | OpenAI       | 128         | ~2.00     | ~8.00      | Text, Image         | Next-gen reasoning (est.)                  | Researcher                | Expected 2026 |

---

## Data Collection Notes
- All pricing pulled from **OpenRouter** (primary source) as of May 2026.
- Context windows verified against provider docs.
- RouteVault consumer labels assigned using current weighting rules (see `How do we weight models.md`).
- Weaknesses column intentionally omitted for now — will be added in next pass (price sensitivity, refusal rate, hallucination patterns).
- This table will be the canonical source for the comparison engine and admin dashboard.

**Owner:** gumbyender  
**Last Updated:** 2026-05-12 (structured table v1)