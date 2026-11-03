# Rebuilding published NuGet packages

Given a package on nuget.org and the commit it names, can a third party reproduce the
DLL served by nuget.org using only the published release and the source at that commit?
If not, what is missing?

Part 2a compares two of our own builds. Part 2b compares our build with the publisher's
bytes. Benedetti et al. (2025) deliberately omit this comparison because the commit
behind an upload is difficult to identify. For packages that provide these records, the
`.nuspec` identifies a commit and Source Link maps source files to it. These records
give us a starting point for the comparison.

## Method

### Population

The population consists of the 341 packages shipped by Phoenix
(`../population/results/shipped-packages.txt`), classified according to the dependency census
(`../population/README.md`).

Part 2b includes packages that ship managed code and whose release identifies both a
commit and, through the PDB, the compiler. Of the 341 packages, 38 ship no managed code.
Another 105 of the remaining 303 fail the filter:

- 9 name no repository.
- 13 name no commit.
- 45 have no PDB.
- 36 have a PDB that is neither included in the package nor available from a symbol
  server.
- 2 have a PDB without a compiler record.

This leaves **198 packages**: 59 third-party and 139 Microsoft packages.
`population.tsv` records the package, version, DLL shipped in Phoenix, owner and census
class.

This population differs from the 224 packages in part 2a
(`../2a-determinism/population.tsv`). The two populations share 185 packages. Part 2a
includes 39 packages that are absent here, while part 2b includes 13 that are absent
from part 2a.

The difference follows from the filters. Part 2b derives the SDK from the compiler
record in the PDB, so a package without that record cannot receive a recipe. Part 2a
holds one SDK fixed and requires only a repository, commit and project.

### Deriving a build recipe

`scripts/derive.py` derives each package's build parameters from its release using eight
rules. The `facts.txt` file beside each recipe classifies every value as *read*,
*inferred* or *default*. Read values include their source, inferred values identify the
rule that converted an observation into a choice, and defaults state why they were used.

| rule | value | taken from |
|---|---|---|
| 1 | package, PDB | nuget.org: the `.nupkg`, else the `.snupkg`, else the symbol server by the DLL's CodeView key |
| 2 | source | the `.nuspec`'s commit; the clone URL from the PDB's Source Link entry at that commit |
| 3 | SDK | `global.json` if its SDK's `csc.dll` has the PDB's compiler version; else the lowest public SDK of the channel whose `csc.dll` has it (inferred; the SDKs not read are listed) |
| 4 | OS | Windows if the SDK-generated files embedded in the PDB have CRLF, else Linux (inferred) |
| 5 | build folder | the PDB's document paths, when they are absolute |
| 6 | checkout line endings | as stored or converted to CRLF, whichever gives the PDB's source checksums |
| 7 | project | the `.csproj` whose assembly name is the DLL's; `ref/` projects dropped; of several, the one named like the package |
| 8 | version | `VersionPrefix`/`VersionSuffix` from the informational version, `AssemblyVersion` and `FileVersion` from the DLL, `PackageVersion` from the `.nuspec` |

If the rules cannot resolve a package, it receives *no recipe*, together with the rule
that stopped the derivation.

Every package uses the same command:

```bash
dotnet build PROJECT -c Release <properties> && dotnet pack PROJECT -c Release --no-build -o out-nupkg <properties>
```

`<properties>` contains the values from rule 8, together with
`ContinuousIntegrationBuild=true` when the PDB paths are mapped to `/_/`. The method
does not read CI files or build scripts. It uses only information available to a
consumer from the release.

### Controlled build environment

Each build uses the derived SDK, installed by itself from Microsoft's archive after
checking its SHA-512 hash (`../tools/install-sdk.py`). It starts from a fresh full clone
at the named commit and an empty package cache. `NuGetAudit=false` prevents advisories
published after the release from failing the restore.

On Linux, the environment is empty apart from `HOME`, `PATH`, `LANG` and
`NUGET_PACKAGES`. Linux recipes run on `arch` (Arch Linux, kernel 7.2.11), or on
GitHub's `ubuntu-24.04` runner when the PDB records a runner build folder. Windows
recipes run on GitHub's `windows-2022` runner (image 20261022.344.1).

Each package is built twice in the same paths, A and A2, with all generated state
deleted between builds.

### Comparison and grading

The comparison uses the DLL shipped in Phoenix, extracted both from our rebuilt package
and from the package on nuget.org. This is the census file for the package's target
framework. It narrows part 2a's level 3 comparison of all DLLs to the single DLL loaded
by Phoenix.

`../tools/dllreport.cs` reads both DLLs and hashes every section, metadata stream and
resource separately. `scripts/level.py` then grades the pair:

| grade | what differs |
|---|---|
| identical | nothing |
| identical without signatures | only the Authenticode block, the strong-name signature and the PE checksum (`../tools/stripsign.cs` cuts them and hashes the rest) |
| same code | only the build identity: MVID, PE timestamp, PDB id and checksum |
| other code | anything in IL, the metadata streams or the resources |

Part 2a's level 1 comparison cannot be applied to nuget.org packages. After upload,
nuget.org adds its repository signature, `.signature.p7s`, so a rebuilt package cannot
be byte-for-byte identical to the served package.

Levels 2 and 3 can still be determined from the stored package listings
(`results/compare.txt`). Of the 86 packages built and compared, 9 are equal at level 2,
which excludes NuGet's packaging files and repository signature. Eleven are equal at
level 3, which compares every DLL under `lib/`, `ref/` and `runtimes/`. Every signed
package fails both levels because of the signature alone. Part 2b therefore grades the
single DLL instead.

Each package is assigned to one of three groups:

- *Reproduced*: identical, or identical without signatures.
- *Built, but differs*: same code, or other code.
- *Not built*: no package, or no recipe.

A publisher's signing key is required to reproduce a signature. For a signed package,
identical without signatures is therefore the highest attainable grade.

The A-to-A2 comparison acts as a control. It distinguishes a build that differs from the
publisher from one that also differs from itself.

## Running the experiment

Run from `2-dependencies/2b-rebuild/` on Linux, with Python 3.11 or later, git, and
network access to nuget.org, GitHub and Microsoft's SDK archives.

**1. One SDK, installed alone.** The DLL reports need a .NET 10 SDK. Each build
installs its own SDK later.

```bash
LAB=$HOME/rebuild-lab                        # outside any repository
python3 -I ../tools/install-sdk.py 10.0.403 $LAB/report-sdk
```

**2. Everything this machine can build, from `population.tsv` to `results/`.** Every
package is derived, the Linux recipes are built here, and every build is compared with
nuget.org. The rows go into `results/release-build.tsv` and `results/compare.txt`,
where they replace the stored rows of the same packages.

```bash
python3 -I scripts/run-batch.py population.tsv $LAB
```

**3. The tables.**

```bash
python3 -I scripts/summary.py                # results/summary.md, results/categories.tsv
```

### Recipes that need Windows

Most recipes name Windows as the publisher's host. Two more need GitHub's Ubuntu runner,
because the build folder their PDBs record, `/home/runner/work/...`, cannot be made
here. Step 2 lists them all in
`$LAB/runner.txt`. On a Windows machine with Python and git, build each one with:

```bash
python -I scripts/rebuild.py RECIPE WORKDIR
```

To use GitHub's runners instead, copy `scripts/nupkg-rebuild.yml` to
`.github/workflows/` in a fork, commit the recipes, and start one run per recipe. Each
run's artifact is the build's `out` folder:

```bash
gh run download RUN -D $LAB/runner/<Package>-<version>
```

Put each `WORKDIR/out` or artifact under `$LAB/runner/<Package>-<version>/`, then run
steps 2 and 3 again. Step 2 reuses everything it has already built.

### The publisher's build

The publisher's build runs after step 2, in the same lab. It derives the recipes from
`publisher-build/packages.txt` and builds the four dotnet/dotnet recipes here, which
need clang, cmake and ninja.

```bash
python3 -I publisher-build/scripts/run-repo-batch.py $LAB
```

The other recipes are listed in `$LAB/repo-runner.txt` and run on Windows in the same
way, with `publisher-build/scripts/repo-build.py` or
`publisher-build/scripts/nupkg-repository-build.yml`. Their output goes under
`$LAB/repo-runner/<name>/`. A second run classifies them into
`$LAB/publisher-build.tsv`, in the form of `publisher-build/results/publisher-build.tsv`.

## Results

The run took place on 27 October 2026. The third-party packages ran from 13:05 to 13:55,
and the Microsoft packages from 10:50 to 12:38.

The experiment derived 157 recipes: 137 ran on `windows-2022`, 18 on `arch` and 2 on
`ubuntu-24.04`. `scripts/summary.py` writes the tables to `results/summary.md`.

### Release build

The release build covers all 198 packages.

| group | grade or outcome | third-party | Microsoft | all |
|---|---|---|---|---|
| reproduced (22) | identical | 14 | 0 | 14 |
| | identical without signatures | 3 | 5 | 8 |
| built, but differs (64) | same code | 9 | 0 | 9 |
| | other code | 16 | 39 | 55 |
| not built (112) | no package | 12 | 59 | 71 |
| | no recipe | 5 | 36 | 41 |
| | total | 59 | 139 | 198 |

The build derived from the release reproduces 22 of the 198 packages: 17 of 59
third-party packages and 5 of 139 Microsoft packages. More than half of the packages do
not build.

A equals A2 for 76 of the 86 compared packages. Nine packages differ from themselves:
the IdentityModel packages, whose version includes the clock. One further package was
not compared. This reproduces the finding from part 2a without introducing any
variation.

The compared assemblies are byte-for-byte identical for: RBush; FluentValidation and its
DependencyInjectionExtensions; Serilog; Serilog.Sinks.File; Serilog.Sinks.Seq;
Ardalis.GuardClauses; CsvHelper; Markdig; Npgsql and its EF Core provider; ScottPlot;
TimeZoneConverter; and UnitsNet.

Cronos, Hangfire.InMemory, NodaTime, Microsoft.Identity.Abstractions,
Microsoft.Identity.Web.Certificateless, .Diagnostics, .TokenCache and Microsoft.OpenApi
received the grade *identical without signatures*. These eight cases were assessed from
DLL reports; they have not been checked by hashing the complete signature-stripped
files.

### Builds with other code

Fifty-five packages produce other code. One value written into the assembly by the
publisher's build accounts for most of these differences. The release states this value,
but the project does not accept it as an input.

| cause | packages | what differs |
|---|---|---|
| Arcade's development versioning | 17 (Roslyn 7, EF Core 7, Sqlite, DiaSymReader, Build.Framework) | `FileVersion` 42.42.42.42424 instead of the shipped one; the informational version loses `+<commit>` |
| clock in the version | 9 (IdentityModel) | `8.23.0-preview-<clock>`; these are the nine where A differs from A2 |
| date suffix on unofficial builds | 8 (Azure SDK, System.ClientModel) | `1.50.0-alpha.<date>.1` against `1.50.0` |
| copyright year from the build clock | 6 (Swashbuckle 5, Stateless) | 2024 against 2026 |
| attributes written by the CI script | 3 (Bogus, YamlDotNet, FluentModbus) | `GenerateAssemblyInfo=false`; the values come from a script the method does not run |
| version computed from git | 2 (MediatR.Contracts by MinVer, ExCSS by GitVersion) | MinVer's tag height; the branch name in the informational version |
| targeting pack | 2 (SharpZipLib, MediatR.Extensions.Microsoft.DependencyInjection) | `TargetFrameworkAttribute`'s display name; IL differs too |
| `RepositoryUrl` form | 2 (Serilog.Settings.Configuration, Serilog.Extensions.Logging) | with or without `.git` |
| signing key | 1 (RecyclableMemoryStream) | strong name and `InternalsVisibleTo` with a key outside the repository |
| not read | 5 (Google.Protobuf, ShimSkiaSharp, Identity.Web 3) | |

### Builds with the same code

Nine third-party packages produce the same code: Ardalis.Specification 2, AutoMapper,
MediatR, Quartz 4 and SendGrid. Their IL, metadata and resources are equal. Only the
build identity differs.

Under deterministic compilation, the build identity is a hash that also covers the PDB,
which this grade does not compare. These differences were not investigated further.

### Packages not built

A total of 112 packages were not built.

| outcome | cause | packages |
|---|---|---|
| no recipe | the compiler is in no public SDK (Microsoft's 8.0.0 and 9.0.0 GA packages and others) | 25 |
| | the compiler ran on .NET Framework (Visual Studio's MSBuild) | 10 |
| | the commit is not reachable at the repository (IdentityModel 8.19.2) | 2 |
| | no single project with the assembly name | 2 |
| | no PDB with a compiler record (SqlClient) | 1 |
| | the checkout failed (ImageSharp) | 1 |
| no package | a project in `dotnet/dotnet` or `dotnet/runtime` needs the repository's bootstrap | 37 |
| | another single-project build error (Svg 5, Identity.Web and others 7) | 12 |
| | SDK workloads (SkiaSharp, HarfBuzzSharp) | 5 |
| | Microsoft's internal feed in `NuGet.config` (ASP.NET Core 9.0.0) | 4 |
| | a `Directory.Build.props` the repository's script generates (Razor 6.0.24) | 2 |
| | a feed outside nuget.org (SixLabors.Fonts), a restore of RazorGenerator (Hangfire 2) | 3 |
| | packed, but not under the release's id and version (Dapper, Humanizer.Core, Mono.TextTemplating, Portable.BouncyCastle, Workspaces.MSBuild, NETCore.App.Runtime, SolutionPersistence) | 7 |
| | the runner job left no output (dotnet-ef) | 1 |

The causes are taken from the first error in each build log in the working repository.
`summary.py` does not determine them.

## Using the publisher's build system

Most Microsoft packages fail in the release build for the same reason: the project
expects the repository's Arcade build system to run first. A second build measures the
value of knowing that build system.

This experiment covers the 96 packages from Arcade repositories. It excludes the two
runtime packs, which require a full product build, and StringTools, which has no
project.

The build invokes the repository's own entry point at the named commit: `eng/build.sh`
or `build.cmd` with `--ci -c Release --pack`, the package subset documented by the
repository. It passes the `OfficialBuildId` decoded from the shipped file version and
the release branding used by the official pipeline.

For the inner repositories of `dotnet/dotnet`, it also passes the two identity
properties used by the VMR: `RepositoryUrl` and `RepoOriginalSourceRevisionId`. The
build disables optimization data through `EnableNgenOptimization=false` and removes
Microsoft's internal feeds from `NuGet.config`.

The 16 standalone recipes, covering 42 packages, ran on GitHub's `windows-2022` runners,
matching the publisher's host. The four VMR builds, covering 54 packages, ran on `arch`
because `dotnet/dotnet` does not fit on a free runner.

| group | grade or outcome | windows-2022 | Linux (VMR) | all |
|---|---|---|---|---|
| reproduced (35) | identical without signatures | 35 | 0 | 35 |
| built, but differs (58) | same code | 4 | 25 | 29 |
| | other code | 0 | 29 | 29 |
| not built (3) | no package | 3 | 0 | 3 |
| | total | 42 | 54 | 96 |

Of the 42 packages built on the publisher's host, 35 are reproduced. Every compared
assembly is byte-for-byte identical after signatures are removed
(`publisher-build/results/signature-stripped.txt`). The same recipes reached only the
same-code grade on Linux, and no VMR package is reproduced.

All 25 packages whose compiler is unavailable in a public SDK built in this experiment.
Twenty-two are reproduced, and three reach the same-code grade. The compiler was
available through the repository's own build system, which supplies it.

For the reproduced assemblies, access to the source was not sufficient: the build also
required knowledge of the publisher's pipeline. The additional inputs included build
IDs, versioning rules, the host operating system and build steps outside the individual
project. The release metadata did not provide a complete recipe for those steps.

The eight Roslyn packages are reproduced only under one rule. Roslyn's official pipeline
does not pass release-branding properties, so the build retains the prerelease
informational version found in the shipped assemblies. A later repack changes the
package version to 5.0.0.

This rule was added after a Windows run with branding properties produced other code
because of that single string. Applying branding properties to every repository
reproduces 27 of 42 packages rather than 35.

### Results per package

| category | packages | without the Roslyn rule |
|---|---|---|
| from the release | 22 | 22 |
| with the publisher's build | 35 | 27 |
| not reproduced (best grade same code 38, other code 68) | 106 | 114 |
| no package | 22 | 22 |
| no recipe | 13 | 13 |

One of the two builds reproduces 57 of the 198 packages. Without the Roslyn rule, the
count is 49. The 13 packages without a recipe are the .NET Framework compilers, the
IdentityModel commits, SqlClient and ImageSharp.

## Earlier versions of the method

The working repository contains three versions of the release build and five versions of
the publisher's build. The versions were documented before their runs, with the
Roslyn-specific rule below developed after inspecting an earlier result. This folder
retains only the final version of each.

Version 1 of the release build ran a single `dotnet pack`, which produces no package for
a project with `GeneratePackageOnBuild`. Version 2 did not pass the assembly and file
versions, excluded preview SDKs from rule 3, and could not choose between a `ref/` and a
`src/` project. Version 3 resolves all three issues using facts from the release.

The publisher's build discarded its first version because it lacked the VMR identity
properties and used a `libs -pack` subset that produced no packages. It also discarded
version 4 because it checked out source files exactly as committed, an approach refuted
by the CRLF line endings in the shipped bytes. Linux runs of the standalone repositories
were superseded by runs on the publisher's host.

The pilot recipes read publisher CI files, which are not release facts. The reprotest
work originally performed in part 2b moved to part 2a. The diagnostic readers,
`pdbdump.cs`, `tabledump.cs` and a glob-order project, explain individual differences
and are cited but are not part of the method.

When counted from one rule set per build, the results equal the working repository's
“best of all versions” count from 28 October.

## Caveats

- There is no held-out set. The rules were refined using the packages later measured.
  Each version was documented before it ran, and the earlier rows are retained. This
  makes the iteration auditable but not blind. The Roslyn rule is the only rule written
  after observing its result.
- The method injects the version, file version, `OfficialBuildId` and `RepositoryUrl`
  read from the shipped DLL. Matching these attributes provides no evidence by itself;
  the evidence comes from the IL, metadata and resources.
- The eight release-build rows graded as identical without signatures were assessed from
  the report lines rather than whole-file hashes produced with `stripsign.cs`. The 35
  corresponding publisher-build rows were hashed as whole files.
- Rule 3 selects the lowest SDK containing the compiler. Higher SDKs with the same
  compiler are listed but not tested.
- Rule 7 reads `AssemblyName` directly from the `.csproj` text rather than evaluating it
  through MSBuild. Workspaces.MSBuild selected the wrong project.
- Each package is built once against the publisher, with A2 as its repeat. A difference
  is observed, while equality means that no difference was detected, as in part 2a.
- Restore used the feeds available on 27 October 2026 rather than those available on the
  release date. A dependency that had since been unlisted or moved would appear as a
  failed restore or a difference.
- The publisher's build covers only Arcade repositories. Each third-party repository has
  its own build process, including scripts, Cake, Nuke or CI files, and no single rule
  covers them all. The 25 third-party rows that built but differed were not retried with
  those repository-specific systems.
- This is a case study of one product's dependency closure, not a sample.

## Data and scripts

```
2b-rebuild/
  README.md
  population.tsv    the 198 packages
  figures/          the method as a figure
  scripts/          the release build and the tables
  results/          the release build's results and the tables
  publisher-build/
    packages.txt    the 99 packages from Arcade repositories, a hand-kept list
    scripts/        the publisher's build
    results/        its results
```

- `population.tsv` lists the 198 packages and the DLL from each package that Phoenix
  ships. It uses the first census-file row per package, as read by `derive.py`, and was
  checked against every stored `facts.txt`. It also records the owner and census class.
- `figures/method.drawio` contains the command sequence as a figure.
  `figures/method.drawio.png` is exported from it using `drawio -x -f png -e -s 2 -b 10
  -o method.drawio.png method.drawio` in `figures/`.
- `scripts/derive.py`, `rebuild.py`, `compare.py` and `level.py` are included.
  `compare.py` and `level.py` are unchanged. `derive.py` and `rebuild.py` are taken from
  the working repository with lab-specific paths removed. These include the report SDK
  path, git mirrors, and the shallow-clone and extra-runtime options unused by any
  version-3 recipe.
- `scripts/run-batch.py` combines the working repository's `run-batch.py` and
  `derive-batch.py`. It omits recipe commits and pushes, GitHub run dispatch and
  polling, and the disk guard. Runner builds are started manually from `runner.txt`.
  In the lab it writes a recipe and `facts.txt` per package under
  `derive/<Package>-<version>/`, the builds made here under
  `build/<Package>-<version>/out/`, and `runner.txt`, `results.tsv`, `compare.txt` and
  `run.log`. It installs the report SDK into `report-sdk/` if step 1 was skipped. The
  rows it writes into `results/` carry `run-batch.py` and the date in the `source`
  column. One package can be built by hand with `python3 -I scripts/derive.py PACKAGE
  VERSION population.tsv $LAB $LAB/derive/PACKAGE-VERSION`, then `python3 -I
  scripts/rebuild.py $LAB/derive/PACKAGE-VERSION/recipe.toml WORKDIR`. The stored run
  took less than one hour for the 59 third-party packages and two hours for the 139
  Microsoft packages, with the runner builds in parallel.
- `scripts/summary.py` contains the tables for both builds. It reproduces
  `results/summary.md` and `results/categories.tsv` from the stored files, as checked on
  3 November.
- `scripts/sdk-csc.json` maps SDK versions to compiler versions. Rule 3 reads the
  compiler version from each SDK's `csc.dll`. `derive.py` reads and extends the mapping.
- `scripts/nupkg-rebuild.yml` is the GitHub workflow that ran `rebuild.py` on the
  runners, using this repository's paths. It is not active here.
- `results/` was assembled from the working repository's runs. The `source` column in
  every TSV row identifies the source data folder and file.
  - `release-build.tsv` contains one row per package from the two version-3 runs on 27
  October: `2026-10-27-nupkg-release-only-batch2-v3` and
  `2026-10-27-nupkg-release-only-batch3-microsoft`.
  - `compare.txt` contains the package listing for every compared release build, with
  one section per package and the source file identified.
  - `environment.txt` contains one line per host.
  - `summary.md` and `categories.tsv` are printed by `summary.py`.
- `publisher-build/packages.txt` lists the Arcade packages covered by the publisher's
  build, with one “Package Version” line per package. The list was manually derived from
  the release build's Microsoft packages. It is the input to `derive-repo.py` rather
  than a separate population, so it retains the working repository's format.
- `publisher-build/scripts/derive-repo.py` and `repo-build.py` come from the working
  repository. `derive-repo.py` includes the final rule set selected by its `--v5` flag.
  The stored recipe for each final row is the recipe derived by that flag. The VMR
  recipes are byte-for-byte identical to those from the Linux run, as checked on 3
  November. `repo-build.py` reads `rebuild.py` and `compare.py` from `scripts/`.
- `publisher-build/scripts/run-repo-batch.py` combines the working repository's
  `run-repo-batch.py` and `collect-runner.py`. It omits the order files, disk guard,
  commits and artifact downloads. It uses the release build's `report-sdk/` and
  `derive/` in the same lab. On Windows, the Node version a recipe names goes first on
  `PATH`. The four dotnet/dotnet builds completed together in less than one hour on a
  16-core machine. A Windows build takes between 6 and 30 minutes on a 4-core runner.
- `publisher-build/scripts/nupkg-repository-build.yml` is the GitHub workflow from the
  Windows run, adjusted to this repository's paths. It is not active here.
- `publisher-build/results/publisher-build.tsv` contains one row per package and a
  `source` column. It combines the Windows run of 28 October
  (`2026-10-28-nupkg-repository-build-windows`), the eight Roslyn rows from the rerun
  under the Roslyn rule (`…-windows-v5`), and the VMR rows from the Linux run
  (`2026-10-28-nupkg-repository-build-v2`). `grade_without_roslyn_rule` retains Roslyn's
  grade from the first Windows run.
- `publisher-build/results/signature-stripped.txt` contains the whole-file checks for
  the 35 reproduced packages from the two Windows runs.
- `../tools/` contains the shared, unchanged `install-sdk.py`, `dllreport.cs` and
  `stripsign.cs`.

The trimmed scripts were run on a sample on 3 November and compared with the stored run:

- `run-batch.py`, with `derive.py`, `rebuild.py`, `compare.py`, `level.py`,
  `../tools/install-sdk.py` and `dllreport.cs`, was run on RBush 4.0.0 and
  FluentValidation 11.11.0 on `arch`. Both rows match the stored results: the same SDK
  and grade, A equal to A2, and the same differing lines. The `runner` column now
  contains `local` where the stored result contains `arch`. The recipes match the stored
  recipes except for their comment lines. The package listings match entry by entry
  except for NuGet's `_rels/.rels`, which receives a new ID on every pack. The same
  trial was run again in an empty lab after `run-batch.py` took over installing the
  report SDK and writing `results/`. It gave the same two rows and left the other 196
  rows and 84 package listings in `results/` byte-for-byte unchanged. The stored files
  were then put back.
- Cronos 0.9.0 was rebuilt again on GitHub's `windows-2022` runner (image
  20261026.347.1) through the working repository's workflow:
  [run 41599872747](https://github.com/peterjuulm/Speciale2026/actions/runs/41599872747).
  That workflow runs the working repository's `rebuild.py` at `f127442`, not the copy
  here. For this recipe both run the same commands: the recipe asks for no shallow clone
  and no extra runtime, the workflow sets no git mirror, and `install-sdk.py` and
  `compare.py` are byte-for-byte the same files. `run-batch.py` here derived the same
  recipe, apart from its comment line, and classified the run's output. The row matches
  the stored one in SDK, grade, A equal to A2 and differing lines. It differs in the
  runner image and in two labels: `ran` for `ran (success)` and `not tested` for `not
  tested (round B)`. The shipped `Cronos.dll` is byte-for-byte the DLL of the 27 October
  run.

The following were not run from this repository: `repo-build.py`, `run-repo-batch.py`,
and `stripsign.cs` on the eight release-build rows graded as identical without
signatures. The copy of `rebuild.py` here has not itself run on Windows.

Every recipe, `facts.txt`, build log and DLL report from the stored runs is available in
the working repository, [Speciale2026](https://github.com/peterjuulm/Speciale2026), at
`f127442` under `dependencies/experiments/nupkg/recipes/` and the data folders named
above.

The notes of record are `dependencies/notes/2026-10-26-nupkg-release-only.md` for the
rules, `2026-10-27-nupkg-release-only-batch2-v3.md`,
`2026-10-27-nupkg-release-only-batch3-microsoft.md` for version 3 and its run,
`2026-10-27-nupkg-repository-build-plan.md`, `2026-10-28-nupkg-repository-build.md`,
`2026-10-28-nupkg-repository-build-windows.md` and `2026-10-28-framework-synthesis.md`.
