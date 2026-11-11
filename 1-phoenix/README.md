# Rebuilding Phoenix

We test what is needed to rebuild a Phoenix release byte for byte across
machines. The method and results will be added here.

- [experiment-1.md](experiment-1.md): the short version of method and results,
  stage by stage.
- [figures/](figures/): `build-publish-pack` (the steps of `dotnet build`,
  `publish` and `pack`), `sdk-processes` (how one build chooses its
  processes' runtimes) `npm-build` (the frontend's `npm ci` and
  `npm run build`) and `npm-findings` (only what the frontend findings need). Each as `.drawio` and exported `.drawio.png`;
  [figures/README.md](figures/README.md) explains every file and step.
- [findings/](findings/): every finding in two views,
  [by stage](findings/by-stage.md) (before and after the fixes) and
  [by cause category](findings/by-category.md).
- [scripts/](scripts/): the scripts needed to redo the experiment, listed
  below.

## Scripts

Copied on 4 November 2026 from `experiments/` in Speciale2026. On 9 November
2026 we sorted them into one folder for each stage, in the order of
[experiment-1.md](experiment-1.md), and gave every stage that reprotest runs
the same form. The defaults point at Leo's machine (`/home/leos/...`,
`/private/tmp/rb1-*`). Scripts that build a release call Phoenix's own
scripts from the measured commit (`pack-release-zip.sh` and others). Those
are not copied here.

```
scripts/
  shared/       make-lab.sh, rt.sh and the checks that several stages use
  1-build/      the two programs: WebAPI and BackgroundJobExecutor
  2-publish/    the two programs and their dependencies, self-contained
  3-frontend/   npm ci and next build: the static export
  4-zip/        the Linux release zips
  5-images/     the OCI images
  6-other/      the Windows release, the migrator and the signing
  ci/           a CI release run against a local rebuild, all stages
```

Every stage that reprotest runs is a folder with two files: `build.sh`,
what each build does, and `artifacts.txt`, what reprotest keeps and
compares. One run is two commands, from `scripts/`:

```
shared/make-lab.sh COMMIT
env OUT=$HOME/Dev/speciale-2026/data/DATE-NAME shared/rt.sh STAGE AXIS
```

`make-lab.sh` exports the commit into an empty lab. `rt.sh` finds the SDK
and Node that the commit asks for, runs reprotest, and writes the run's
folder and its row in `summary.tsv`. Make the lab again before each run.
Stage 5 is the exception: the images are built outside reprotest, with
`5-images/image-probe.sh`.

### `shared/`

| Script | What it is for |
| --- | --- |
| `make-lab.sh` | Makes the lab: deletes it, exports one commit into an empty folder with `git archive`, and writes the commit's id and time beside it |
| `rt.sh` | Runs reprotest once on a stage folder's `build.sh`: one stage, one axis. Each run gets its own folder with the command, the environment, the log and reprotest's store, and one row in `summary.tsv`. Not the `user_group` axis, which needs a second user |
| `sample-dotnet.py` | Samples the dotnet or node processes once a second during a run. Shows whether reprotest's variation reached them. `rt.sh` starts it twice |
| `labcheck.py` | Checks that a lab is an exact copy of the commit, file by file. `5-images/image-probe.sh` and `6-other/migrator-probe.sh` call it |

### `1-build/`: the two programs

`build.sh` builds `WebAPI` and `BackgroundJobExecutor` with
`dotnet build -c Release`, and with them the projects they reference.
Before the fixes `6b7a3254d`, after them `e6e924230`.

```
shared/make-lab.sh 6b7a3254d
env OUT=$HOME/Dev/speciale-2026/data/2026-11-09-layer1 shared/rt.sh 1-build none
```

| Script | What it is for |
| --- | --- |
| `build.sh` | The two `dotnet build` commands and a hash of every file under `src/*/bin`. Runs by hand too; see its first lines |
| `artifacts.txt` | Our DLLs, PDBs and `.json` files |
| `pdbdump/` | Prints a PDB's document table and embedded sources as text. Found the Razor paths that `PathMap` misses (W7) |

### `2-publish/`: the two programs and their dependencies

`build.sh` does what the release job did at `4e5237a33`: a locked restore
and two self-contained `linux-x64` publishes, with the locale pinned. The
commands fit the commits from `84d73a2f6` to before `5031c5af`.

```
shared/make-lab.sh 4e5237a33
env OUT=$HOME/Dev/speciale-2026/data/2026-11-09-layer2 shared/rt.sh 2-publish none
```

| Script | What it is for |
| --- | --- |
| `build.sh` | The restore, the two publishes into `release/`, and a hash of every file under it |
| `artifacts.txt` | Our four assemblies and the two Linux launchers |
| `pe-diff-regions.py` | Shows which part of a DLL holds the differing bytes: metadata tables, strings, debug directory. Found the locale's type order (W26) |
| `md-strings.py` | Prints the names at given offsets in a DLL's string heap, to read the types that `pe-diff-regions.py` points at |

### `3-frontend/`: the static export

`build.sh` does what the release's frontend job did at `2cd85fd01`:
`npm ci` from the npm cache without network, and `next build`. The lab
holds the whole commit because the frontend imports code from `mcp/` (W39).
Not yet run with `rt.sh`.

```
shared/make-lab.sh 2cd85fd01
env OUT=$HOME/Dev/speciale-2026/data/DATE-stage3 shared/rt.sh 3-frontend none
```

| Script | What it is for |
| --- | --- |
| `build.sh` | `npm ci` and `npm run build`, and a hash of every file under `out/`. Stages 4 and 6 run it first |
| `artifacts.txt` | The static export |
| `compare-chunks.py` | Compares two webpack chunk logs. The logs come from `module-order-plugin.js` in Speciale2026 (W51) |

### `4-zip/`: the Linux release zips

`build.sh` does what the release's Linux job did at `2cd85fd01`: stage 3,
the locked restore, the two publishes with the export in `wwwroot/`, and
the zips packed with the commit's `scripts/pack-release-zip.sh` and the
commit's time. The hash list covers the zips and the folders in them, so
this stage also measures the publish with the frontend. The commands fit
the commits from `5ec085acb` on. Not yet run with `rt.sh`.

```
shared/make-lab.sh 2cd85fd01
env OUT=$HOME/Dev/speciale-2026/data/DATE-stage4 shared/rt.sh 4-zip none
```

| Script | What it is for |
| --- | --- |
| `build.sh` | Stage 3, the restore, the publishes, the zips, and a hash of every file under `release/` |
| `artifacts.txt` | The two zips |

`../ci/ci-compare.sh` compares CI's zips with a local rebuild, entry by
entry.

### `5-images/`: the OCI images

No `build.sh`. The images are built as two plain builds outside reprotest
and compared by manifest, config and layer.

| Script | What it is for |
| --- | --- |
| `image-probe.sh` | Builds each .NET image twice as the release job does, and compares them with `oci-diff.py` |
| `oci-diff.py` | Compares two OCI images: manifest, config, and each layer's files |
| `oci-file.py` | Extracts one file from an OCI image. Uses `oci-diff.py` |
| `attest-compare.py` | Shows which fields of the provenance and SBOM differ between two images |
| `attest-layers.py` | Checks whether the layers named in the provenance are the image's layers |
| `ghcr-manifests.py` | Compares a pushed image tag with a local image by manifest |
| `faketime-tests.sh` | Checks that the images' build-time tests still pass one year later |

### `6-other/`: the Windows release and the other outputs

`build.sh` is the Windows release as the release's Windows job built it at
`2cd85fd01`, on Linux and unsigned: stage 3, the locked restore, three
`win-x64` publishes, the migrator's copy, and both zips. Not yet run with
`rt.sh`.

```
shared/make-lab.sh 2cd85fd01
env OUT=$HOME/Dev/speciale-2026/data/DATE-stage6 shared/rt.sh 6-other none
```

| Script | What it is for |
| --- | --- |
| `build.sh` | Stage 3, the restore, the three publishes, the migrator's copy, the zips, and a hash of every file under `release/` |
| `artifacts.txt` | The two zips and the migrator |
| `migrator-probe.sh` | Builds the database migrator twice at two paths, for linux-x64 and win-x64, and compares them |
| `signing-probe.sh` | Signs two Windows builds with a test certificate, strips the signatures, and pastes them onto the other build. Its input is the `release/` folders of two stores from `rt.sh 6-other` |
| `signing-paste.sh` | Repeats the paste step of `signing-probe.sh`, with two more negative controls |

### `ci/`: all stages against a CI run

| Script | What it is for |
| --- | --- |
| `ci-local.sh` | Rebuilds each job of the release workflow locally from a tag. The `build.sh` files of stages 3, 4 and 6 take its commands |
| `ci-compare.sh` | Compares every CI output with the rebuild. Exits 1 on any difference. Uses `5-images/oci-diff.py` |
| `ci-compare-tests.sh` | Checks that `ci-compare.sh` reports a difference when there is one |

### Old and new paths

The notes in Speciale2026 use the old paths. The three old reprotest
drivers were removed here on 9 November 2026, when `rt.sh` and the
`build.sh` files took their place. Their originals are still in
Speciale2026's `experiments/`.

| Speciale2026 `experiments/` | Here, `scripts/` |
| --- | --- |
| `phoenix-rt/run.sh`, `phoenix-rt-human/run.sh` | `shared/rt.sh` and each stage's `build.sh`. Mode `1` is `1-build`, `2` is `2-publish`, `R` and `Z` are `4-zip`, `W` is `6-other` |
| `phoenix-fe/run.sh` | `shared/rt.sh 3-frontend` |
| `sample-dotnet.py`, `labcheck.py` | `shared/` |
| `pdbdump/` | `1-build/pdbdump/` |
| `pe-diff-regions.py`, `md-strings.py` | `2-publish/` |
| `phoenix-fe/compare-chunks.py` | `3-frontend/` |
| `phoenix-rt/image-probe.sh`, `oci-*.py`, `attest-*.py`, `ghcr-manifests.py`, `faketime-tests.sh` | `5-images/` |
| `phoenix-rt/migrator-probe.sh`, `signing-*.sh` | `6-other/` |
| `phoenix-rt/ci-*.sh` | `ci/` |
