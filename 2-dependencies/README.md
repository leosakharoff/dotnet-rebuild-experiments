# Experiment 2: Phoenix's NuGet dependencies

What does a rebuild of the packages Phoenix ships need to know, and does
any record of the release name it? Three steps, each in its own folder
with the same shape (README, `scripts/`, `results/`, and for the two
measurements `population.tsv` and `figures/`):

| folder | step | one line |
|---|---|---|
| `population/` | The 341 packages Phoenix ships, and what each declares about its origin | the list both parts start from |
| `2a-determinism/` | Build determinism: two builds of the same commit under one fixed SDK, one condition varied at a time | 102 of 127 identical with the ecosystem's own configuration; 25 held back by the publishers' build logic |
| `2b-rebuild/` | Rebuild against nuget.org: can the published bytes be produced from what the release names? | 22 of 198 from the release alone, 35 more with the publisher's own build on Windows |
| `tools/` | What all three share: one SDK by hash, a DLL and PDB report, signatures stripped | |

How the steps connect:

```
population/results/shipped-packages.txt  (341)  →  2a/scripts/population.py  →  2a/population.tsv  (224 with repo, commit, project)
population/results/packages.tsv  (what each declares)  →  2b's filter  →  2b/population.tsv  (198 with commit and compiler record)
```

2a holds the toolchain fixed and asks what the build itself does; 2b
derives the toolchain from what the release names and asks whether the
publisher's bytes come back. Each README states the question, the
population, the exact commands, the comparison levels, the result tables
and the caveats; the working repository
[Speciale2026](https://github.com/peterjuulm/Speciale2026) holds every
run, log and dated note behind them.
