# Experiment 1: Rebuilding Phoenix

A build is reproducible when the same source always gives the same bytes.
Then anyone can check that a binary was made from the source it names. This
experiment asks whether the WS.Phoenix release can be built so that two
builds give bit-identical output, also when the build environment changes.
Which properties of the build environment change the bytes of each stage,
and can each cause be removed?

WS.Phoenix is Weel-Sandvig's product: four .NET assemblies, about 300 NuGet
dependencies, a Next.js frontend, release zips and container images. Before
Phoenix, we built one empty C# class to test the set-up and the method:
build twice, hash every file, compare, find the cause, fix, and build again.

## Method

### The stage plan

The release is built in six stages. Each stage adds its own possible
sources of difference, so each is measured on its own before the next.

| Stage | What is built | What is compared |
| --- | --- | --- |
| 1 Build | `dotnet build -c Release` | Our DLLs and PDBs, `deps.json`, `runtimeconfig.json` |
| 2 Publish | `dotnet publish`, the release's own commands | The publish folder: our assemblies, dependencies, the .NET runtime |
| 3 Frontend | `npm ci` + `next build` | The static export: HTML, JavaScript, CSS |
| 4 Zip | The release zips | The archive's bytes |
| 5 Container | The OCI images | Image manifest and layers |
| 6 Other release outputs | Database migrator, SQL script, checksum file, Windows release, signing | Each file the release ships |

Stages 1-3 are loose files. Stages 4 and 5 are archives, which also store
file times, modes and order. The fixes were made on the WS.Phoenix branch
`thesis/reproducible-builds`. [scripts/commits.md](scripts/commits.md)
lists its commits, oldest first, and marks the before and after commit of
each stage.

### Set-up

All builds ran on one Arch Linux laptop. These conditions make sure that the
environment is what we say it is, and that the only difference between two
builds is the one we chose:

- The source is an exact export of one commit (`git archive`), outside git,
  checked file by file before each batch.
- The SDK is pinned by `global.json`: Microsoft's 9.0.120, from 12 October
  2026 10.0.401. The compiler's SHA-256 is recorded with each run.
- Each run starts clean (no `bin/`, `obj/`) and only one build runs at a
  time.
- .NET's build servers are stopped before and after each build, so the
  second build cannot reuse a process that the first build started.
- reprotest starts from an empty environment with five listed variables.

### Instrument

**reprotest** 0.7.32 builds the project twice, changes one property of the
environment between the two builds, and compares the outputs. The axes used:
build path, time, locale, umask, `PATH`, time zone, environment variables,
home folder, kernel, CPU count, user, and all at once. **diffoscope** 329
shows which bytes differ. The verdict is a SHA-256 hash of every output
file. Where diffoscope's report was not enough, a reader for that file type
was used (PDB, zip header, OCI image).

Every stage follows the same procedure:

1. Two clean builds at the same path.
2. reprotest, one axis per run, then all axes at once.
3. Each difference traced to its file and field, fixed on the branch, and
   the run repeated.

### What is particular to each stage

Stage 1, build. The first same-path test built the whole solution and hashed
all 1610 files under `bin/Release`, tests included. The reprotest runs build
only the two programs, `WebAPI` and `BackgroundJobExecutor`, with the
projects they reference. They hash our DLLs, PDBs and `.json` files.

Stage 2, publish. The release job's own commands: a locked restore and two
self-contained `linux-x64` publishes, with the release's version flags. NuGet
lock files pin every package by content hash. Measured first without, then
with the frontend export in `wwwroot/`, as CI ships it. With `rt.sh`, stage
2 runs on SDK 9, at `4e5237a33`. Its `build.sh` is the release job at that
commit, with the locale pinned, and fits from `84d73a2f6` to before
`5031c5af`. The publish on SDK 10 is measured inside stage 4, which hashes
the unpacked release folders as well as the zips.

Stage 3, frontend. Built from an export of the whole commit, because the
frontend imports code from outside its own folder. Node pinned to one
version; `npm ci --offline` from a filled cache. Where an order varied
between builds, webpack logged its order and was delayed on purpose, to
confirm the cause before the fix.

Stage 4, zip. The zips packed as CI packs them (`zip -r`), and with a
normalised packing: fixed times, sorted names, fixed modes, no extra fields.
Compared entry by entry: name, content, time, mode, owner, order. Only with
no variation and with all axes at once.

Stage 5, container. Built as the release job builds them, with BuildKit and
no cache, as two plain builds outside reprotest. Compared by manifest,
config, and layer by layer. Repeated with the commit's time as
`SOURCE_DATE_EPOCH` and BuildKit's `rewrite-timestamp`.

Stage 6, other release outputs. The release job's own commands for each
output. The database migrator built from two exports at two paths. The SQL
script from two exports, the second under another locale and time zone. The
Windows release built on Linux as its CI job builds it, under no variation,
all axes and the Estonian locale. The Windows binaries signed twice with a
test certificate, and the signatures then copied onto an unsigned rebuild,
since a signature carries its own timestamp.

### Unit of measurement

The unit is the SHA-256 hash of each output file. A stage is green when
every hash is the same in both builds, and red otherwise. A difference
counts even when it looks harmless. Counts are given as differing files out
of all files.

## Running the experiment

### What the machine needs

The defaults point at Leo's laptop. Each can be changed with the variable in
brackets; see the first lines of `make-lab.sh` and `rt.sh`.

- The WS.Phoenix repository with the branch `thesis/reproducible-builds`, in
  `~/Dev/Weel-Sandvig/WS.Phoenix-repro` (`REPO`).
- The .NET SDKs 9.0.120 and 10.0.401 in `~/.dotnet` (`DOTNET_DIR`). The lab's
  `global.json` chooses one.
- Node 20.20.2 in `/opt/rb1-node` and Node 22.23.3 in
  `/private/tmp/rb1-node22` (`NODE_DIR`). The frontend's `.nvmrc` chooses
  one.
- For stages 3, 4 and 6: the npm cache `/private/tmp/rb1-npm`, filled once
  by `npm ci` with network in an export of the frontend.
- For stages 4 and 6: Info-ZIP 3.0 as `/private/tmp/rb1-tools/zip`, which
  `pack-release-zip.sh` gets first on its `PATH`.
- reprotest 0.7.32 and diffoscope 329 on `PATH`, from pipx.
- For stage 5: Docker with a buildx builder named `rb1`.

### One run

One run is two commands, from `scripts/`. Look up the stage's commit in
[commits.md](scripts/commits.md) first. Here stage 3, at `2cd85fd01`, with
no variation:

```bash
shared/make-lab.sh 2cd85fd01
env OUT=$HOME/Dev/speciale-2026/data/$(date +%F)-stage3 shared/rt.sh 3-frontend none
```

`$(date +%F)` is today's date, as in `2026-11-11`, in bash and in fish.

`make-lab.sh COMMIT` exports the commit into an empty lab,
`/private/tmp/rb1-phoenix`.

`rt.sh STAGE AXIS` checks that the lab holds no build output. It finds the SDK and Node that the
commit asks for, runs reprotest, and writes the run's folder and one row in
`OUT/summary.tsv`. AXIS is `none`, one reprotest variation such as
`build_path`, or `all`. A run takes about 5 minutes for stages 1 and 2.

- Make the lab again when you change commit, and after running a `build.sh`
  by hand in it. A run with `rt.sh` leaves the lab clean, because reprotest
  builds in its own copies.
- Run one stage at a time: none first, then single axes, then all. When all
  is red, single axes find the cause.
- Run one heavy build at a time. Two at once ran the laptop out of memory on
  13 October.
- In fish, write `$HOME` and not `~` after `OUT=`; fish does not expand it
  there. `rt.sh` stops if you do.
- Each `build.sh` also runs by hand, without reprotest, from inside a lab.
  Its first lines show how. That is the quickest way to see a build fail.

Stage 5 runs outside reprotest:
`OUT=<folder> [EPOCH=<seconds>] 5-images/image-probe.sh COMMIT LABEL`.

### Comparing two builds of a DLL

When a run is red, the run's `store/` holds the kept files of both builds,
under `control/source-root/` and `experiment-1/source-root/`.
[dllreport.cs](../2-dependencies/tools/dllreport.cs) writes one report per
DLL: a hash for each part, the debug entries and the PDB's paths. A diff of
two reports shows which parts differ, and often why. From inside `store/`:

```bash
dotnet run ~/Dev/dotnet-rebuild-experiments/2-dependencies/tools/dllreport.cs -- control/source-root/PATH/X.dll > /private/tmp/report-control.txt
dotnet run ~/Dev/dotnet-rebuild-experiments/2-dependencies/tools/dllreport.cs -- experiment-1/source-root/PATH/X.dll > /private/tmp/report-experiment.txt
diff /private/tmp/report-control.txt /private/tmp/report-experiment.txt
```

It needs a .NET 10 SDK, so run it outside a lab whose `global.json` asks
for 9.0.120. The report reads the PDB next to the DLL. When the two files'
`sha256` differ but every part in the reports is equal, the difference lies
outside the parts that `dllreport.cs` reads, such as the entry point.

### Runs with rt.sh

`rt.sh` replaced the old drivers on 9 November 2026, so the results below
came from them. Since then, stage 1 has been run with `rt.sh` before and
after the fixes: identical under none, and under `build_path` different
after the fixes only in the two development files. Stage 2 gave identical
with none on 9 November and with all on 11 November, with the same hashes
both days. Stages 3, 4 and 6 have not been run with `rt.sh` yet.

## Results

Every stage that ships became bit-identical on every axis we ran. Two
development files in stage 1 still differ with the build path; they are not
part of the release.

Stages 1 and 2 were deterministic from the start and differed only when the
environment changed: the build path and the locale. Stages 3, 4 and 5
differed even between two builds in the same environment: a random build
ID, orders that followed build timing, and timestamps in archives and
images. Most causes belong to the tools, not to Phoenix: the compiler's
culture-dependent order, the SDK 10 timestamps, and webpack's
timing-dependent order. Signed files can never be rebuilt byte for byte,
because each signature carries its own timestamp; a rebuild is checked by
copying the release's signatures onto it.

Every finding has an id and is listed twice in [findings/](findings/):
[by stage](findings/by-stage.md), before and after the fixes, and
[by cause category](findings/by-category.md).

### Stage 1: build

| Test | Differing files | Cause | Fix |
| --- | --- | --- | --- |
| Same path | 0 of 1610 |  | None needed |
| Build path | All 10 compared | Absolute paths in the PDBs and in the DLLs; type names generated from source paths; Razor-generated code with absolute paths | `PathMap`: the compiler writes `/_/` instead of the build folder. Two unused Razor pages deleted, as `PathMap` does not reach their paths |
| Build path, after fix | 2 dev files | The build path in plain text (`spa.proxy.json`, `staticwebassets.runtime.json`) | Not fixed: development only, not in the release |
| Locale (Estonian) | Our 4 assemblies | The compiler sorts generated type names by the culture's rules | `LC_ALL=C.UTF-8`: the compiler sorts with culture-neutral rules |
| All other axes | 0 |  | None needed |

### Stage 2: publish

| Test | Differing files | Cause | Fix |
| --- | --- | --- | --- |
| Same path, first runs | Extra and wrong files | An empty `package-lock.json`, committed by mistake, shipped; Windows libraries shipped in the Linux release; `deps.json` listed our libraries as version 1.0.0 | Stray file deleted; platform setting on the two programs only; version flags on the restore too |
| Same path, after fix | 0 of 1237 |  |  |
| Locale (Estonian) | 10 of 1237 | The same compiler defect as in stage 1 | `LC_ALL=C.UTF-8`: 0 |
| All axes at once | 10 of 1237 | Only the locale; no other axis changed a byte | The same locale fix: 0 |
| Umask | 0 contents | 142 file modes follow the umask | None here; stage 4 sets the modes |
| With the frontend | 0 of 2227 |  | None needed |
| SDK 10 | 1 file | The SDK dated the compressed copies of static files with the time it wrote them | Compression off (`CompressionEnabled=false`); the app never used the copies. Then 0 of 2121 |

On SDK 10 the locale defect was gone.

### Stage 3: frontend

| Test | Differing files | Cause | Fix |
| --- | --- | --- | --- |
| Same path | 110 of 998 | Next.js draws a random build ID in every build and writes it into paths and pages | Build ID set to the release version (`generateBuildId`) |
| Repeated builds | 4 of 998, in 1 of 4 builds | Two stylesheets in another order | All third-party CSS imported once, in a fixed order, in `_app.tsx` |
| Every axis, 26 builds | 109 of 990 | Two different outputs, 12 and 14 times: webpack's page order followed the timing of file reads | A webpack plugin sorts the pages by name before the chunks are made |
| About 1 in 50 builds | 5 | Two identical chunks swapped ids | The same plugin also sorts the modules and their links |
| After the fixes | 0 |  |  |

### Stage 4: zip

| Test | Result | Cause | Fix |
| --- | --- | --- | --- |
| As CI packs, no variation | Different every build | 1237 of 1847 entries with other times; 140 positions in another order | Normalised packing: the commit's time on every file, fixed modes (755 or 644), sorted names, no owner fields (`zip -X`), UTC |
| As CI packs, all axes | Different | Also modes and owner | The same packing |
| Normalised packing | Identical in 4 builds |  |  |

### Stage 5: container

| Test | Result | Cause | Fix |
| --- | --- | --- | --- |
| WebAPI and job worker images | Different | Times only: config and 123 of 1408 file entries | `SOURCE_DATE_EPOCH` set to the commit's time; BuildKit sets later file times to it (`rewrite-timestamp`) |
| Three MCP images | Different | Caches written during the build | Each cache deleted in the step that writes it |
| Image tags | Different every build | Attestations hold the build's clock time and a random id | None; compare the image manifest, not the tag |

### Stage 6: other release outputs

| Test | Result | Cause | Fix |
| --- | --- | --- | --- |
| Database migrator, two paths | 93 of 827,679,078 bytes differ | `dotnet ef migrations bundle` builds the migrator in a random `/tmp` folder, and that path reaches the binary | Migrator kept as a project in the repository, where `PathMap` applies: identical |
| SQL script | Identical |  | None needed |
| Windows release, built on Linux | 2132 files identical under no variation, all axes and the Estonian locale |  | None needed |
| Checksum file | Line order follows the locale | The shell lists the files in the locale's sort order | `LC_ALL=C` before the file list |
| Windows signing, twice | 177 files and both zips differ | Each signature carries its own timestamp | Copy the release's signatures onto the rebuild: identical |

## Caveats

- The runs above were on one machine. The checks across machines (GitHub's
  runner, the laptop and a Mac) are in
  [findings/by-stage.md](findings/by-stage.md), under "Across machines".
- Not every axis was run: file order needs `disorderfs`, which this machine
  does not have. ASLR alone cannot be varied with reprotest. Stages 4 and 5
  were tested with fewer axes than stages 1-3.
- Few repetitions: many results rest on two builds. Rare races were found
  only by repetition, about once in 50 builds.
- Hashes before and after the SDK change (12 October 2026) do not compare.
- The Windows release was built on Linux, as its CI job builds it, not on
  Windows.
- `rt.sh` compares file contents only. The 142 file modes that follow the
  umask in stage 2 (W30) are not seen by it.
- Not reported to the tools' maintainers yet: the compiler's locale order,
  the SDK 10 timestamps, and webpack's orders in Next.js.

## Data and scripts

```
1-phoenix/
  README.md
  figures/                      four figures as .drawio and .drawio.png; figures/README.md explains each step
  findings/
    by-stage.md                 every finding, stage by stage, before and after the fixes
    by-category.md              the same findings by cause category
  scripts/
    commits.md                  every commit on the branch; marks each stage's before and after
    shared/
      make-lab.sh               exports a stage's commit into an empty lab
      rt.sh                     runs reprotest once: one stage, one axis
      sample-dotnet.py          records the dotnet and node processes once a second during a run
      labcheck.py               checks that a lab is an exact copy of a commit; image-probe.sh and migrator-probe.sh use it
    1-build/
      build.sh, artifacts.txt   dotnet build of the two programs; keeps the bin folders whole
      pdbdump/                  prints a PDB's document table and embedded sources; found the Razor paths PathMap misses (W7)
    2-publish/
      build.sh, artifacts.txt   the locked restore and two self-contained linux-x64 publishes; keeps release/ whole
    3-frontend/
      build.sh, artifacts.txt   npm ci --offline and next build; keeps the static export. Stages 4 and 6 run it first
      compare-chunks.py         compares two webpack chunk logs (W51)
    4-zip/
      build.sh, artifacts.txt   stage 3, the publishes with the export, the zips; keeps the two zips
    5-images/
      image-probe.sh            builds each .NET image twice as the release job does and compares them
      oci-diff.py               compares two OCI images: manifest, config, each layer's files
      oci-file.py               extracts one file from an OCI image
      attest-compare.py         which fields of the provenance and SBOM differ between two images
      attest-layers.py          whether the layers named in the provenance are the image's layers
      ghcr-manifests.py         compares a pushed image tag with a local image by manifest
      faketime-tests.sh         checks that the images' build-time tests still pass one year later
    6-other/
      build.sh, artifacts.txt   the Windows release built on Linux, unsigned; keeps the two zips and the migrator
      migrator-probe.sh         builds the migrator twice at two paths, for linux-x64 and win-x64
      signing-probe.sh          signs two Windows builds with a test certificate and pastes the signatures across
      signing-paste.sh          repeats the paste step with two more negative controls
    ci/
      ci-local.sh               rebuilds each job of the release workflow locally from a tag
      ci-compare.sh             compares every CI output with the rebuild; exits 1 on any difference
      ci-compare-tests.sh       checks that ci-compare.sh reports a difference when there is one
```

Each stage that reprotest runs is a folder with `build.sh`, what each build
does, and `artifacts.txt`, what reprotest keeps so diffoscope can explain a
difference. The verdict is `hashes.sha256`, which `build.sh` writes: one
hash for every file the stage produces. Scripts that build a release call
Phoenix's own scripts from the measured commit, such as
`pack-release-zip.sh`. Those are not copied here.

The runs' data are in `~/Dev/speciale-2026/data/`, which is private: they
hold Weel-Sandvig's build output. The finding ids (E, W, R, T) are the rows
of `notes/findings-table.md` in
[Speciale2026](https://github.com/peterjuulm/Speciale2026).

### Old and new paths

The scripts were copied on 4 November 2026 from `experiments/` in
Speciale2026. On 9 November 2026 `rt.sh` and the `build.sh` files replaced
the three old reprotest drivers. The notes in Speciale2026 use the old
paths, and the originals are still there.

| Speciale2026 `experiments/` | Here, `scripts/` |
| --- | --- |
| `phoenix-rt/run.sh`, `phoenix-rt-human/run.sh` | `shared/rt.sh` and each stage's `build.sh`. Mode `1` is `1-build`, `2` is `2-publish`, `R` and `Z` are `4-zip`, `W` is `6-other` |
| `phoenix-fe/run.sh` | `shared/rt.sh 3-frontend` |
| `sample-dotnet.py`, `labcheck.py` | `shared/` |
| `pdbdump/` | `1-build/pdbdump/` |
| `pe-diff-regions.py`, `md-strings.py` | Removed on 11 November 2026; `2-dependencies/tools/dllreport.cs` shows which parts of two DLLs differ |
| `phoenix-fe/compare-chunks.py` | `3-frontend/` |
| `phoenix-rt/image-probe.sh`, `oci-*.py`, `attest-*.py`, `ghcr-manifests.py`, `faketime-tests.sh` | `5-images/` |
| `phoenix-rt/migrator-probe.sh`, `signing-*.sh` | `6-other/` |
| `phoenix-rt/ci-*.sh` | `ci/` |
