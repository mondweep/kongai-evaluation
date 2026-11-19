# Validation plan

Each claim is graded on four levels of evidence: claimed (marketing), documented (technical docs), demonstrated (our own test passes), attested (an independent party vouches for it). The living version is at https://claude.ai/artifact/FQJeKYkXHUhksYZXqTdK1s

## Test bed
- Serverless control plane "serverless-api-gateway-demo" (EU).
- Mock OpenAI-compatible upstream (on the gateway itself) for most tests. Real model (Gemini free tier) only for C4, C5 and smoke tests.
- Two or more test consumers with API keys. Everything is tagged `validation`.
- Step 0: check which AI plugins the serverless gateway accepts.

## 1. Data exposure
Features: AI Sanitizer, AI Prompt Guard, AI Semantic Prompt Guard, AI Semantic Response Guard, cloud guardrails.
- D1 PII redaction: 50 prompts seeded with fake UK PII, compare sent vs received. Pass: no card or NI numbers reach the upstream, and at least 95% of items are redacted.
- D2 Restore: the client sees the original values, the provider never does.
- D3 Evasion: obfuscated PII. Report the rate.
- D4 Logs: no raw PII stored unless payload logging is turned on.

## 2. Uncontrolled costs
Features: AI Rate Limiting Advanced (tokens or cost), consumer group budgets, model cost settings, semantic cache, prompt compressor.
- C1 Token limit, sequential. Pass: 429 at the limit, overshoot no more than one request.
- C2 Concurrency leak: measure the overshoot from a burst of 10.
- C3 Cost limit blocks at the configured spend.
- C4 Kong's tokens and cost vs the provider's usage. Pass: tokens within 1%, cost within 5%.
- C5 Semantic cache hits avoid provider tokens.

## 3. Compliance and audit
- A1 Admin audit trail shows who, when, what and from where, and can't be edited.
- A2 Every request traceable to a consumer, model, token count and cost.
- A3 Data residency stays in the EU.
- A4 Retention and SIEM export.

## 4. Operational risk
- O1 Failover with one broken target. Pass: 100% client success.
- O2 Provider 429s are retried or failed over.
- O3 Gateway overhead under 50 ms at p95.
- O4 Failures are visible in Konnect within minutes.

## 5. Security
- S1 No key or a revoked key gets 401. S2 ACL breach gets 403. S3 The provider key never leaks.
- S4 About 100 injection prompts plus benign prompts: report the block rate and false-positive rate.

## Independent evidence
Kong trust centre (SOC 2 Type II, under NDA), DPA and sub-processors, open-source plugin code, CVE history, peer reviews.
