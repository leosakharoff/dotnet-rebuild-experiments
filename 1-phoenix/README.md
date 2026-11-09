# Rebuilding Phoenix

We test what is needed to rebuild a Phoenix release byte for byte across
machines. The method and results will be added here.

- [experiment-1.md](experiment-1.md): the short version of method and results,
  layer by layer.
- [figures/](figures/): `build-publish-pack` (the steps of `dotnet build`,
  `publish` and `pack`), `sdk-processes` (how one build chooses its
  processes' runtimes) `npm-build` (the frontend's `npm ci` and
  `npm run build`) and `npm-findings` (only what the frontend findings need). Each as `.drawio` and exported `.drawio.png`;
  [figures/README.md](figures/README.md) explains every file and step.
- [findings/](findings/): every finding in two views,
  [by layer](findings/by-layer.md) (before and after the fixes) and
  [by cause family](findings/by-family.md).
- [scripts/](scripts/): the scripts needed to redo the experiment, listed
  below.

## Scripts

Copied on 4 November 2026 from `experiments/` in Speciale2026. On 9 November
2026 we sorted them into one folder for each layer, in the order of
[experiment-1.md](experiment-1.md). The scripts find each other by relative
path, and those paths follow the new folders. The defaults point at Leo's
machine (`/home/leos/...`, `/private/tmp/rb1-*`). Scripts that build a release
call Phoenix's own scripts from the measured commit (`pack-release-zip.sh` and
others). Those are not copied here.

```
scripts/
  shared/       the reprotest driver and the checks that several layers use
  1-build/      the two programs: WebAPI and BackgroundJobExecutor
  2-publish/    the two programs and their dependencies, self-contained
  3-frontend/   npm ci and next build: the static export
  4-zip/        the release zips
  5-images/     the OCI images
  6-other/      the migrator, the signing and the Windows release
  ci/           a CI release run against a local rebuild, all layers
```

### `shared/`

| Script | Layers | What it is for |
| --- | --- | --- |
| `run.sh` | 1, 2, 4, 6 | Runs reprotest once: one layer, one axis. Shuts down the build servers before and after each build, and starts reprotest under `env -i`. Its modes: `1` build, `2` publish, `R` the release with the frontend, `Z` the zips, `W` the Windows release |
| `run-readable.sh` | 1, 2, 4, 6 | The same as `run.sh` (`e9e84397`), written to be read. Gives reprotest the same command |
| `sample-dotnet.py` | 1 to 4, 6 | Samples the .NET processes once a second during a run. Shows whether reprotest's variation reached the compiler. `run.sh`, `run-readable.sh` and `3-frontend/run.sh` start it |
| `labcheck.py` | 5, 6 | Checks that the lab is an exact copy of the commit, file by file. `5-images/image-probe.sh` and `6-other/migrator-probe.sh` call it |

### `1-build/`: the two programs

`shared/run.sh 1 AXIS` builds `WebAPI` and `BackgroundJobExecutor` with
`dotnet build -c Release`, and with them the projects they reference.

| Script | What it is for |
| --- | --- |
| `pdbdump/` | Prints a PDB's document table and embedded sources as text. Found the Razor paths that `PathMap` misses (W7) |

### `2-publish/`: the two programs and their dependencies

`shared/run.sh 2 AXIS` does what the release job does: a locked restore and
two self-contained `linux-x64` publishes. `shared/run.sh R AXIS` does the same
with the frontend's export in `wwwroot/`.

| Script | What it is for |
| --- | --- |
| `pe-diff-regions.py` | Shows which part of a DLL holds the differing bytes: metadata tables, strings, debug directory. Found the locale's type order (W26) |
| `md-strings.py` | Prints the names at given offsets in a DLL's string heap, to read the types that `pe-diff-regions.py` points at |

### `3-frontend/`

| Script | What it is for |
| --- | --- |
| `run.sh` | Runs reprotest on the frontend's static export, with the same protocol as `shared/run.sh`. Builds only the frontend; the lab holds the whole commit because the frontend imports code from `mcp/` (W39) |
| `compare-chunks.py` | Compares two webpack chunk logs. The logs come from `module-order-plugin.js` in Speciale2026 (W51) |

### `4-zip/`

No script of its own. See [4-zip/README.md](scripts/4-zip/README.md).

### `5-images/`

| Script | What it is for |
| --- | --- |
| `image-probe.sh` | Builds each .NET image twice as the release job does, and compares them with `oci-diff.py` |
| `oci-diff.py` | Compares two OCI images: manifest, config, and each layer's files |
| `oci-file.py` | Extracts one file from an OCI image. Uses `oci-diff.py` |
| `attest-compare.py` | Shows which fields of the provenance and SBOM differ between two images |
| `attest-layers.py` | Checks whether the layers named in the provenance are the image's layers |
| `ghcr-manifests.py` | Compares a pushed image tag with a local image by manifest |
| `faketime-tests.sh` | Checks that the images' build-time tests still pass one year later |

### `6-other/`: other release outputs

| Script | What it is for |
| --- | --- |
| `migrator-probe.sh` | Builds the database migrator twice at two paths, for linux-x64 and win-x64, and compares them |
| `signing-probe.sh` | Signs two Windows builds with a test certificate, strips the signatures, and pastes them onto the other build. Its input is two stores of `shared/run.sh W` |
| `signing-paste.sh` | Repeats the paste step of `signing-probe.sh`, with two more negative controls |

The Windows release itself is `shared/run.sh W AXIS`.

### `ci/`: all layers against a CI run

| Script | What it is for |
| --- | --- |
| `ci-local.sh` | Rebuilds each job of the release workflow locally from a tag |
| `ci-compare.sh` | Compares every CI output with the rebuild. Exits 1 on any difference. Uses `5-images/oci-diff.py` |
| `ci-compare-tests.sh` | Checks that `ci-compare.sh` reports a difference when there is one |

### Old and new paths

The notes in Speciale2026 use the old paths.

| Speciale2026 `experiments/` | Here, `scripts/` |
| --- | --- |
| `phoenix-rt/run.sh` | `shared/run.sh` |
| `phoenix-rt-human/run.sh` | `shared/run-readable.sh` |
| `sample-dotnet.py`, `labcheck.py` | `shared/` |
| `pdbdump/` | `1-build/pdbdump/` |
| `pe-diff-regions.py`, `md-strings.py` | `2-publish/` |
| `phoenix-fe/run.sh`, `phoenix-fe/compare-chunks.py` | `3-frontend/` |
| `phoenix-rt/image-probe.sh`, `oci-*.py`, `attest-*.py`, `ghcr-manifests.py`, `faketime-tests.sh` | `5-images/` |
| `phoenix-rt/migrator-probe.sh`, `signing-*.sh` | `6-other/` |
| `phoenix-rt/ci-*.sh` | `ci/` |
