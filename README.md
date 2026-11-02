# Rebuilding .NET: the experiments

Scripts and results behind the MSc thesis of Leo Sakharoff and Peter Juul
Møller (IT University of Copenhagen, 2026) on reproducible builds in the
.NET ecosystem, measured on one real product, Weel-Sandvig's PEMS platform
(Phoenix), and its NuGet dependency closure.

The question:

> Given a shipped binary and the source commit it names, what else does a
> third party need to know to produce the same bytes, and does any record
> of the release name it?

Two experiments answer it, from two sides:

| folder | experiment | question | answer in one line |
|---|---|---|---|
| `1-phoenix/` | Make one product reproducible | Can Phoenix's release be rebuilt byte for byte? | Yes, once every input is pinned: 1002 files and five images, on three machines |
| `2-dependencies/` | The product's dependencies | What does a rebuild of the 341 packages Phoenix ships need to know? | Two parts, below |

Experiment 2 has two parts, each in its own folder under `2-dependencies/`:

| folder | part | question | answer in one line |
|---|---|---|---|
| `2a-rebuild/` | Rebuild against nuget.org | Can the published bytes be produced again from what the release names? | For 57 of 198 tried; 143 of 341 name nothing a rebuild can start from |
| `2b-determinism/` | Determinism in a fixed environment | With every input held, does the build give the same bytes, and what breaks it? | 66 of 90 with the ecosystem's own configuration; the rest is the publishers' build logic |

`2-dependencies/census/` holds the population both parts draw from: what
each package of Phoenix's dependency closure declares for a rebuild.
`2-dependencies/tools/` holds what both parts share: installing one SDK by
hash, reading a DLL and its PDB.

Every part follows the same four steps, and its folder is laid out after
them: **derive** a recipe from what is public, **build** it, **classify** the
outcome against a fixed scale, **summarise** into one table. Each folder's
README states the question, the population, the exact command, the scale,
the result table and the caveats.

## What this repository is, and is not

This is the finished form. The working repository,
[Speciale2026](https://github.com/peterjuulm/Speciale2026), holds every run,
restart, pilot and dead end, with notes dated by the day they were run.

Two rules hold here:

1. **A script next to a result is the script that produced it.** Where a
   script was trimmed for reading, it was run again on a sample and the rows
   compared; the folder's README says so and names the working repository's
   commit the data came from.
2. **Nothing from Weel-Sandvig's source or build output.** Experiment 1's
   fixes live on a branch of Phoenix's own repository; `1-phoenix/` describes
   them and holds the measuring scripts only.
