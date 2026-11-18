# Experiment 1: findings

**93** findings: **39** causes of a difference, **9** setup faults we corrected, **20** variations that changed no byte, **25** about the method. **9** are still open.

[By stage](stages.md) gives what each stage looked like before and after the fixes. This page lists every finding once.

**Id.** `E1-S3-02` is stage 3, finding 2; `E1-M-05` is about the method. The old id in brackets is the row of `notes/findings-table.md` in Speciale2026.

**Code.** The cause, from the [codebook](../../coding/codebook.md). After a slash: what a rebuilder lacked, for findings that came from comparing with CI or another machine. CONFIG, STABLE and METHOD are findings that are not causes.

**Fix in.** Where the fix belongs: *our build* (WS.PEMS's build was changed), *the rebuild* (whoever rebuilds or compares must do something), *upstream* (only the tool's maintainers can fix it; we pin or work around), *not needed* (measured, and it did not differ or does not ship). A dash: not yet decided.

**Causes by code:** PATH 9 · INPUT 7 · TOOL 6 · TIME 5 · RANDOM 4 · LOCALE 3 · META 2 · CI 2 · ? 1

## Stage 1: Build

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s1-01"></a>**E1-S1-01** (E1) | Two clean builds of the empty class at the same path, machine and SDK: identical DLL and PDB. | STABLE | csc | not needed | closed |
| <a name="e1-s1-02"></a>**E1-S1-02** (E2) | Two machines gave different DLLs from the same source. Both compilers were called 9.0.120, but one was Arch's build of csc and one was Microsoft's. | TOOL / ENV | SDK vendor | the rebuild | closed |
| <a name="e1-s1-03"></a>**E1-S1-03** (E3) | The two compilers have the same Roslyn code and emit the same IL, yet 70 of 4096 bytes differ: the PDB records the compiler's commit, and the DLL a hash of the PDB. | TOOL / ENV | csc | upstream | closed |
| <a name="e1-s1-04"></a>**E1-S1-04** (E4) | Microsoft's csc is a different binary on macOS and Linux, but both gave the same bytes. The output follows the compiler's Roslyn commit, not its file hash. | STABLE | Microsoft | not needed | closed |
| <a name="e1-s1-05"></a>**E1-S1-05** (E5) | The PE `TimeDateStamp` is part of a content hash, not a time. It changes only when the content changes. | STABLE | csc | not needed | closed |
| <a name="e1-s1-06"></a>**E1-S1-06** (E6) | Another build path changed the DLL and the PDB: both hold absolute paths. | PATH | csc | our build | closed |
| <a name="e1-s1-07"></a>**E1-S1-07** (E7) | Time, locale, umask, exec path and file order changed no byte of the empty class. | STABLE | – | not needed | closed |
| <a name="e1-s1-08"></a>**E1-S1-08** (W1) | Two clean builds of the whole solution at the same path: 0 of 1610 files differ. | STABLE | csc, MSBuild | not needed | closed |
| <a name="e1-s1-09"></a>**E1-S1-09** (W3) | All four PDBs held absolute source paths. | PATH | csc | our build | closed |
| <a name="e1-s1-10"></a>**E1-S1-10** (W4) | The DLL holds the PDB's path. A path 2 characters longer moves every address after it. | PATH | csc | our build | closed |
| <a name="e1-s1-11"></a>**E1-S1-11** (W5) | Four generated regex types are named by a hash of the source file's path. | PATH | csc, regex generator | our build | closed |
| <a name="e1-s1-12"></a>**E1-S1-12** (W6) | `ContinuousIntegrationBuild` maps the source root only when Source Link finds `.git`. In an export it mapped only the NuGet cache. Fixed with an explicit `PathMap`. | PATH | SDK Source Link targets | our build | closed |
| <a name="e1-s1-13"></a>**E1-S1-13** (W7) | The Razor generator writes the absolute `.cshtml` path into generated C#, and `PathMap` does not reach that text. Fixed in WS.PEMS by deleting two unused pages; open for other projects. | PATH | Razor source generator | our build | closed |
| <a name="e1-s1-14"></a>**E1-S1-14** (W8) | `spa.proxy.json` holds the path to `ClientApp/`. Development only, not shipped. | PATH | SpaProxy targets | – | open |
| <a name="e1-s1-15"></a>**E1-S1-15** (W9) | `staticwebassets.runtime.json` holds paths to `obj/` and the NuGet cache. Development only, not shipped. | PATH | SDK | – | open |
| <a name="e1-s1-16"></a>**E1-S1-16** (W10) | A green result for time, locale, umask and exec path on stage 1. Withdrawn: the compiler server kept the control build's environment (E1-M-07). | METHOD | – | – | withdrawn |
| <a name="e1-s1-17"></a>**E1-S1-17** (W12) | MSBuild sorts the source files before the compiler sees them, so the directory's file order does not matter. | STABLE | MSBuild | not needed | closed |
| <a name="e1-s1-18"></a>**E1-S1-18** (W13) | Building with and without the compiler server gave the same 639 files. | STABLE | MSBuild, csc | not needed | closed |
| <a name="e1-s1-19"></a>**E1-S1-19** (W15) | A cold restore on another machine resolved the same versions and hashes for all packages. | STABLE | NuGet | not needed | closed |
| <a name="e1-s1-20"></a>**E1-S1-20** (W34) | Stage 1 with the compiler inside the variation, nine axes: no difference. | STABLE | – | not needed | closed |
| <a name="e1-s1-21"></a>**E1-S1-21** (W49) | The explicit `PathMap` also rewrote `[CallerFilePath]`, which broke the tests' search for the solution folder. | CONFIG | csc, Testcontainers | our build | closed |
| <a name="e1-s1-22"></a>**E1-S1-22** (W70) | The branch's SDK installer refused every archive on older Python versions. Fixed in the installer. | CONFIG | our installer | our build | closed |

## Stage 2: Publish

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s2-01"></a>**E1-S2-01** (W16) | Two clean publishes with the release's own commands: 1238 identical files. | STABLE | SDK, csc | not needed | closed |
| <a name="e1-s2-02"></a>**E1-S2-02** (W17) | The two json files of E1-S1-14 and E1-S1-15 do not ship. The shipped endpoints file has no paths. | STABLE | SpaProxy, SDK | not needed | closed |
| <a name="e1-s2-03"></a>**E1-S2-03** (W18) | An empty `package-lock.json`, committed by mistake, shipped in the release. | CONFIG | Web SDK content glob | our build | closed |
| <a name="e1-s2-04"></a>**E1-S2-04** (W19) | The release's version flags reach every assembly. A verifier must know the version string. | CI / PROCESS | SDK | not needed | closed |
| <a name="e1-s2-05"></a>**E1-S2-05** (W20) | A publish with `-r linux-x64` puts the platform in the PDB path and the PE header. Compare a DLL only with the same publish command. | CI / PROCESS | SDK | not needed | closed |
| <a name="e1-s2-06"></a>**E1-S2-06** (W21) | 323 of WebAPI's 746 files are copies from Microsoft's runtime packs, which no lock file records. The branch checks them by hash. | INPUT / ENV | Microsoft | upstream | closed |
| <a name="e1-s2-07"></a>**E1-S2-07** (W22) | NuGet lock files pin every package by content hash. A locked restore gives the same release. | INPUT | NuGet | our build | closed |
| <a name="e1-s2-08"></a>**E1-S2-08** (W23) | `RuntimeIdentifiers` on every project made the libraries platform-specific and shipped Windows DLLs in the Linux release. | CONFIG | SDK | our build | closed |
| <a name="e1-s2-09"></a>**E1-S2-09** (W24) | A restore without the version flags made `deps.json` list our libraries as 1.0.0. | CONFIG | NuGet, SDK | our build | closed |
| <a name="e1-s2-10"></a>**E1-S2-10** (W25) | Another build path on the final tree: no difference. | STABLE | – | not needed | closed |
| <a name="e1-s2-11"></a>**E1-S2-11** (W26) | Under Estonian the compiler orders the types it generates for collection expressions differently: 10 of 1237 files. A Roslyn defect, gone on SDK 10. | LOCALE | csc | our build, upstream | closed |
| <a name="e1-s2-12"></a>**E1-S2-12** (W29) | Clock +398 days, umask (contents) and exec path, now with the variation inside the compiler: no difference. | STABLE | – | not needed | closed |
| <a name="e1-s2-13"></a>**E1-S2-13** (W30) | File modes in the release follow the umask: 142 files change under umask 0002. Left to stage 4, whose zip packing sets the modes. | META | csc, MSBuild, SDK, NuGet | – | open |
| <a name="e1-s2-14"></a>**E1-S2-14** (W31) | 311 `Last-Modified` dates come from a NuGet package's zip, not from the build clock. Stable. | STABLE | SDK, NuGet | not needed | closed |
| <a name="e1-s2-15"></a>**E1-S2-15** (W32) | Time zone, environment, home, CPUs and another user: no difference. | STABLE | – | not needed | closed |
| <a name="e1-s2-16"></a>**E1-S2-16** (W33) | With eleven axes varied at once, the release equals the Estonian-only build: no other axis changes a byte. `LC_ALL=C.UTF-8` fixes it. | LOCALE | csc (E1-S2-11) | our build | closed |
| <a name="e1-s2-17"></a>**E1-S2-17** (W45) | The release's builds got the version by different routes. Now one `APP_VERSION` for every build. | CONFIG | MSBuild, workflow | our build | closed |
| <a name="e1-s2-18"></a>**E1-S2-18** (W50) | SDK 10 dates the compressed copies of static files with the time it wrote them. Fixed by turning compression off. | TIME | SDK static web assets | our build, upstream | closed |
| <a name="e1-s2-19"></a>**E1-S2-19** (W58) | GitHub's runner and our machine: our assemblies differ by the runtime patch the compiler ran on, 10.0.13 against 10.0.12. Fixed by installing the `global.json` SDK alone. | TOOL / ENV | setup-dotnet, .NET host | our build | closed |
| <a name="e1-s2-20"></a>**E1-S2-20** (W71) | macOS on arm64 against GitHub's Linux x86-64 runner: nothing differs, frontend and zips included. | STABLE | Roslyn, SWC, zip | not needed | closed |

## Stage 3: Frontend

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s3-01"></a>**E1-S3-01** (W37) | Next.js draws a random build ID in every build and writes it into paths and pages: 110 of 998 files. Set to the release version. | RANDOM | Next.js | our build | closed |
| <a name="e1-s3-02"></a>**E1-S3-02** (W38) | Two frontend builds at the same path, with the build ID fixed: identical. | STABLE | Next.js, webpack, SWC | not needed | closed |
| <a name="e1-s3-03"></a>**E1-S3-03** (W39) | The frontend imports 7 files from outside `ClientApp`. Build it from an export of the whole commit. | INPUT / SOURCE | webpack | the rebuild | closed |
| <a name="e1-s3-04"></a>**E1-S3-04** (W40) | The release asked for Node `20.x`, a major version only. Now pinned in `.nvmrc` and read by every workflow. | TOOL / ENV | setup-node, Node | our build | closed |
| <a name="e1-s3-05"></a>**E1-S3-05** (W41) | 391 of 1509 lock entries had no content hash, so npm trusted the registry for them. Filled in. | INPUT | npm | our build | closed |
| <a name="e1-s3-06"></a>**E1-S3-06** (W43) | Shared CSS files took their order from build timing: 4 of 998 files in 1 of 4 builds. All third-party CSS now imported in one place. | RANDOM | Next.js CSS chunking | our build, upstream | closed |
| <a name="e1-s3-07"></a>**E1-S3-07** (W44) | Between two commits, the minifier gave other short names in the runtime chunk. Never within one commit, so it does not break reproducibility. | STABLE | SWC minifier | – | open |
| <a name="e1-s3-08"></a>**E1-S3-08** (W46) | The release's npm drops the `libc` field from the lock file. It changes which packages install, not the export of one commit. | TOOL / ENV | npm | – | open |
| <a name="e1-s3-09"></a>**E1-S3-09** (W47) | Webpack ordered the pages by build timing: two outputs over 26 builds, 109 of 990 files. A plugin sorts them by name. | RANDOM | Next.js, webpack | our build, upstream | closed |
| <a name="e1-s3-10"></a>**E1-S3-10** (W51) | About 1 in 50 builds, two identical chunks swapped ids: webpack's module order followed timing. The plugin also sorts modules. | RANDOM | webpack | our build, upstream | closed |

## Stage 4: Zip

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s4-01"></a>**E1-S4-01** (W48) | The zips differ in every build though every entry's bytes are equal: times, order, modes, owner. Fixed by normalised packing. | META | Info-ZIP zip | our build | closed |

## Stage 5: The release

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s5-01"></a>**E1-S5-01** (W52) | The `ef bundle` migrator is built in a random `/tmp` folder: 93 of 827,679,078 bytes differ. Now a project in the repository, where `PathMap` applies. | PATH | dotnet ef | our build | closed |
| <a name="e1-s5-02"></a>**E1-S5-02** (W53) | On .NET 10 the migration jobs failed before building: `dotnet ef` needs a restore first. | CONFIG | dotnet-ef 10 | our build | closed |
| <a name="e1-s5-03"></a>**E1-S5-03** (W54) | On macOS the migrator's locked restore failed: the SDK added the Mac's platform, which the lock does not hold. | CONFIG | SDK | our build | closed |
| <a name="e1-s5-04"></a>**E1-S5-04** (W55) | The Windows release, built on Linux as its job builds it: 2132 files identical under no variation, all axes and Estonian. | STABLE | – | not needed | closed |
| <a name="e1-s5-05"></a>**E1-S5-05** (W59) | Signing gives each of 177 files a timestamped signature, so two signed builds always differ. Check a rebuild by pasting the release's signatures onto it. | TIME / PROCESS | jsign, timestamp server | the rebuild | closed |
| <a name="e1-s5-06"></a>**E1-S5-06** (W61) | The SQL script from two exports, at two paths and under another locale and time zone: identical. | STABLE | EF Core | not needed | closed |
| <a name="e1-s5-07"></a>**E1-S5-07** (W63) | `SHA256SUMS` lists the files in the locale's sort order. Fixed with `LC_ALL=C`. | LOCALE | bash, glibc | our build | closed |
| <a name="e1-s5-08"></a>**E1-S5-08** (W64) | On a self-hosted runner the Windows job took a frontend export that another job had left on the machine. It now always downloads the release's own. | INPUT | release workflow | our build | closed |
| <a name="e1-s5-09"></a>**E1-S5-09** (W66) | `SHA256SUMS` named three files by a folder that the GitHub Release does not have, so a download could not be checked. | CONFIG | release workflow | our build | closed |
| <a name="e1-s5-10"></a>**E1-S5-10** (W69) | `dotnet tool restore` can run a tool from another job's folder on a shared runner. The migration job now has its own CLI home. | TOOL | .NET CLI | our build | closed |

## Stage 6: Container images

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-s6-01"></a>**E1-S6-01** (W56) | The WebAPI and job worker images differ in times only. Fixed with `SOURCE_DATE_EPOCH` and BuildKit's `rewrite-timestamp`. | TIME | BuildKit | our build | closed |
| <a name="e1-s6-02"></a>**E1-S6-02** (W60) | The MCP images kept files that build steps write as a side effect: font caches, Node's compile cache, test durations. Removed in each step. | ? | fontconfig, npm, vitest | our build | closed |
| <a name="e1-s6-03"></a>**E1-S6-03** (W62) | The migrations image, from the manual image script, had the same time difference as E1-S6-01. Fixed the same way. | TIME | BuildKit | our build | closed |
| <a name="e1-s6-04"></a>**E1-S6-04** (W65) | Image tags point at attestations that hold the build's clock and a random id, so tags differ in every build. Compare the image manifest instead. | TIME | BuildKit, syft | the rebuild | closed |
| <a name="e1-s6-05"></a>**E1-S6-05** (W67) | The MCP images install Debian packages from the live archive. Now installed from a dated snapshot. | INPUT | apt, Debian | our build | closed |
| <a name="e1-s6-06"></a>**E1-S6-06** (W68) | canvas downloads a prebuilt binary from GitHub without a checksum. Now added by its SHA-256. | INPUT | prebuild-install | our build | closed |

## The method

| Id | Finding | Code | Bytes written by | Fix in | Status |
| --- | --- | --- | --- | --- | --- |
| <a name="e1-m-01"></a>**E1-M-01** (E8) | A command-line `PathMap` must use the shell's `$PWD`. `$(MSBuildProjectDirectory)` is ignored there without a warning. | METHOD | MSBuild | the rebuild | closed |
| <a name="e1-m-02"></a>**E1-M-02** (E9) | Sorting one file list under two locales gave two different hash lists. | METHOD | the OS | the rebuild | closed |
| <a name="e1-m-03"></a>**E1-M-03** (E10) | Deleting only `bin/` does not rebuild: MSBuild copies the old files from `obj/` again. | METHOD | MSBuild | the rebuild | closed |
| <a name="e1-m-04"></a>**E1-M-04** (W2) | Deleting `obj/` between builds also deletes the restore's output, so both builds fail. | METHOD | NuGet | the rebuild | closed |
| <a name="e1-m-05"></a>**E1-M-05** (W11) | Our clean step missed the test project, which then built in only one of the two builds. | METHOD | our script | the rebuild | closed |
| <a name="e1-m-06"></a>**E1-M-06** (W14) | The shared droplet (1 CPU, 1 GB) could not compile WS.PEMS in 3 hours. A verifier needs several GB of RAM. | METHOD | – | – | open |
| <a name="e1-m-07"></a>**E1-M-07** (W27) | reprotest's second build reuses the compiler server that the first build started, so the varied environment never reaches the compiler. Fix: shut the build servers down before each build. | METHOD | .NET build servers | the rebuild | closed |
| <a name="e1-m-08"></a>**E1-M-08** (W28) | reprotest also fixes settings it does not vary: one CPU, `TZ=GMT+12`, `LANG=C.UTF-8`, `HOME` in the build folder. | METHOD | reprotest | not needed | closed |
| <a name="e1-m-09"></a>**E1-M-09** (W35) | With MSBuild's node reuse off, no compiler server or worker node survived any of 32 runs. | METHOD | MSBuild | the rebuild | closed |
| <a name="e1-m-10"></a>**E1-M-10** (W36) | The working directory does not show which build a process belongs to; `HOME` does. | METHOD | – | the rebuild | closed |
| <a name="e1-m-11"></a>**E1-M-11** (W42) | Stage 2 was first measured without the frontend export that CI copies into `wwwroot/`. | METHOD | MSBuild | the rebuild | closed |
| <a name="e1-m-12"></a>**E1-M-12** (W57) | BuildKit reuses a cached `WORKDIR` step despite `--no-cache`, so one builder can hide a time difference. | METHOD | BuildKit | not needed | closed |
| <a name="e1-m-13"></a>**E1-M-13** (R1) | The `aslr` axis alone changes nothing: both builds run with ASLR on. Only `kernel` turns it off. | METHOD | reprotest | – | open |
| <a name="e1-m-14"></a>**E1-M-14** (R2) | The `kernel` axis varies two things: the reported kernel version and ASLR. | METHOD | reprotest | not needed | closed |
| <a name="e1-m-15"></a>**E1-M-15** (R3) | Axes change more than their names say: `build_path` moves `HOME`, and `user_group` replaces `PATH`. | METHOD | reprotest | not needed | closed |
| <a name="e1-m-16"></a>**E1-M-16** (R4) | The builds inherit the whole environment of the shell that starts reprotest, 105 variables in our case. Start it under `env -i`. | METHOD | reprotest | the rebuild | closed |
| <a name="e1-m-17"></a>**E1-M-17** (R5) | Under reprotest's fixed setting, the caller's other locale variables still apply. Only `LC_ALL`, `LC_MESSAGES` and `LANG` decide ICU's locale. | METHOD | reprotest, ICU | not needed | closed |
| <a name="e1-m-18"></a>**E1-M-18** (R6) | On a green run reprotest replaces the second build's output with a link to the first. Compare hashes across runs, not only verdicts. | METHOD | reprotest | not needed | closed |
| <a name="e1-m-19"></a>**E1-M-19** (R7) | The `time` axis silently skips its shift when the newest source file is over 398 days old. | METHOD | reprotest | the rebuild | closed |
| <a name="e1-m-20"></a>**E1-M-20** (R8) | reprotest's log names each build's varied axes and values, and its exit code tells pass, differ and fail apart. | METHOD | reprotest | not needed | closed |
| <a name="e1-m-21"></a>**E1-M-21** (T1) | npm, pip, gem, Maven and Go leave no process alive between reprotest's builds. .NET's compiler server does (E1-M-07). | METHOD | – | not needed | closed |
| <a name="e1-m-22"></a>**E1-M-22** (T2) | The `time` axis cannot move the clock of a static binary: Go's compiler reads the real time. | METHOD | libfaketime | – | open |
| <a name="e1-m-23"></a>**E1-M-23** (T3) | Under `time`, pip's build fails the TLS check against PyPI. | METHOD | pip | the rebuild | open |
| <a name="e1-m-24"></a>**E1-M-24** (T4) | reprotest's `HOME` does not reach Maven, which still uses the real `~/.m2`. | METHOD | Maven | not needed | closed |
