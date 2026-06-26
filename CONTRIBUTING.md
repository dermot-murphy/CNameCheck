# Contributing to CStyleCheck

Thank you for your interest in contributing to CStyleCheck.

## Reporting Issues

Use the [GitHub Issues](https://github.com/dermot-murphy/CStyleCheck/issues) tracker:

- **Bug reports**: label `bug` — include a minimal reproducing C file, your `.cstylecheck.yml`, and the version (`cstylecheck --version`).
- **Feature requests**: label `enhancement` — describe the Barr-C:2018 or MISRA-C rule being targeted and the expected behaviour.
- **Documentation issues**: label `documentation`.

## Pull Requests

1. Fork the repository and create a branch from `develop` (not `main`).
2. Follow the coding conventions enforced by CStyleCheck's own `rules.yml`:
   - Run `python src/cstylecheck.py --config src/rules.yml src/cstylecheck/` before pushing.
3. Add or update unit tests in `tests/` covering the changed behaviour.
4. Ensure CI passes: `pytest tests/ --tb=short`.
5. Open the PR against `develop`; include a reference to the relevant GitHub Issue.

## Code Style

CStyleCheck applies Barr-C:2018 and MISRA-C complementary naming conventions to its own source. The project's rule configuration is `src/rules.yml`. Any contribution must pass the self-check CI job (`cstylecheck_rules.yml`).

## AI Assistance Policy

This project uses AI tooling (Claude, Anthropic) as a development aid, documented in `docs/aspice/CStyleCheck_DEV001_AI_Authorship_Deviation.md`. Human review and approval of all AI-generated changes is required before merge (see `docs/aspice/CStyleCheck_DEV002_Independent_Review_Deviation.md`).

Contributors may also use AI assistance; however, the contributor is responsible for the correctness and style conformance of any AI-generated code submitted via PR.

## Licence

By contributing you agree that your contributions will be licensed under the [MIT Licence](LICENSE).
