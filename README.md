# Reproducible builds in .NET

This repository contains experiments for our MSc thesis at the IT University
of Copenhagen: Leo Sakharoff and Peter Juul Møller, 2026.
We study reproducible builds using Weel-Sandvig's PEMS platform, Phoenix,
and the NuGet packages it ships.
We want to know what someone outside the development team needs to rebuild
a release byte for byte, and how much of that information the release provides.

## Experiments

[Experiment 1: Phoenix](1-phoenix/) examines the application's own build.
After pinning its build inputs, we obtained matching output across three
machines: 1002 files and five container images.
The documentation for this experiment is still being added.

Experiment 2 examines Phoenix's 341 NuGet package versions in two parts:

- [2a: Build determinism](2-dependencies/2a-determinism/) compares two local
  builds of the same source commit under a fixed toolchain, varying one
  environmental condition at a time.
  Of 127 packages built, 102 produced identical complete packages with
  deterministic-build configuration.
  Of these, four already had identical contents under the default build;
  the other 98 needed configuration to reach that result.
  The remaining 25 had differences or build failures under the tested
  variations.
- [2b: Rebuilding published packages](2-dependencies/2b-rebuild/) compares
  rebuilt assemblies with those distributed on nuget.org.
  Of 198 package versions attempted, 22 were reproduced using information
  recorded in the release, and another 35 using the publisher's build system
  on Windows.
  These counts include matches that disregard publisher signatures.
  Of the 143 packages outside this population, 38 ship no managed code,
  22 lack source information, and 83 lack a compiler record.

Both parts start from the same [population](2-dependencies/population/):
the 341 shipped packages and what each declares about its origin
(repository, commit, compiler, symbols, signatures). Each part selects
from it by its own criteria, stated in its README.
[Shared tools](2-dependencies/tools/) install specific SDK versions, inspect
assemblies and debug symbols, and compare assemblies with signatures removed.
The experiment READMEs describe the methods, commands, results and limitations.

## Scripts and data

We keep the full run history, logs and dated research notes in
[Speciale2026](https://github.com/peterjuulm/Speciale2026).
This repository brings together the methods, scripts and results for the thesis.
Each experiment documents where its data came from and which scripts have
been checked against the recorded results.
Some scripts have been adapted from the working repository and still need
to be rerun; their status is noted in the relevant README.

Weel-Sandvig's source code and build output are not included here.
The changes to Phoenix remain in its own repository.
