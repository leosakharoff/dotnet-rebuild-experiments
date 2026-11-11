# Reproducible builds in .NET

These are the experiments for our MSc thesis at the IT University of Copenhagen:
Leo Sakharoff and Peter Juul Møller, 2026. We study reproducible builds using
Weel-Sandvig's PEMS platform, Phoenix, and the NuGet packages it ships. We want
to know what someone outside the development team needs to rebuild a release
byte for byte, and how much of that information the release provides.

## Experiments

[Experiment 1: Phoenix](1-phoenix/) tests the application's own build. After
pinning its build inputs, we obtained matching output across three machines:
1002 files and five container images. Its README gives the stage plan, how to
run each stage, and the results stage by stage.

Experiment 2 examines Phoenix's 341 NuGet package versions in two parts:

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

Both parts start from the same [population](2-dependencies/population/): the 341
shipped packages and what each declares about its origin (repository, commit,
compiler, symbols, signatures). Each part states its selection criteria in its
README. The [dependency graph](https://leosakharoff.github.io/phoenix-dependencies/)
draws the 341 packages with the edges from Phoenix's lock files, each node
coloured by its result in both parts: a page with six views, published on
GitHub Pages, and a figure. Its scripts and data are in
[`2-dependencies/graph/`](2-dependencies/graph/). [Shared tools](2-dependencies/tools/)
install specific SDK versions, inspect assemblies and debug symbols, and
compare assemblies with signatures removed. The experiment READMEs describe
the methods, commands, results and limitations.

## Scripts and data

We keep the full run history, logs and dated research notes in
[Speciale2026](https://github.com/peterjuulm/Speciale2026). The methods, scripts
and results for the thesis are collected here. Each experiment records its data
sources and which scripts were checked against the recorded results. Some
adapted scripts still need to be rerun. Each README states their status.

Weel-Sandvig's source code and build output are not included here. The changes
to Phoenix remain in its own repository.
