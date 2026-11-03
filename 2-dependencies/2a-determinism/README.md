# Build determinism under environmental variation

We test whether the selected NuGet packages produce identical outputs across
different environmental conditions, with and without deterministic-build
configuration. Each comparison uses the same source commit and toolchain.

The experiment follows the reprotest approach and result categories used by
Benedetti et al. (2025) for Cargo, npm, Maven, PyPI and RubyGems. We apply it to
NuGet. Both outputs in each comparison are built locally; [part
2b](../2b-rebuild/) compares local builds with published assemblies.

## Method

### Population

We start with the 341 packages shipped with Phoenix
(`../population/results/shipped-packages.txt`, from its lock files). For each
package, `scripts/population.py` reads the repository URL and commit from the
package's `.nuspec` on nuget.org. It identifies the assembly under `lib/`,
fetches the repository at that commit and searches for the project file with the
same assembly name.

`population.tsv` contains one row per package, with the package, version,
repository, commit, project, assembly and status. Of the 341 rows, 224 contain
all required information. The remaining 117 record where the process stopped:

- 75 packages have no assembly matching the package name under `lib/`: 27 ship
  no managed code, 45 are Humanizer satellite packages, two place their
  assemblies under `runtimes/`, and one under `tools/`.
- 20 specify no commit.
- 11 specify no repository.
- 8 could not be fetched: 5 SkiaSharp and HarfBuzz packages use a dead `fwlink`
  URL, the server no longer provides the commit for 2 IdentityModel 8.19.2
  packages, and 1 request timed out.
- 3 have no uniquely identified project with the required assembly name.

Whether a row builds is a result, not a filter. `batch` records the first error
for every package that does not build.

### Toolchain and build preparation

We used .NET SDK 10.0.403 with NuGet 7.9.0-rc.2412. We installed it alone from
the official tarball after checking its SHA-512 checksum
(`../tools/install-sdk.py`). One online restore per package filled a shared
package cache. Every measured build runs with `--no-restore` from a clean clone
at the declared commit (`core.autocrlf=false`, with submodules initialised).

When a repository's `global.json` pins an SDK unavailable in the lab, the pin is
removed and the row records the pinned version. This applies to 80 of the 127
measured packages. Another 46 have no pin, while DiaSymReader's pin is retained.

All builds ran on one machine with Arch Linux, kernel 7.2.11, glibc 2.44,
reprotest 0.7.32, disorderfs 0.6.2 and faketime 0.9.13.
`results/environment.txt` contains the full environment record.

### Build commands

Two commands are used:

| mode | command |
|---|---|
| default | `dotnet build PROJECT -c Release --no-restore && dotnet pack PROJECT -c Release --no-build -o out` |
| configured | the same plus `-p:ContinuousIntegrationBuild=true -p:Deterministic=true -p:DeterministicTimestamp=<commit time>` |

Both include `-p:UseSharedCompilation=false` to disable the compiler server,
which hangs under the `time` variation.

The default command builds and packs a cloned project as a consumer would. This
is Benedetti's “as is” category. The configured command is Benedetti's
“reproducible with infrastructure configuration” category. It sets the three
properties the .NET ecosystem offers for deterministic output: source paths
mapped to `/_/`, deterministic compilation and fixed ZIP entry times. It does
not reproduce configuration from the publisher's CI.

### Environmental variations

The experiment applies reprotest's eight variations one at a time, each against
its own control build: `build_path`, `environment`, `locales`, `exec_path`,
`time` (with the clock approximately one year ahead), `timezone`, `umask` and
`fileordering` (disorderfs).

`kernel` is not varied because it requires a second kernel. `user_group` and
`domain_host` are also excluded. Reprotest runs both through `sudo`, and the lab
ran as an ordinary user without it.

### Comparison and classification

Each pair of builds is compared at three levels:

| level | compares |
|---|---|
| 1 whole file | the `.nupkg` byte for byte |
| 2 content | every archive entry by bytes, except NuGet's packaging files (`nuget.psmdcp`, `_rels/.rels`, `[Content_Types].xml`) |
| 3 DLLs | the assemblies (`.dll`, `.exe`) under `lib/`, `ref/`, `runtimes/` |

Each combination of package, mode and axis receives one of three verdicts:
`same`, `differs` (including the first differing entry) or `failed` (when a
build produces no package).

Packages from each run are paired by package ID rather than file name because
two packages include the clock in their version. Symbol packages are not
compared.

At each comparison level, packages are assigned to the categories in Benedetti's
Figure 3:

- *As is* means that every default run is `same`.
- *With configuration* means that every difference in the default builds has a
  configured run that is `same`.
- *Unreproducible* means that at least one configured run still differs or
  fails.

## Running the experiment

Run from `2-dependencies/2a-determinism/` on Linux, with Python 3.11 or later,
git, network access, reprotest 0.7.32 (`pipx install reprotest==0.7.32`) with
disorderfs, faketime and the `et_EE.UTF-8` locale, and `pwsh` on `PATH` for the
Azure packages. The lab needs about 40 GB outside any repository.

1. One SDK, installed alone. `environment` reads the SHA-512 from the log.

```bash
LAB=$HOME/determinism-lab && mkdir -p $LAB/tmp
python3 -I ../tools/install-sdk.py 10.0.403 $LAB/sdk | tee $LAB/install-sdk.log
```

2. Everything, from `population.tsv` to `results/`. Every package, eight axes,
   both modes. `TMPDIR` keeps reprotest's build trees out of `/tmp`. On the
   recorded machine, `/tmp` was a 31 GB tmpfs, and four parallel batches over
   the Roslyn, EF Core and Azure SDK trees did not fit in it.

```bash
TMPDIR=$LAB/tmp python3 -I scripts/build-and-compare.py batch population.tsv $LAB
python3 -I scripts/build-and-compare.py results $LAB results/runs.tsv
python3 -I scripts/build-and-compare.py environment $LAB && cp $LAB/environment.txt results/
```

3. The tables.

```bash
python3 -I scripts/summary.py $LAB results    # results/summary.md, results/categories.tsv
```

## Results

The experiment ran on `arch` from 2 November at 17:43 to 3 November at 08:49,
2026. The 1008 verdicts from the 1 to 2 November run were carried over
unchanged. The remaining packages were built during the night of 2 November.
Runs that failed with the full `/tmp` were repeated on the morning of 3
November, as described under Caveats.

Of the 224 eligible rows, 127 packages from 68 repositories built and were
measured. The remaining 97 did not build with the default command.

`results/runs.tsv` contains 2214 rows:

- 16 runs for each of the 127 measured packages, covering eight axes and two
  modes;
- 85 runs using all eight variations at once, carried over from 1 November;
- one row for each of the 97 packages that did not build.

`scripts/summary.py` generates the result tables from these rows and writes them
to `results/summary.md`.

### Reproducibility by package

The Figure 3 categories for the 127 measured packages are:

| level | as is | with configuration | unreproducible |
|---|---|---|---|
| 1 whole file | 0 | 102 | 25 |
| 2 content | 4 | 98 | 25 |
| 3 DLLs | 4 | 98 | 25 |

No package is reproducible as is at the whole-file level because NuGet stamps
every ZIP entry with the build time. `DeterministicTimestamp` removes this
source of variation.

Four packages are reproducible as is at both the content and DLL levels:
CsvHelper, FluentValidation, FluentValidation.DependencyInjectionExtensions and
ScottPlot. They set `ContinuousIntegrationBuild` in their own project files.

Configuration resolves the content and assembly differences for another 98
packages. This gives 102 successful packages at all three levels. Of the
remaining 25, 23 have byte differences and two fail during the time variation.
The diagnoses below separate build logic that uses the clock or path from
failures involving npm and the clock-manipulation tool.

### Differences by axis in the default build

The table counts how many of the 127 packages differ between the two default
builds on each axis:

| axis | whole file | content | DLLs | build failed |
|---|---|---|---|---|
| build_path | 127 | 123 | 123 | 0 |
| time | 125 | 18 | 18 | 2 |
| environment, locales, exec_path, timezone, umask, fileordering (each) | 127 | 5 | 5 | 0 |

`build_path` produces the most assembly differences in this population. The
compiler writes absolute source paths into the PDB and the PDB ID into the DLL.
The DLL therefore varies with the path unless PathMap is enabled.

For the other six variations, content and assembly differences occur only in the
five IdentityModel 8.23.0 packages whose versions include the clock. Two builds
a minute apart receive different versions. A difference under each axis
therefore does not establish that each axis independently caused it.

`time` affects 18 packages: those five packages and 13 others whose build logic
reads the clock.

### Packages not fixed by configuration

The causes for the 25 packages that remain unreproducible after configuration
are:

| cause | packages | axis | where the difference is |
|---|---|---|---|
| date in the package version | Azure.Core, Azure.Identity, Azure.Storage.Blobs, Azure.Storage.Common, Azure.Security.KeyVault.Certificates, Azure.Security.KeyVault.Secrets, Azure.Communication.Email, System.ClientModel (8) | time | `X.Y.Z-alpha.<yyyymmdd>.1` in nuspec, file name and assembly attributes |
| clock in the package version | Microsoft.IdentityModel.Abstractions, JsonWebTokens, Logging, Tokens, System.IdentityModel.Tokens.Jwt 8.23.0 (5) | every axis | `8.22.1-preview-<yMMddHHmmss>`: two builds a minute apart differ |
| copyright year from the clock | Swashbuckle.AspNetCore.Swagger, SwaggerGen, Annotations 7.2.0; Stateless 5.16.0 (4) | time | `$([System.DateTime]::Now.ToString(yyyy))` in `Directory.Build.props` line 10 and `Stateless.csproj` line 9, into `AssemblyCopyright` |
| npm in the build | Swashbuckle.AspNetCore.ReDoc, SwaggerUI 7.2.0 (2) | time (build fails) | the project runs `npm`; Node does not run under libfaketime |
| Arcade's date-based build number | Microsoft.Build.Framework 18.0.2 (1) | time | `AssemblyFileVersion` 18.0.2.55101 against .60401, from `DateTime.Now` when `OfficialBuildId` is empty |
| a hash of the project path in the PDB | Quartz, Quartz.AspNetCore, Quartz.Extensions.DependencyInjection, Quartz.Extensions.Hosting 3.13.1 (4) | build_path | LibLog ships source as `.cs.pp` content files; the SDK writes them to `obj/.../NuGet/<hash of the project path>/`; the folder is a PDB document name, PathMap maps the prefix and not the hash; the DLL follows through its PDB id |
| the PDB path unmapped | ClosedXML 0.104.2 (1) | build_path | the DLL's debug directory names the PDB by its absolute path (`/tmp/reprotest.*/.../ClosedXML/obj/Release/netstandard2.1/ClosedXML.pdb`, where a repaired package says `/_/...`); the repository rewrites the DLL after compiling (Fody 6.3.0, which writes through Mono.Cecil), pins Microsoft.SourceLink.GitHub 1.1.1 over the SDK's Source Link, and declares `SourceRoot` as a property; which of the three defeats PathMap is not isolated |

### Packages that did not build

The first error for each of the 97 packages that did not build is recorded in
`results/summary.md`.

The failures are:

- 50 are dotnet/runtime libraries, including Microsoft.Extensions.*, System.*
  and Microsoft.Bcl.*. Their projects read the targeting pack from the
  repository build: “the shared framework must be built before the local
  targeting pack can be consumed.”
- 10 are ASP.NET Core 10.0.12 packages whose restore requires prune-package data
  unavailable in the SDK (NETSDK1226).
- 7 ASP.NET Core 6 to 9 packages import a generated `Directory.Build.props`
  (MSB4019).
- 6 fail to compile at the commit (CS0234): the Svg 5.1.1 family and
  System.IO.Hashing 6.0.0.
- 4 IdentityModel 8.7.0 packages reject their own version string (CS7035).
- 2 fail in an MSBuild task (MSB4018): Dapper's Nerdbank.GitVersioning and
  System.IO.Hashing 7.0.0's package validation, which reads a file generated by
  the repository build.
- 2 fail because the repository treats a compiler warning as an error (CS8625):
  DocumentFormat.OpenXml 3.1.1 and its Framework package.
- 2 fail on an analyzer (IDE0055): NuGet.DependencyResolver.Core and
  NuGet.ProjectModel.
- 2 read from a feed that is no longer available or is internal (NU1301).
- 2 require a newer SDK for the .NET task host:
  Microsoft.Extensions.Logging.Abstractions and System.Text.Json 10.0.12.
- The remaining 10 fall into separate failure categories.

For 50 of the 224 candidates, the project depends on outputs from the
publisher's repository build and cannot be built independently by the
experimental command.

### Additional measurement

For 62 of the 127 packages, the default build produces a package whose file name
does not contain the released version. The causes include `1.0.0` defaults,
Arcade's `-dev`, `-alpha.<date>`, `-rc.32767`, the clock and `-g<commit>`. For
these packages, the publisher's CI supplies the version rather than the
repository at the declared commit.

### Comparison with Benedetti et al.

At the whole-file level, 0% of packages are reproducible as is, 80% are
reproducible with configuration and 20% remain unreproducible. “As is” is
Benedetti's term for the default build.

The reported rates are Maven (2.1% as is and 92.6% with configuration), RubyGems
(0% and 97.1%) and PyPI (12.2% as is). Cargo and npm were reported as 100% as
is.

Three differences in the study designs limit a direct comparison:

- This experiment measured 127 packages from 68 repositories, whereas Benedetti
  et al. measured 4000 randomly selected packages per ecosystem. The 25
  unreproducible packages in this experiment come from seven repositories.
- No patched package manager was tested.
- The `time` variation used reprotest's full range, which Benedetti et al.
  reduced.

## Caveats

- The experiment uses one machine, one Linux distribution and one SDK. Windows
  is excluded because reprotest runs only on Linux.
- Each axis has one control build and one build per variation. A difference is
  observed directly. Equality means that no difference was detected.
- The night run of 2 November took place while `/tmp` was 98% full because a
  population check had left 29 GB of scratch clones. As a result, 442 runs and
  11 screens failed with “No space left on device” and were repeated on 3
  November.
- A further 38 runs across 13 packages from the Azure SDK, Roslyn and EF Core
  failed in reprotest's testbed for a second time because of insufficient space
  or a failed copy into the testbed. Four parallel copies of these source trees
  do not fit in the 31 GB tmpfs. These runs were repeated a third time with
  `TMPDIR` on disk. The final two runs, one affected by a copydown timeout and
  one missing from a state file, were run with one worker.
- Every `same` and `differs` verdict comes from a run in which both builds
  completed. Only `failed` verdicts were repeated. Logs from the removed runs
  remain in the working repository as `*.nospace.log`, `*.nospace2.log` and
  `*.nospace3.log`.
- The 127 measured packages are the subset of Phoenix's dependencies that have a
  project-level build under one Linux SDK. They are not a sample of NuGet.
- The proposed causes and fixes are diagnoses, not tested interventions. The
  diagnosis for ClosedXML is the least certain.
- Restore ran online once per package. The measured builds used `--no-restore`
  but did not run inside a network namespace.

## Data and scripts

```
2a-determinism/
  README.md
  population.tsv              the 341 shipped packages with repository, commit, project and status; 224 are `ok`
  figures/
    method.drawio             the command sequence as a figure; method.drawio.png is its export
  scripts/
    population.py             derives population.tsv from ../population/results/shipped-packages.txt
    build-and-compare.py      the driver: try-build, build-twice, batch, results, environment
    summary.py                the tables: results/summary.md and categories.tsv from the lab
  results/
    runs.tsv                  one row per run (package, mode, axis, verdict at three levels)
    categories.tsv            one row per package with its category at each level
    summary.md                the tables printed by summary.py
    environment.txt           host, SDK and tools as they were when the run was made
```

- `scripts/build-and-compare.py` is the experiment driver. Four copies of
  `batch` ran in parallel over disjoint slices of `population.tsv`. `batch` is
  resumable. The reruns on 3 November used the same command over the slices
  after the failed runs had been removed from the state files. The second and
  third reruns used `TMPDIR=$LAB/tmp`. The 1008 verdicts carried over from 1
  November were produced by the first version of the driver in the working
  repository. On 2 November, the current version was checked against the stored
  runs and produced the recorded verdict for every run from that lab. `batch`
  skips a package whose result is recorded. A package takes 2 to 3 minutes per
  axis and mode, and a Roslyn package takes 30. One package by hand:
  `scripts/build-and-compare.py try-build population.tsv Quartz $LAB`, then
  `build-twice population.tsv Quartz $LAB default build_path` (or `configured`,
  or another axis). The lab's `pwsh` was PowerShell 7.6.9 installed as a dotnet
  tool (`$LAB/sdk/dotnet tool install PowerShell --version 7.6.9 --tool-path
  $LAB/tools`). The driver puts `$LAB/tools` on `PATH` ahead of the host's.
- `scripts/summary.py` generates the tables and reproduces `results/summary.md`
  and `results/categories.tsv` from the lab (checked 3 November).
- `../population/results/shipped-packages.txt` contains the 341 packages shipped
  with Phoenix and is the experiment's only input.
- `scripts/population.py` derives `population.tsv`, which contains 341 rows with
  repository, commit, project and status.
- `figures/method.drawio` shows the method. `figures/method.drawio.png` is its
  exported preview. Regenerate it from this folder with `drawio -x -f png -e -s
  2 -b 10 -o figures/method.drawio.png figures/method.drawio`.
- `results/` contains `runs.tsv` (one row per run), `categories.tsv` (one row
  per package), `summary.md` and `environment.txt`.
- Every build log, comparison and file list is stored in the working repository,
  [Speciale2026](https://github.com/peterjuulm/Speciale2026), under
  `dependencies/data/2026-11-02-determinism/`, with the result note
  `dependencies/notes/2026-11-03-determinism.md`. The earlier run from 1 to 2
  November, based on a population of 90 packages, is stored under
  `dependencies/data/2026-11-01-determinism/` with its note
  `dependencies/notes/2026-11-01-determinism.md`.
