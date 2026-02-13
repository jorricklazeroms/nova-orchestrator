# Contributing

Thanks for contributing. This project follows a DUO delivery model with explicit ownership and quality gates.

## Ground Rules
- No direct pushes to `main`.
- Open a branch and submit a pull request.
- CI must pass before merge.
- At least one owner approval is required before merge.

## Development Flow
1. Create a feature branch from `main`.
2. Keep changes scoped and include tests when behavior changes.
3. Run local quality checks.
4. Open a PR with test output.

## Required Quality Checks
- Node repos: `npm run lint`, `npm test`, `npm run build`
- Python repos: `ruff check .`, `pytest -q`
- WordPress theme repo: `npm run lint` (includes CSS + PHP syntax checks)

## Pull Requests
- Describe the problem and solution.
- Include exact command output for checks.
- Link related issue(s).
- Request owner review.
