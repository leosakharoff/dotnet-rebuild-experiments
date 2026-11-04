# Experiment 2: Phoenix's NuGet dependencies

What information is needed to rebuild Phoenix's packages, and does the release
record it? The four steps each have a folder with a README, `scripts/` and
`results/`. The two measurements also have `population.tsv`, and three of the
steps have `figures/`:

| folder | step | one line |
|---|---|---|
| `population/` | The 341 packages Phoenix ships, and what each declares about its origin | the list both parts start from |
| `2a-determinism/` | Build determinism: two builds of the same commit under one fixed SDK, one condition varied at a time | 102 of 127 identical with the ecosystem's own configuration; 25 held back by the publishers' build logic |
| `2b-rebuild/` | Rebuild against nuget.org: can the published bytes be produced from what the release names? | 22 of 198 from the release alone; the publisher's own build, a diagnostic, reproduces 35 more on Windows |
| `graph/` | The 341 packages as a graph: the edges from Phoenix's lock files, each node coloured by its 2a and 2b result | a figure, and [a page](https://leosakharoff.github.io/phoenix-dependencies/) where each package opens, with six views |
| `tools/` | What all three share: one SDK by hash, a DLL and PDB report, signatures stripped | |

How the steps connect:

```
population/results/shipped-packages.txt  (341)  →  2a/scripts/population.py  →  2a/population.tsv  (224 with repo, commit, project)
population/results/packages.tsv  (what each declares)  →  2b's filter  →  2b/population.tsv  (198 with commit and compiler record)
```

2a uses a fixed toolchain to test the build itself. 2b derives the toolchain
from the release records and tries to reproduce the published bytes. `graph/`
reads both parts' `results/categories.tsv` and the population's
`packages.tsv`, adds the edges from Phoenix's lock files, and draws the
result. Each README gives the question, population, commands, comparison
levels, result tables and caveats. The working repository
[Speciale2026](https://github.com/peterjuulm/Speciale2026) holds every run, log
and dated note behind them.
