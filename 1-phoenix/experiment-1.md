# Experiment 1: Reproducible builds of WS.Phoenix (short version)

## Introduction

A build is reproducible when the same source always gives the same bytes. Then anyone can check that a binary was made from the source it names. This experiment asks whether the WS.Phoenix release can be built so that two builds give bit-identical output, also when the build environment changes.

WS.Phoenix is Weel-Sandvig's product: four .NET assemblies, about 300 NuGet dependencies, a Next.js frontend, release zips and container images. Before Phoenix, we built one empty C# class to test the set-up and the method: build twice, hash every file, compare, find the cause, fix, and build again.

### The stage plan

The release is built in six stages. Each stage adds its own possible sources of difference, so each is measured on its own before the next.

| Stage | What is built | What is compared |
| --- | --- | --- |
| 1 Build | `dotnet build -c Release` | Our DLLs and PDBs, `deps.json`, `runtimeconfig.json` |
| 2 Publish | `dotnet publish`, the release's own commands | The publish folder: our assemblies, dependencies, the .NET runtime |
| 3 Frontend | `npm ci` + `next build` | The static export: HTML, JavaScript, CSS |
| 4 Zip | The release zips | The archive's bytes |
| 5 Container | The OCI images | Image manifest and layers |
| 6 Other release outputs | Database migrator, SQL script, checksum file, Windows release, signing | Each file the release ships |

Stages 1-3 are loose files. Stages 4 and 5 are archives, which also store file times, modes and order.

### Problem statement

Which properties of the build environment change the bytes of each stage, and can each cause be removed?

## Methods

### Set-up

All builds ran on one Arch Linux laptop, from the branch `thesis/reproducible-builds`. These conditions make sure that the environment is what we say it is, and that the only difference between two builds is the one we chose:

- The source is an exact export of one commit (`git archive`), outside git, checked file by file before each batch.
- The SDK is pinned by `global.json`: Microsoft's 9.0.120, from 12 October 2026 10.0.401. The compiler's SHA-256 is recorded with each run.
- Each run starts clean (no `bin/`, `obj/`) and only one build runs at a time.
- .NET's build servers are stopped before and after each build, so the second build cannot reuse a process that the first build started.
- reprotest starts from an empty environment with five listed variables.

### Instrument

**reprotest** 0.7.32 builds the project twice, changes one property of the environment between the two builds, and compares the outputs. The axes used: build path, time, locale, umask, `PATH`, time zone, environment variables, home folder, kernel, CPU count, user, and all at once. **diffoscope** 329 shows which bytes differ. The verdict is a SHA-256 hash of every output file. Where diffoscope's report was not enough, a reader for that file type was used (PDB, zip header, OCI image).

Every stage follows the same procedure:

1. Two clean builds at the same path.
2. reprotest, one axis per run, then all axes at once.
3. Each difference traced to its file and field, fixed on the branch, and the run repeated.

The sections below give only what is particular to each stage.

### Stage 1: build

The first same-path test built the whole solution and hashed all 1610 files under `bin/Release`, tests included. The reprotest runs build only the two programs, `WebAPI` and `BackgroundJobExecutor`, with the projects they reference. They hash our DLLs, PDBs and `.json` files.

### Stage 2: publish

The release job's own commands: a locked restore and two self-contained `linux-x64` publishes, with the release's version flags. NuGet lock files pin every package by content hash. Measured first without, then with the frontend export in `wwwroot/`, as CI ships it.

### Stage 3: frontend

Built from an export of the whole commit, because the frontend imports code from outside its own folder. Node pinned to one version; `npm ci --offline` from a filled cache. Where an order varied between builds, webpack logged its order and was delayed on purpose, to confirm the cause before the fix.

### Stage 4: zip

The zips packed as CI packs them (`zip -r`), and with a normalised packing: fixed times, sorted names, fixed modes, no extra fields. Compared entry by entry: name, content, time, mode, owner, order. Only with no variation and with all axes at once.

### Stage 5: container

Built as the release job builds them, with BuildKit and no cache, as two plain builds outside reprotest. Compared by manifest, config, and layer by layer. Repeated with the commit's time as `SOURCE_DATE_EPOCH` and BuildKit's `rewrite-timestamp`.

### Stage 6: other release outputs

The release job's own commands for each output. The database migrator built from two exports at two paths. The SQL script from two exports, the second under another locale and time zone. The Windows release built on Linux as its CI job builds it, under no variation, all axes and the Estonian locale. The Windows binaries signed twice with a test certificate, and the signatures then copied onto an unsigned rebuild, since a signature carries its own timestamp.

### Unit of measurement

The unit is the SHA-256 hash of each output file. A stage is green when every hash is the same in both builds, and red otherwise. A difference counts even when it looks harmless. Counts are given as differing files out of all files.

## Results

Every stage that ships became bit-identical on every axis we ran. Two development files in stage 1 still differ with the build path; they are not part of the release.

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

## Discussion and conclusion

Each stage had its own causes of difference, and each was removed by a change to the build. Stages 1 and 2 were deterministic from the start and differed only when the environment changed: the build path and the locale. Stages 3, 4 and 5 differed even between two builds in the same environment: a random build ID, orders that followed build timing, and timestamps in archives and images.

Most causes belong to the tools, not to Phoenix: the compiler's culture-dependent order, the SDK 10 timestamps, and webpack's timing-dependent order. Any project that uses the same tools inherits them.

Signed files can never be rebuilt byte for byte, because each signature carries its own timestamp. A rebuild is checked by copying the release's signatures onto it; then every byte is equal.

### Limitations

- All builds ran on one machine. Builds on different machines are not part of this experiment.
- Not every axis was run: file order needs `disorderfs`, which this machine does not have. ASLR alone cannot be varied with reprotest. Stages 4 and 5 were tested with fewer axes than stages 1-3.
- Few repetitions: many results rest on two builds. Rare races were found only by repetition, about once in 50 builds.
- Hashes before and after the SDK change (12 October 2026) do not compare.
- The Windows release was built on Linux, as its CI job builds it, not on Windows.

### Future work

- Builds on different machines and operating systems.
- The axes not run here, on a machine with `disorderfs`.
- Reports to the tools' maintainers: the compiler's locale order, the SDK 10 timestamps, and webpack's orders in Next.js.
