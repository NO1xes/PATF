# OpenTelemetry Adapter (baseline a)

Wraps OpenTelemetry trace data (OTLP format) into AgentProf's `AgentEvent` format.

## Status: stub (not yet implemented)

## Rationale

OpenTelemetry is the de-facto standard for distributed tracing.
Comparing AgentProf's observer output against OTel for the same agent run
demonstrates what additional information AgentProf provides (resource layer,
methodology-driven drill-down, LLM-generated ObservationPlan).
