# Experiment 1 findings, by cause category

**View:** [by stage](by-stage.md) · by cause category

**93** findings: **47** causes of difference, **21** checks with no difference, **25** about the method. **5** are still open.

An id such as E1-S3-02 is experiment 1, stage 3, finding 2; E1-M-05 is a finding about the method. The old id in brackets is the row of `notes/findings-table.md` in Speciale2026. Stage 5 groups the release's other outputs, which the findings table files under stages 2 and 4. Stage 6 holds the images, which the findings table numbers 5. Hashes made before the move to SDK 10 (12 October 2026) do not compare with later ones.

| Fix type | Meaning |
| --- | --- |
| fix build | WS.PEMS's build was changed |
| fix rebuild | The rebuild or the measurement must do something |
| upstream | Only the tool's maintainers can fix it; we pin or work around it |
| none needed | Measured, and it did not differ or does not ship |
| open | Not resolved |
| rejected | The result was withdrawn |

**Categories:** [Build path](#build-path) (12) · [Locale](#locale) (3) · [Clock time](#clock-time) (7) · [Chance and timing](#chance-and-timing) (5) · [Toolchain identity](#toolchain-identity) (8) · [Inputs and pinning](#inputs-and-pinning) (9) · [File and archive metadata](#file-and-archive-metadata) (3) · [Build and release configuration](#build-and-release-configuration) (9) · [Measured stable](#measured-stable) (12) · [Method](#method) (25)

<a name="build-path"></a>

## Build path

The folder the build runs in gets into the output: in PDBs, in generated code, in type names and in plain-text files.

Fix types: fix build 8, none needed 2, open 3

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-06"></a>**E1-S1-06** (E6) | 1 | Another build path changed the DLL and the PDB: both hold absolute paths. | csc | fix build | 🟢 closed |
| <a name="e1-s1-09"></a>**E1-S1-09** (W3) | 1 | All four PDBs held absolute source paths. | csc | fix build | 🟢 closed |
| <a name="e1-s1-10"></a>**E1-S1-10** (W4) | 1 | The DLL holds the PDB's path. A path 2 characters longer moves every address after it. | csc | fix build | 🟢 closed |
| <a name="e1-s1-11"></a>**E1-S1-11** (W5) | 1 | Four generated regex types are named by a hash of the source file's path. | csc, regex generator | fix build | 🟢 closed |
| <a name="e1-s1-12"></a>**E1-S1-12** (W6) | 1 | `ContinuousIntegrationBuild` maps the source root only when Source Link finds `.git`. In an export it mapped only the NuGet cache. Fixed with an explicit `PathMap`. | SDK Source Link targets | fix build | 🟢 closed |
| <a name="e1-s1-13"></a>**E1-S1-13** (W7) | 1 | The Razor generator writes the absolute `.cshtml` path into generated C#, and `PathMap` does not reach that text. Fixed in WS.PEMS by deleting two unused pages; open for other projects. | Razor source generator | fix build, open | 🟢 closed |
| <a name="e1-s1-14"></a>**E1-S1-14** (W8) | 1 | `spa.proxy.json` holds the path to `ClientApp/`. Development only, not shipped. | SpaProxy targets | open | 🔴 open |
| <a name="e1-s1-15"></a>**E1-S1-15** (W9) | 1 | `staticwebassets.runtime.json` holds paths to `obj/` and the NuGet cache. Development only, not shipped. | SDK | open | 🔴 open |
| <a name="e1-s2-02"></a>**E1-S2-02** (W17) | 2 | The two json files of E1-S1-14 and E1-S1-15 do not ship. The shipped endpoints file has no paths. | SpaProxy, SDK | none needed | 🟢 closed |
| <a name="e1-s2-10"></a>**E1-S2-10** (W25) | 2 | Another build path on the final tree: no difference. | – | none needed | 🟢 closed |
| <a name="e1-s1-21"></a>**E1-S1-21** (W49) | 1 | The explicit `PathMap` also rewrote `[CallerFilePath]`, which broke the tests' search for the solution folder. | csc, Testcontainers | fix build | 🟢 closed |
| <a name="e1-s5-01"></a>**E1-S5-01** (W52) | 5 | The `ef bundle` migrator is built in a random `/tmp` folder: 93 of 827,679,078 bytes differ. Now a project in the repository, where `PathMap` applies. | dotnet ef | fix build | 🟢 closed |

<a name="locale"></a>

## Locale

The language setting decides a sort order, so the same build under another locale writes the same items in another order.

Fix types: fix build 3, upstream 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s2-11"></a>**E1-S2-11** (W26) | 2 | Under Estonian the compiler orders the types it generates for collection expressions differently: 10 of 1237 files. A Roslyn defect, gone on SDK 10. | csc | fix build, upstream | 🟢 closed |
| <a name="e1-s2-16"></a>**E1-S2-16** (W33) | 2 | With eleven axes varied at once, the release equals the Estonian-only build: no other axis changes a byte. `LC_ALL=C.UTF-8` fixes it. | csc (E1-S2-11) | fix build | 🟢 closed |
| <a name="e1-s5-07"></a>**E1-S5-07** (W63) | 5 | `SHA256SUMS` lists the files in the locale's sort order. Fixed with `LC_ALL=C`. | bash, glibc | fix build | 🟢 closed |

<a name="clock-time"></a>

## Clock time

The time of the build gets into the output: file dates, image times, signature timestamps, attestations.

Fix types: fix build 3, fix rebuild 2, upstream 1, none needed 2

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-05"></a>**E1-S1-05** (E5) | 1 | The PE `TimeDateStamp` is part of a content hash, not a time. It changes only when the content changes. | csc | none needed | 🟢 closed |
| <a name="e1-s2-14"></a>**E1-S2-14** (W31) | 2 | 311 `Last-Modified` dates come from a NuGet package's zip, not from the build clock. Stable. | SDK, NuGet | none needed | 🟢 closed |
| <a name="e1-s2-18"></a>**E1-S2-18** (W50) | 2 | SDK 10 dates the compressed copies of static files with the time it wrote them. Fixed by turning compression off. | SDK static web assets | fix build, upstream | 🟢 closed |
| <a name="e1-s6-01"></a>**E1-S6-01** (W56) | 6 | The WebAPI and job worker images differ in times only. Fixed with `SOURCE_DATE_EPOCH` and BuildKit's `rewrite-timestamp`. | BuildKit | fix build | 🟢 closed |
| <a name="e1-s5-05"></a>**E1-S5-05** (W59) | 5 | Signing gives each of 177 files a timestamped signature, so two signed builds always differ. Check a rebuild by pasting the release's signatures onto it. | jsign, timestamp server | fix rebuild | 🟢 closed |
| <a name="e1-s6-03"></a>**E1-S6-03** (W62) | 6 | The migrations image, from the manual image script, had the same time difference as E1-S6-01. Fixed the same way. | BuildKit | fix build | 🟢 closed |
| <a name="e1-s6-04"></a>**E1-S6-04** (W65) | 6 | Image tags point at attestations that hold the build's clock and a random id, so tags differ in every build. Compare the image manifest instead. | BuildKit, syft | fix rebuild | 🟢 closed |

<a name="chance-and-timing"></a>

## Chance and timing

Two builds in the same environment still differ: a random id, or an order that follows which file finished first.

Fix types: fix build 4, upstream 3, open 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s3-01"></a>**E1-S3-01** (W37) | 3 | Next.js draws a random build ID in every build and writes it into paths and pages: 110 of 998 files. Set to the release version. | Next.js | fix build | 🟢 closed |
| <a name="e1-s3-06"></a>**E1-S3-06** (W43) | 3 | Shared CSS files took their order from build timing: 4 of 998 files in 1 of 4 builds. All third-party CSS now imported in one place. | Next.js CSS chunking | fix build, upstream | 🟢 closed |
| <a name="e1-s3-07"></a>**E1-S3-07** (W44) | 3 | Between two commits, the minifier gave other short names in the runtime chunk. Never within one commit, so it does not break reproducibility. | SWC minifier | open | 🔴 open |
| <a name="e1-s3-09"></a>**E1-S3-09** (W47) | 3 | Webpack ordered the pages by build timing: two outputs over 26 builds, 109 of 990 files. A plugin sorts them by name. | Next.js, webpack | fix build, upstream | 🟢 closed |
| <a name="e1-s3-10"></a>**E1-S3-10** (W51) | 3 | About 1 in 50 builds, two identical chunks swapped ids: webpack's module order followed timing. The plugin also sorts modules. | webpack | fix build, upstream | 🟢 closed |

<a name="toolchain-identity"></a>

## Toolchain identity

Which binary of a tool did the work. The same version number can hide another compiler, runtime or npm.

Fix types: fix build 3, fix rebuild 1, upstream 1, none needed 2, open 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-02"></a>**E1-S1-02** (E2) | 1 | Two machines gave different DLLs from the same source. Both compilers were called 9.0.120, but one was Arch's build of csc and one was Microsoft's. | SDK vendor | fix rebuild | 🟢 closed |
| <a name="e1-s1-03"></a>**E1-S1-03** (E3) | 1 | The two compilers have the same Roslyn code and emit the same IL, yet 70 of 4096 bytes differ: the PDB records the compiler's commit, and the DLL a hash of the PDB. | csc | upstream | 🟢 closed |
| <a name="e1-s1-04"></a>**E1-S1-04** (E4) | 1 | Microsoft's csc is a different binary on macOS and Linux, but both gave the same bytes. The output follows the compiler's Roslyn commit, not its file hash. | Microsoft | none needed | 🟢 closed |
| <a name="e1-s3-04"></a>**E1-S3-04** (W40) | 3 | The release asked for Node `20.x`, a major version only. Now pinned in `.nvmrc` and read by every workflow. | setup-node, Node | fix build | 🟢 closed |
| <a name="e1-s3-08"></a>**E1-S3-08** (W46) | 3 | The release's npm drops the `libc` field from the lock file. It changes which packages install, not the export of one commit. | npm | open | 🔴 open |
| <a name="e1-s2-19"></a>**E1-S2-19** (W58) | 2 | GitHub's runner and our machine: our assemblies differ by the runtime patch the compiler ran on, 10.0.13 against 10.0.12. Fixed by installing the `global.json` SDK alone. | setup-dotnet, .NET host | fix build | 🟢 closed |
| <a name="e1-s5-10"></a>**E1-S5-10** (W69) | 5 | `dotnet tool restore` can run a tool from another job's folder on a shared runner. The migration job now has its own CLI home. | .NET CLI | fix build | 🟢 closed |
| <a name="e1-s2-20"></a>**E1-S2-20** (W71) | 2, 3, 4 | macOS on arm64 against GitHub's Linux x86-64 runner: nothing differs, frontend and zips included. | Roslyn, SWC, zip | none needed | 🟢 closed |

<a name="inputs-and-pinning"></a>

## Inputs and pinning

What goes into the build: dependencies pinned by version instead of content, files from outside the project, side products of a build step.

Fix types: fix build 6, fix rebuild 1, upstream 1, none needed 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-19"></a>**E1-S1-19** (W15) | 1 | A cold restore on another machine resolved the same versions and hashes for all packages. | NuGet | none needed | 🟢 closed |
| <a name="e1-s2-06"></a>**E1-S2-06** (W21) | 2 | 323 of WebAPI's 746 files are copies from Microsoft's runtime packs, which no lock file records. The branch checks them by hash. | Microsoft | upstream | 🟢 closed |
| <a name="e1-s2-07"></a>**E1-S2-07** (W22) | 2 | NuGet lock files pin every package by content hash. A locked restore gives the same release. | NuGet | fix build | 🟢 closed |
| <a name="e1-s3-03"></a>**E1-S3-03** (W39) | 3 | The frontend imports 7 files from outside `ClientApp`. Build it from an export of the whole commit. | webpack | fix rebuild | 🟢 closed |
| <a name="e1-s3-05"></a>**E1-S3-05** (W41) | 3 | 391 of 1509 lock entries had no content hash, so npm trusted the registry for them. Filled in. | npm | fix build | 🟢 closed |
| <a name="e1-s6-02"></a>**E1-S6-02** (W60) | 6 | The MCP images kept files that build steps write as a side effect: font caches, Node's compile cache, test durations. Removed in each step. | fontconfig, npm, vitest | fix build | 🟢 closed |
| <a name="e1-s5-08"></a>**E1-S5-08** (W64) | 5 | On a self-hosted runner the Windows job took a frontend export that another job had left on the machine. It now always downloads the release's own. | release workflow | fix build | 🟢 closed |
| <a name="e1-s6-05"></a>**E1-S6-05** (W67) | 6 | The MCP images install Debian packages from the live archive. Now installed from a dated snapshot. | apt, Debian | fix build | 🟢 closed |
| <a name="e1-s6-06"></a>**E1-S6-06** (W68) | 6 | canvas downloads a prebuilt binary from GitHub without a checksum. Now added by its SHA-256. | prebuild-install | fix build | 🟢 closed |

<a name="file-and-archive-metadata"></a>

## File and archive metadata

The contents are equal, but the metadata around them is not: file modes, zip entry fields, the names in the checksum file.

Fix types: fix build 2, open 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s2-13"></a>**E1-S2-13** (W30) | 2 | File modes in the release follow the umask: 142 files change under umask 0002. Left to stage 4, whose zip packing sets the modes. | csc, MSBuild, SDK, NuGet | open | 🔴 open |
| <a name="e1-s4-01"></a>**E1-S4-01** (W48) | 4 | The zips differ in every build though every entry's bytes are equal: times, order, modes, owner. Fixed by normalised packing. | Info-ZIP zip | fix build | 🟢 closed |
| <a name="e1-s5-09"></a>**E1-S5-09** (W66) | 5 | `SHA256SUMS` named three files by a folder that the GitHub Release does not have, so a download could not be checked. | release workflow | fix build | 🟢 closed |

<a name="build-and-release-configuration"></a>

## Build and release configuration

Errors in how the project or workflow was set up. Some made wrong output, some came from our own fixes.

Fix types: fix build 7, none needed 2

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s2-03"></a>**E1-S2-03** (W18) | 2 | An empty `package-lock.json`, committed by mistake, shipped in the release. | Web SDK content glob | fix build | 🟢 closed |
| <a name="e1-s2-04"></a>**E1-S2-04** (W19) | 2 | The release's version flags reach every assembly. A verifier must know the version string. | SDK | none needed | 🟢 closed |
| <a name="e1-s2-05"></a>**E1-S2-05** (W20) | 2 | A publish with `-r linux-x64` puts the platform in the PDB path and the PE header. Compare a DLL only with the same publish command. | SDK | none needed | 🟢 closed |
| <a name="e1-s2-08"></a>**E1-S2-08** (W23) | 2 | `RuntimeIdentifiers` on every project made the libraries platform-specific and shipped Windows DLLs in the Linux release. | SDK | fix build | 🟢 closed |
| <a name="e1-s2-09"></a>**E1-S2-09** (W24) | 2 | A restore without the version flags made `deps.json` list our libraries as 1.0.0. | NuGet, SDK | fix build | 🟢 closed |
| <a name="e1-s2-17"></a>**E1-S2-17** (W45) | 2 | The release's builds got the version by different routes. Now one `APP_VERSION` for every build. | MSBuild, workflow | fix build | 🟢 closed |
| <a name="e1-s5-02"></a>**E1-S5-02** (W53) | 5 | On .NET 10 the migration jobs failed before building: `dotnet ef` needs a restore first. | dotnet-ef 10 | fix build | 🟢 closed |
| <a name="e1-s5-03"></a>**E1-S5-03** (W54) | 5 | On macOS the migrator's locked restore failed: the SDK added the Mac's platform, which the lock does not hold. | SDK | fix build | 🟢 closed |
| <a name="e1-s1-22"></a>**E1-S1-22** (W70) | 1 | The branch's SDK installer refused every archive on older Python versions. Fixed in the installer. | our installer | fix build | 🟢 closed |

<a name="measured-stable"></a>

## Measured stable

Baselines and axes that we varied and that changed no byte. They show where no fix is needed.

Fix types: none needed 12

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-01"></a>**E1-S1-01** (E1) | 1 | Two clean builds of the empty class at the same path, machine and SDK: identical DLL and PDB. | csc | none needed | 🟢 closed |
| <a name="e1-s1-07"></a>**E1-S1-07** (E7) | 1 | Time, locale, umask, exec path and file order changed no byte of the empty class. | – | none needed | 🟢 closed |
| <a name="e1-s1-08"></a>**E1-S1-08** (W1) | 1 | Two clean builds of the whole solution at the same path: 0 of 1610 files differ. | csc, MSBuild | none needed | 🟢 closed |
| <a name="e1-s1-17"></a>**E1-S1-17** (W12) | 1 | MSBuild sorts the source files before the compiler sees them, so the directory's file order does not matter. | MSBuild | none needed | 🟢 closed |
| <a name="e1-s1-18"></a>**E1-S1-18** (W13) | 1 | Building with and without the compiler server gave the same 639 files. | MSBuild, csc | none needed | 🟢 closed |
| <a name="e1-s2-01"></a>**E1-S2-01** (W16) | 2 | Two clean publishes with the release's own commands: 1238 identical files. | SDK, csc | none needed | 🟢 closed |
| <a name="e1-s2-12"></a>**E1-S2-12** (W29) | 2 | Clock +398 days, umask (contents) and exec path, now with the variation inside the compiler: no difference. | – | none needed | 🟢 closed |
| <a name="e1-s2-15"></a>**E1-S2-15** (W32) | 2 | Time zone, environment, home, CPUs and another user: no difference. | – | none needed | 🟢 closed |
| <a name="e1-s1-20"></a>**E1-S1-20** (W34) | 1 | Stage 1 with the compiler inside the variation, nine axes: no difference. | – | none needed | 🟢 closed |
| <a name="e1-s3-02"></a>**E1-S3-02** (W38) | 3 | Two frontend builds at the same path, with the build ID fixed: identical. | Next.js, webpack, SWC | none needed | 🟢 closed |
| <a name="e1-s5-04"></a>**E1-S5-04** (W55) | 5 | The Windows release, built on Linux as its job builds it: 2132 files identical under no variation, all axes and Estonian. | – | none needed | 🟢 closed |
| <a name="e1-s5-06"></a>**E1-S5-06** (W61) | 5 | The SQL script from two exports, at two paths and under another locale and time zone: identical. | EF Core | none needed | 🟢 closed |

---

<a name="method"></a>

## Method

Findings about how to measure, not about WS.PEMS: what reprotest really varies, and what can make a green result wrong.

Fix types: fix rebuild 12, none needed 9, open 3, rejected 1

| Id | Stage | What we found | Bytes written by | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-m-01"></a>**E1-M-01** (E8) | M | A command-line `PathMap` must use the shell's `$PWD`. `$(MSBuildProjectDirectory)` is ignored there without a warning. | MSBuild | fix rebuild | 🟢 closed |
| <a name="e1-m-02"></a>**E1-M-02** (E9) | M | Sorting one file list under two locales gave two different hash lists. | the OS | fix rebuild | 🟢 closed |
| <a name="e1-m-03"></a>**E1-M-03** (E10) | M | Deleting only `bin/` does not rebuild: MSBuild copies the old files from `obj/` again. | MSBuild | fix rebuild | 🟢 closed |
| <a name="e1-m-04"></a>**E1-M-04** (W2) | M | Deleting `obj/` between builds also deletes the restore's output, so both builds fail. | NuGet | fix rebuild | 🟢 closed |
| <a name="e1-s1-16"></a>**E1-S1-16** (W10) | 1 | A green result for time, locale, umask and exec path on stage 1. Withdrawn: the compiler server kept the control build's environment (E1-M-07). | – | rejected | 🔴 open |
| <a name="e1-m-05"></a>**E1-M-05** (W11) | M | Our clean step missed the test project, which then built in only one of the two builds. | our script | fix rebuild | 🟢 closed |
| <a name="e1-m-06"></a>**E1-M-06** (W14) | M | The shared droplet (1 CPU, 1 GB) could not compile WS.PEMS in 3 hours. A verifier needs several GB of RAM. | – | open | 🔴 open |
| <a name="e1-m-07"></a>**E1-M-07** (W27) | M | reprotest's second build reuses the compiler server that the first build started, so the varied environment never reaches the compiler. Fix: shut the build servers down before each build. | .NET build servers | fix rebuild | 🟢 closed |
| <a name="e1-m-08"></a>**E1-M-08** (W28) | M | reprotest also fixes settings it does not vary: one CPU, `TZ=GMT+12`, `LANG=C.UTF-8`, `HOME` in the build folder. | reprotest | none needed | 🟢 closed |
| <a name="e1-m-09"></a>**E1-M-09** (W35) | M | With MSBuild's node reuse off, no compiler server or worker node survived any of 32 runs. | MSBuild | fix rebuild | 🟢 closed |
| <a name="e1-m-10"></a>**E1-M-10** (W36) | M | The working directory does not show which build a process belongs to; `HOME` does. | – | fix rebuild | 🟢 closed |
| <a name="e1-m-11"></a>**E1-M-11** (W42) | M | Stage 2 was first measured without the frontend export that CI copies into `wwwroot/`. | MSBuild | fix rebuild | 🟢 closed |
| <a name="e1-m-12"></a>**E1-M-12** (W57) | M | BuildKit reuses a cached `WORKDIR` step despite `--no-cache`, so one builder can hide a time difference. | BuildKit | none needed | 🟢 closed |
| <a name="e1-m-13"></a>**E1-M-13** (R1) | M | The `aslr` axis alone changes nothing: both builds run with ASLR on. Only `kernel` turns it off. | reprotest | open | 🔴 open |
| <a name="e1-m-14"></a>**E1-M-14** (R2) | M | The `kernel` axis varies two things: the reported kernel version and ASLR. | reprotest | none needed | 🟢 closed |
| <a name="e1-m-15"></a>**E1-M-15** (R3) | M | Axes change more than their names say: `build_path` moves `HOME`, and `user_group` replaces `PATH`. | reprotest | none needed | 🟢 closed |
| <a name="e1-m-16"></a>**E1-M-16** (R4) | M | The builds inherit the whole environment of the shell that starts reprotest, 105 variables in our case. Start it under `env -i`. | reprotest | fix rebuild | 🟢 closed |
| <a name="e1-m-17"></a>**E1-M-17** (R5) | M | Under reprotest's fixed setting, the caller's other locale variables still apply. Only `LC_ALL`, `LC_MESSAGES` and `LANG` decide ICU's locale. | reprotest, ICU | none needed | 🟢 closed |
| <a name="e1-m-18"></a>**E1-M-18** (R6) | M | On a green run reprotest replaces the second build's output with a link to the first. Compare hashes across runs, not only verdicts. | reprotest | none needed | 🟢 closed |
| <a name="e1-m-19"></a>**E1-M-19** (R7) | M | The `time` axis silently skips its shift when the newest source file is over 398 days old. | reprotest | fix rebuild | 🟢 closed |
| <a name="e1-m-20"></a>**E1-M-20** (R8) | M | reprotest's log names each build's varied axes and values, and its exit code tells pass, differ and fail apart. | reprotest | none needed | 🟢 closed |
| <a name="e1-m-21"></a>**E1-M-21** (T1) | M | npm, pip, gem, Maven and Go leave no process alive between reprotest's builds. .NET's compiler server does (E1-M-07). | – | none needed | 🟢 closed |
| <a name="e1-m-22"></a>**E1-M-22** (T2) | M | The `time` axis cannot move the clock of a static binary: Go's compiler reads the real time. | libfaketime | open | 🔴 open |
| <a name="e1-m-23"></a>**E1-M-23** (T3) | M | Under `time`, pip's build fails the TLS check against PyPI. | pip | fix rebuild | 🔴 open |
| <a name="e1-m-24"></a>**E1-M-24** (T4) | M | reprotest's `HOME` does not reach Maven, which still uses the real `~/.m2`. | Maven | none needed | 🟢 closed |
