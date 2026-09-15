# Tasks

## 2026-09-15 Gemini model migration

- [x] Audit current model settings and provider lifecycle documentation.
- [x] Receive implementation and pull-request approval from Arjun.
- [x] Replace the unavailable OpenRouter Gemini Pro endpoint while preserving public aliases and historical evaluation results.
- [x] Run relevant tests and bounded provider smoke checks.
- [x] Review the diff and prepare the pull request.

### Review

The OpenRouter Gemini 3 Pro endpoint is no longer present in the model catalog. Preserve the existing gemini-3-pro application alias while routing new requests to google/gemini-3.1-pro-preview. Update the corresponding fallback price key and document the mapping. Historical evaluation results remain unchanged.

The application alias and exact new provider ID resolve correctly; the fallback cost calculation matches the standard catalog rates. A live request to the replacement endpoint returned the expected answer. Syntax and diff checks passed.

Gemini 3.1 Pro is a currently available preview endpoint. This fixes its OpenRouter model mapping; the Google Cloud 2.5 retirement notice has a separate provider lifecycle.
