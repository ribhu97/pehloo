<!--
Pull Request Template — optimized for humans and AI agents reviewing this PR.

Guidance:
- Fill every section. If a section truly does not apply, write "N/A — <reason>".
- Keep prose tight. Bullet points > paragraphs.
- Link issues, ADRs, docs, and prior PRs by URL or `#123`.
- Agents: treat every section as load-bearing context. Do not skip headings.
-->

## Summary

<!-- One or two sentences: WHAT changed and WHY. Not HOW. -->

## Motivation & Context

<!--
Why does this change exist? What problem does it solve?
- Link the issue: Closes #
- Link the ADR or design doc (if any):
- If this is a bug fix: what was the user-visible symptom and the root cause?
-->

## Type of Change

<!-- Check all that apply. -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Refactor (no behavior change)
- [ ] Performance improvement
- [ ] Documentation only
- [ ] Build / CI / tooling
- [ ] Dependency update
- [ ] Revert

## Scope of Change

<!--
List the components, modules, or layers touched. This helps reviewers (and agents)
locate the blast radius without re-reading the diff.

Example for this codebase:
- `pehloo/domain/entities/observation.py` — added `delight_score` field
- `pehloo/adapters/browser/browser_use_agent.py` — populate new field from agent output
- `tests/unit/domain/test_observation.py` — coverage for new field
-->

## How It Works

<!--
Brief technical explanation of the approach. Call out:
- Key design decisions and trade-offs considered
- Anything non-obvious in the diff (workarounds, ordering constraints, invariants)
- Alternatives rejected and why
-->

## Testing

<!--
What you did to convince yourself this works. Be specific.
-->

- [ ] Unit tests added / updated
- [ ] Integration tests added / updated
- [ ] Manually verified locally
- [ ] Tested edge cases: <!-- list them -->

**Reproduction steps for reviewers:**

```bash
# Commands a reviewer can paste to verify
```

**Expected vs actual behavior:**

<!-- Before/after, or screenshots/recordings for UI. -->

## Breaking Changes & Migration

<!--
If this is a breaking change:
- What breaks?
- Who is affected (users, downstream callers, CLI consumers)?
- Migration steps:
If not, write: "None."
-->

## Risk Assessment

<!--
- Blast radius: low / medium / high
- Rollback plan: how do we revert if this misbehaves in prod?
- Feature flag / gate: yes / no (link)
- Data migration: yes / no (reversible?)
-->

## Checklist

- [ ] Code follows the project's architecture rules (hexagonal layering — see `CLAUDE.md`)
- [ ] No new framework imports inside `domain/` or `use_cases/`
- [ ] Public APIs, ports, and entities have type hints
- [ ] Added/updated docstrings only where the *why* is non-obvious
- [ ] Logged decisions / next steps via `graph_add_memory` where appropriate
- [ ] Updated `CLAUDE.md` / `README.md` / examples if behavior or interfaces changed
- [ ] No secrets, credentials, or `.env` values committed
- [ ] `ruff` and `mypy` pass locally
- [ ] All tests pass locally (`pytest`)

## Screenshots / Demos

<!-- For UI / CLI output changes. Drag-and-drop images or paste terminal output. -->

## Related

<!--
- Closes #
- Related to #
- Follow-up issues to file:
- Prior PR:
-->

## Notes for Reviewers (Humans & Agents)

<!--
Anything that would meaningfully speed up review:
- Files to read first (in order)
- Files safe to skim
- Known limitations / explicit out-of-scope items
- Open questions you want feedback on
-->
