# Reproducible builds in .NET

These are the experiments for our MSc thesis at the IT University of Copenhagen:
Leo Sakharoff and Peter Juul Møller, 2026. We study reproducible builds using
Weel-Sandvig's PEMS platform, WS.PEMS, and the NuGet packages it ships.
The product is WS.PEMS. Its source repository is still called WS.Phoenix, and
that name appears only where a script points at the source. We want
to know what someone outside the development team needs to rebuild a release
byte for byte, and how much of that information the release provides.

## Experiments

| Part | Question | Folder | Findings | Figures |
| --- | --- | --- | --- | --- |
| Experiment 1 | RQ1: what it takes to make WS.PEMS's release reproducible | [1-ws-pems/](1-ws-pems/) | [findings](1-ws-pems/results/findings.md) · [by stage](1-ws-pems/results/stages.md) | [figures](1-ws-pems/figures/) |
| Experiment 2a | RQ2a: do the NuGet packages build deterministically | [2a-determinism/](2-dependencies/2a-determinism/) | [findings](2-dependencies/2a-determinism/results/findings.md) | [figures](2-dependencies/2a-determinism/figures/) |
| Experiment 2b | RQ2b: can the published packages be rebuilt | [2b-rebuild/](2-dependencies/2b-rebuild/) | [findings](2-dependencies/2b-rebuild/results/findings.md) | [figures](2-dependencies/2b-rebuild/figures/) |

Each experiment folder has the same layout: a README (method, how to run it,
results, caveats, data and scripts), `figures/`, `scripts/` and `results/`.
Scripts that several parts use are in a folder called `shared/`.

## Shared parts

| Folder | What it is |
| --- | --- |
| [categories/](categories/) | How we grouped the causes found in both experiments: the [codebook](categories/codebook.md) and the [codes](categories/codes.tsv) given to each finding |
| [2-dependencies/population/](2-dependencies/population/) | The 341 packages WS.PEMS ships and what each declares about its origin; the input to 2a and 2b |
| [2-dependencies/dependency-graph/](2-dependencies/dependency-graph/) | Not an experiment: a figure and a [web page](https://leosakharoff.github.io/phoenix-dependencies/) that draw the 341 packages as a graph, each coloured by its result in 2a and 2b |
| [2-dependencies/shared/](2-dependencies/shared/) | Scripts that 2a and 2b both use: install one SDK, inspect a DLL, strip signatures |
| [1-ws-pems/scripts/shared/](1-ws-pems/scripts/shared/) | Scripts that every stage of experiment 1 uses |

[Experiment 1: WS.PEMS](1-ws-pems/) tests the application's own build. After
the fixes, two runs on the same Arch machine gave identical output: 1002 files
and five container images. A separate check compared the same commit on
GitHub's runner, our Linux laptop and a Mac; its result is under
[Across machines](1-ws-pems/results/stages.md#across-machines). The README
gives the stage plan, how to run each stage, and the results stage by stage.

Experiment 2 examines WS.PEMS's 341 NuGet package versions in two parts:

- [2a: Build determinism](2-dependencies/2a-determinism/) compares two local
  builds of the same source commit under a fixed toolchain, varying one
  environmental condition at a time. Of 127 packages built, 102 produced
  identical complete packages with deterministic-build configuration. Of these,
  four already had identical contents under the default build; the other 98
  needed configuration to reach that result. The remaining 25 had differences or
  build failures under the tested variations.
- [2b: Rebuilding published packages](2-dependencies/2b-rebuild/) compares
  rebuilt assemblies with those distributed on nuget.org. Of 198 package
  versions attempted, 22 were reproduced using information recorded in the
  release. This count includes matches that disregard publisher signatures. A
  second, diagnostic build with Microsoft's own build system reproduced 35 more
  Microsoft packages on Windows; it shows what the release is missing and is
  not counted as reproduction. Of the 143 packages not attempted, 38 ship no
  managed code, 22 lack source information, and 83 lack a compiler record.

Both parts start from the same population, and each states its selection
criteria in its README. The experiment READMEs describe the methods, commands,
results and limitations.

## Scripts and data

We keep the full run history, logs and dated research notes in
[Speciale2026](https://github.com/peterjuulm/Speciale2026). The methods, scripts
and results for the thesis are collected here. Each experiment records its data
sources and which scripts were checked against the recorded results. Some
adapted scripts still need to be rerun. Each README states their status.

Weel-Sandvig's source code and build output are not included here. The changes
to WS.PEMS remain in its own repository.
