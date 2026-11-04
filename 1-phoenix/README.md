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

Copied on 4 November 2026 from `experiments/` in Speciale2026, in the same
folder layout, because the scripts find each other by relative path. The
defaults point at Leo's machine (`/home/leos/...`, `/private/tmp/rb1-*`).
Scripts that build a release call Phoenix's own scripts from the measured
commit (`pack-release-zip.sh` and others). Those are not copied here.

**Shared**

| Script | What it is for |
| --- | --- |
| `sample-dotnet.py` | Samples the .NET processes once a second during a run. Shows whether reprotest's variation reached the compiler. The `run.sh` scripts start it |
| `labcheck.py` | Checks that the lab is an exact copy of the commit, file by file |

**Layers 1 to 4, with reprotest**

| Script | Layer | What it is for |
| --- | --- | --- |
| `phoenix-rt/run.sh` | 1, 2, 4, Windows | Runs reprotest once: one layer, one axis. Shuts down the build servers before and after each build, and starts reprotest under `env -i` |
| `phoenix-rt-human/run.sh` | 1, 2, 4, Windows | The same as `phoenix-rt/run.sh` (`e9e84397`), written to be read. Gives reprotest the same command |
| `phoenix-fe/run.sh` | 3 | The same protocol for the frontend's static export |

**Readers, to find which bytes differ**

| Script | Layer | What it is for |
| --- | --- | --- |
| `pdbdump/` | 1, 2 | Prints a PDB's document table and embedded sources as text. Found the Razor paths that `PathMap` misses (W7) |
| `pe-diff-regions.py` | 1, 2 | Shows which part of a DLL holds the differing bytes: metadata tables, strings, debug directory |
| `md-strings.py` | 1, 2 | Prints the names at given offsets in a DLL's string heap |
| `phoenix-fe/compare-chunks.py` | 3 | Compares two webpack chunk logs. The logs come from `module-order-plugin.js` in Speciale2026 (W51) |

**Builds of one part, twice**

| Script | Layer | What it is for |
| --- | --- | --- |
| `phoenix-rt/migrator-probe.sh` | 2 | Builds the database migrator twice at two paths, for linux-x64 and win-x64, and compares them |
| `phoenix-rt/image-probe.sh` | 5 | Builds each .NET image twice as the release job does, and compares them with `oci-diff.py` |
| `phoenix-rt/oci-diff.py` | 5 | Compares two OCI images: manifest, config, and each layer's files |
| `phoenix-rt/oci-file.py` | 5 | Extracts one file from an OCI image |
| `phoenix-rt/attest-compare.py` | 5 | Shows which fields of the provenance and SBOM differ between two images |
| `phoenix-rt/attest-layers.py` | 5 | Checks whether the layers named in the provenance are the image's layers |
| `phoenix-rt/signing-probe.sh` | Windows | Signs two Windows builds with a test certificate, strips the signatures, and pastes them onto the other build |
| `phoenix-rt/signing-paste.sh` | Windows | Repeats the paste step of `signing-probe.sh`, with two more negative controls |

**CI against a rebuild**

| Script | Layer | What it is for |
| --- | --- | --- |
| `phoenix-rt/ci-local.sh` | all | Rebuilds each job of the release workflow locally from a tag |
| `phoenix-rt/ci-compare.sh` | all | Compares every CI output with the rebuild. Exits 1 on any difference |
| `phoenix-rt/ci-compare-tests.sh` | all | Checks that `ci-compare.sh` reports a difference when there is one |
| `phoenix-rt/ghcr-manifests.py` | 5 | Compares a pushed image tag with a local image by manifest |
| `phoenix-rt/faketime-tests.sh` | 5 | Checks that the images' build-time tests still pass one year later |
