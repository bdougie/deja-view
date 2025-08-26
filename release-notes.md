# Release Notes

_Released on August 26, 2025_

## 🚀 Major Features

- **feat: resource monitoring, other small updates** ([#7377](https://github.com/continuedev/continue/pull/7377)) by @sestinj
- **feat: --mcp + --model flagss and some refactoring** ([#7379](https://github.com/continuedev/continue/pull/7379)) by @sestinj
- **feat: multi edit and single search and replace tools** ([#7267](https://github.com/continuedev/continue/pull/7267)) by @RomneyDa

## ✨ Improvements

- feat: add brief apply formatting instructions to agent/plan, current file description update ([#7247](https://github.com/continuedev/continue/pull/7247)) by @RomneyDa
- feat: --prompt flag ([#7358](https://github.com/continuedev/continue/pull/7358)) by @sestinj
- feat: plan mode sys prompt ([#7365](https://github.com/continuedev/continue/pull/7365)) by @sestinj
- feat: diff UI for find and replace tools ([#7367](https://github.com/continuedev/continue/pull/7367)) by @RomneyDa
- feat: allow/blocklisted blocks in unrollAssistant ([#7400](https://github.com/continuedev/continue/pull/7400)) by @sestinj

## 📝 Other Changes

- fix: correct malformed Warning tag in ollama-guide.mdx ([#7418](https://github.com/continuedev/continue/pull/7418)) by @bdougie
- docs: update open model recs for embed and rerank ([#7313](https://github.com/continuedev/continue/pull/7313)) by @shssoichiro
- fix: add Run Extension (standalone) config ([#7329](https://github.com/continuedev/continue/pull/7329)) by @exigow
- feat: focus on chat input after apply ([#7390](https://github.com/continuedev/continue/pull/7390)) by @uinstinct
- chore: bold Rules to match other headers IntroMessage ([#7303](https://github.com/continuedev/continue/pull/7303)) by @tingwai
- feat: add tool support for Novita provider models ([#7172](https://github.com/continuedev/continue/pull/7172)) by @u-yuta
- docs: Update Ollama guide documentation ([#7215](https://github.com/continuedev/continue/pull/7215)) by @bdougie
- fix: update broken links to Next Edit documentation ([#7339](https://github.com/continuedev/continue/pull/7339)) by @bdougie
- fix: handle apply errors in tools (+ fix auto accept diffs flake) ([#7278](https://github.com/continuedev/continue/pull/7278)) by @RomneyDa
- fix: CLI UI Improvements ([#7344](https://github.com/continuedev/continue/pull/7344)) by @sestinj
- chore(deps): bump form-data from 4.0.2 to 4.0.4 in /packages/continue-sdk ([#7320](https://github.com/continuedev/continue/pull/7320)) by @dependabot[bot]
- Respect "useReranking" field from configuration ([#7286](https://github.com/continuedev/continue/pull/7286)) by @Pyroboomka
- chore(deps): bump actions/checkout from 4 to 5 ([#7287](https://github.com/continuedev/continue/pull/7287)) by @dependabot[bot]
- docs: update recommended model links ([#7345](https://github.com/continuedev/continue/pull/7345)) by @bdougie
- chore: upgrade to 1.3.0 ([#7347](https://github.com/continuedev/continue/pull/7347)) by @tomasz-stefaniak
- refactor: code cleanup for next edit ([#7312](https://github.com/continuedev/continue/pull/7312)) by @jpoly1219
- fix: stop dependencies from logging to stdout when in tui mode ([#7346](https://github.com/continuedev/continue/pull/7346)) by @sestinj
- fix: name check ([#7352](https://github.com/continuedev/continue/pull/7352)) by @tomasz-stefaniak
- fix: redirect agents -> assistants ([#7243](https://github.com/continuedev/continue/pull/7243)) by @RomneyDa
- Update package.json ([#7356](https://github.com/continuedev/continue/pull/7356)) by @sestinj
- Add tokenizer tests and fix auto-compact calculation to account for max_tokens ([#7342](https://github.com/continuedev/continue/pull/7342)) by @sestinj
- Update cli-pr-checks.yml ([#7299](https://github.com/continuedev/continue/pull/7299)) by @sestinj
- chore(deps): bump form-data from 4.0.2 to 4.0.4 in /packages/continue-sdk/typescript ([#7364](https://github.com/continuedev/continue/pull/7364)) by @dependabot[bot]
- chore(deps): bump form-data from 4.0.0 to 4.0.4 in /binary ([#7366](https://github.com/continuedev/continue/pull/7366)) by @dependabot[bot]
- fix: grep escaped chars and empty results ([#7323](https://github.com/continuedev/continue/pull/7323)) by @RomneyDa
- feat: :lipstick: Unified Terminal ([#7383](https://github.com/continuedev/continue/pull/7383)) by @chezsmithy
- Fix reranking on vllm provider ([#7210](https://github.com/continuedev/continue/pull/7210)) by @Pyroboomka
- fix: remove kover ([#7325](https://github.com/continuedev/continue/pull/7325)) by @exigow
- fix: HOTFIX local assistant loading ([#7354](https://github.com/continuedev/continue/pull/7354)) by @RomneyDa
- fix: jump label overlapping with the inline tip label ([#7399](https://github.com/continuedev/continue/pull/7399)) by @jpoly1219
- Add continue-on-error to JetBrains plugin publish steps ([#7394](https://github.com/continuedev/continue/pull/7394)) by @sestinj
- fix: reinstate gui telemetry for non-continue users by separating sentry and posthog logic ([#7396](https://github.com/continuedev/continue/pull/7396)) by @sestinj
- fix: remove non recommended models ([#7397](https://github.com/continuedev/continue/pull/7397)) by @bdougie
- fix: show autodetected in model titles ([#7393](https://github.com/continuedev/continue/pull/7393)) by @RomneyDa
- fix: CSS files not being indexed (#7072) ([#7375](https://github.com/continuedev/continue/pull/7375)) by @su0as
- feat: support env section in config yaml ([#7250](https://github.com/continuedev/continue/pull/7250)) by @uinstinct
- fix: properly build packages for cli releases ([#7334](https://github.com/continuedev/continue/pull/7334)) by @sestinj
- fix: HOTFIX unknown context provider file ([#7311](https://github.com/continuedev/continue/pull/7311)) by @RomneyDa
- chore: bump versions ([#7335](https://github.com/continuedev/continue/pull/7335)) by @tomasz-stefaniak
- fix: move dependencies to devDependencies and add @sentry/profiling-node ([#7340](https://github.com/continuedev/continue/pull/7340)) by @sestinj
- chore(deps-dev): bump form-data from 4.0.0 to 4.0.4 in /gui ([#7321](https://github.com/continuedev/continue/pull/7321)) by @dependabot[bot]
- chore(deps): bump actions/setup-node from 3 to 4 ([#7289](https://github.com/continuedev/continue/pull/7289)) by @dependabot[bot]
- fix: tab and esc are properly reserved ([#7268](https://github.com/continuedev/continue/pull/7268)) by @jpoly1219

## 👥 Contributors

Thanks to all contributors: @Pyroboomka, @RomneyDa, @bdougie, @chezsmithy, @dependabot[bot], @exigow, @jpoly1219, @sestinj, @shssoichiro, @su0as, @tingwai, @tomasz-stefaniak, @u-yuta, @uinstinct
