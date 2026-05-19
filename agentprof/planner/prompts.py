"""Prompt templates for the LLM planner.

The planner prompt must give the LLM:
  1. Its role and hard constraints (no optimization)
  2. The profiling spec (what we're trying to find out)
  3. Current breakdown (where time went)
  4. Resource health snapshot (any obvious symptoms)
  5. Observer registry summary (what tools are available)
  6. Diagnostic questions (what we want to answer)
  7. Known unknowns (what we already know we don't know)
  8. Budget remaining

The LLM must output a structured ObservationPlan (JSON).

Milestone 3 implementation target.
"""

SYSTEM_PROMPT = """\
You are AgentProf's observation planner. Your job is to decide the next profiling step.

HARD CONSTRAINTS — you must never suggest:
- change_concurrency, change_arrival_rate, toggle_cache, set_timeout, set_quota, apply_patch
- Modifying the target agent's prompt, planner, or configuration
- Any action that optimizes or changes the system under test

You may only select observers from the provided observer registry.
You must output a valid ObservationPlan JSON object.
"""

PLAN_REQUEST_TEMPLATE = """\
## Profiling Spec
{spec_summary}

## Current Breakdown
{breakdown}

## Resource Health
{resource_health}

## Available Observers
{observer_registry_summary}

## Diagnostic Questions
{diagnostic_questions}

## Known Unknowns
{known_unknowns}

## Budget Remaining
{budget}

## Task
Select the next observation plan. Output JSON matching the ObservationPlan schema.
Required fields: plan_id, question_id, observers, scope, mode, rationale, expected_evidence.
"""
