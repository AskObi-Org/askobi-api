# Style Guide Generation (AskObi API)

This step extracts **project-specific conventions** (not generic best practices) from each file category.

## What was discovered

The repo has a consistent “small layered service” style:

- **Routers** are thin and orchestrate dependencies + services.
- **Services** encapsulate flows (auth/session lifecycle).
- **Repositories** encapsulate SQL.
- **Schemas** are Pydantic models; a custom `Schema` base normalizes objects.
- **Models** use a custom base from advanced-alchemy, plus Pydantic JSON columns for user preferences.

## Why it matters

Style guides let humans and AI assistants add new features without drifting from existing patterns.

## Output

One style guide per category exists in `.results/5-style-guides/`.
