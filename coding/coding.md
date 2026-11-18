# Proposed coding of the findings

Claude's proposal, 18 November 2026, using [the codebook](codebook.md). Peter checks it. Experiment 1 counts findings; experiment 2 counts cause types and packages.

Ids: `E1-S3-02` is experiment 1, stage 3, finding 2 (stages: 1 build, 2 publish, 3 frontend, 4 zip, 5 release, 6 images; `M` is the method). `E2a-04` and `E2b-07` are cause types in experiment 2a and 2b. Each id in experiment 1 links to its finding.

## Experiment 1: WS.PEMS

### Causes of a difference (39)

| Id | Finding | Cause | Note |
| --- | --- | --- | --- |
| [E1-S1-06](../1-phoenix/findings/by-category.md#e1-s1-06) | Another build path changed the DLL and the PDB: both hold absolute paths. | PATH |  |
| [E1-S1-09](../1-phoenix/findings/by-category.md#e1-s1-09) | All four PDBs held absolute source paths. | PATH |  |
| [E1-S1-10](../1-phoenix/findings/by-category.md#e1-s1-10) | The DLL holds the PDB's path. | PATH |  |
| [E1-S1-11](../1-phoenix/findings/by-category.md#e1-s1-11) | Four generated regex types are named by a hash of the source file's path. | PATH |  |
| [E1-S1-12](../1-phoenix/findings/by-category.md#e1-s1-12) | `ContinuousIntegrationBuild` maps the source root only when Source Link finds `.git`. | PATH |  |
| [E1-S1-13](../1-phoenix/findings/by-category.md#e1-s1-13) | The Razor generator writes the absolute `.cshtml` path into generated C#, and `PathMap` does not reach that text. | PATH |  |
| [E1-S1-14](../1-phoenix/findings/by-category.md#e1-s1-14) | `spa.proxy.json` holds the path to `ClientApp/`. | PATH | file does not ship |
| [E1-S1-15](../1-phoenix/findings/by-category.md#e1-s1-15) | `staticwebassets.runtime.json` holds paths to `obj/` and the NuGet cache. | PATH | file does not ship |
| [E1-S5-01](../1-phoenix/findings/by-category.md#e1-s5-01) | The `ef bundle` migrator is built in a random `/tmp` folder: 93 of 827,679,078 bytes differ. | PATH |  |
| [E1-S2-06](../1-phoenix/findings/by-category.md#e1-s2-06) | 323 of WebAPI's 746 files are copies from Microsoft's runtime packs, which no lock file records. | INPUT | runtime packs not in any lock file |
| [E1-S2-07](../1-phoenix/findings/by-category.md#e1-s2-07) | NuGet lock files pin every package by content hash. | INPUT |  |
| [E1-S3-03](../1-phoenix/findings/by-category.md#e1-s3-03) | The frontend imports 7 files from outside `ClientApp`. | INPUT | needs the whole commit |
| [E1-S3-05](../1-phoenix/findings/by-category.md#e1-s3-05) | 391 of 1509 lock entries had no content hash, so npm trusted the registry for them. | INPUT |  |
| [E1-S5-08](../1-phoenix/findings/by-category.md#e1-s5-08) | On a self-hosted runner the Windows job took a frontend export that another job had left on the machine. | INPUT |  |
| [E1-S6-05](../1-phoenix/findings/by-category.md#e1-s6-05) | The MCP images install Debian packages from the live archive. | INPUT |  |
| [E1-S6-06](../1-phoenix/findings/by-category.md#e1-s6-06) | canvas downloads a prebuilt binary from GitHub without a checksum. | INPUT |  |
| [E1-S1-02](../1-phoenix/findings/by-category.md#e1-s1-02) | Two machines gave different DLLs from the same source. | TOOL |  |
| [E1-S1-03](../1-phoenix/findings/by-category.md#e1-s1-03) | The two compilers have the same Roslyn code and emit the same IL, yet 70 of 4096 bytes differ: the PDB records the compiler's commit, and the DLL a hash of the PDB. | TOOL |  |
| [E1-S2-19](../1-phoenix/findings/by-category.md#e1-s2-19) | GitHub's runner and our machine: our assemblies differ by the runtime patch the compiler ran on, 10.0.13 against 10.0.12. | TOOL |  |
| [E1-S3-04](../1-phoenix/findings/by-category.md#e1-s3-04) | The release asked for Node `20.x`, a major version only. | TOOL | Node pinned by major version only |
| [E1-S3-08](../1-phoenix/findings/by-category.md#e1-s3-08) | The release's npm drops the `libc` field from the lock file. | TOOL | borderline: npm version changes what installs (INPUT?) |
| [E1-S5-10](../1-phoenix/findings/by-category.md#e1-s5-10) | `dotnet tool restore` can run a tool from another job's folder on a shared runner. | TOOL | borderline: leftover state on a shared runner (INPUT?) |
| [E1-S2-18](../1-phoenix/findings/by-category.md#e1-s2-18) | SDK 10 dates the compressed copies of static files with the time it wrote them. | TIME |  |
| [E1-S5-05](../1-phoenix/findings/by-category.md#e1-s5-05) | Signing gives each of 177 files a timestamped signature, so two signed builds always differ. | TIME | signature timestamps; rebuilder lacks the key |
| [E1-S6-01](../1-phoenix/findings/by-category.md#e1-s6-01) | The WebAPI and job worker images differ in times only. | TIME |  |
| [E1-S6-03](../1-phoenix/findings/by-category.md#e1-s6-03) | The migrations image, from the manual image script, had the same time difference as W56. | TIME |  |
| [E1-S6-04](../1-phoenix/findings/by-category.md#e1-s6-04) | Image tags point at attestations that hold the build's clock and a random id, so tags differ in every build. | TIME | attestation also holds a random id (RANDOM) |
| [E1-S3-01](../1-phoenix/findings/by-category.md#e1-s3-01) | Next.js draws a random build ID in every build and writes it into paths and pages: 110 of 998 files. | RANDOM |  |
| [E1-S3-06](../1-phoenix/findings/by-category.md#e1-s3-06) | Shared CSS files took their order from build timing: 4 of 998 files in 1 of 4 builds. | RANDOM |  |
| [E1-S3-09](../1-phoenix/findings/by-category.md#e1-s3-09) | Webpack ordered the pages by build timing: two outputs over 26 builds, 109 of 990 files. | RANDOM |  |
| [E1-S3-10](../1-phoenix/findings/by-category.md#e1-s3-10) | About 1 in 50 builds, two identical chunks swapped ids: webpack's module order followed timing. | RANDOM |  |
| [E1-S2-11](../1-phoenix/findings/by-category.md#e1-s2-11) | Under Estonian the compiler orders the types it generates for collection expressions differently: 10 of 1237 files. | LOCALE | compiler defect, gone on SDK 10 |
| [E1-S2-16](../1-phoenix/findings/by-category.md#e1-s2-16) | With eleven axes varied at once, the release equals the Estonian-only build: no other axis changes a byte. | LOCALE | only axis of eleven that changed bytes |
| [E1-S5-07](../1-phoenix/findings/by-category.md#e1-s5-07) | `SHA256SUMS` lists the files in the locale's sort order. | LOCALE |  |
| [E1-S2-04](../1-phoenix/findings/by-category.md#e1-s2-04) | The release's version flags reach every assembly. | CI | verifier must know the version string |
| [E1-S2-05](../1-phoenix/findings/by-category.md#e1-s2-05) | A publish with `-r linux-x64` puts the platform in the PDB path and the PE header. | CI | verifier must know the publish command |
| [E1-S2-13](../1-phoenix/findings/by-category.md#e1-s2-13) | File modes in the release follow the umask: 142 files change under umask 0002. | META |  |
| [E1-S4-01](../1-phoenix/findings/by-category.md#e1-s4-01) | The zips differ in every build though every entry's bytes are equal: times, order, modes, owner. | META | borderline: zip times are TIME by rule 2, order FSORDER |
| [E1-S6-02](../1-phoenix/findings/by-category.md#e1-s6-02) | The MCP images kept files that build steps write as a side effect: font caches, Node's compile cache, test durations. | ? | side products of build steps (caches); no code fits |

### Compared with CI or another machine

These causes came from comparing with a build we did not make ourselves, so they also say what a rebuilder was missing.

| Id | Cause | Missing for the rebuild |
| --- | --- | --- |
| [E1-S2-06](../1-phoenix/findings/by-category.md#e1-s2-06) | INPUT | ENV |
| [E1-S3-03](../1-phoenix/findings/by-category.md#e1-s3-03) | INPUT | SOURCE |
| [E1-S1-02](../1-phoenix/findings/by-category.md#e1-s1-02) | TOOL | ENV |
| [E1-S1-03](../1-phoenix/findings/by-category.md#e1-s1-03) | TOOL | ENV |
| [E1-S2-19](../1-phoenix/findings/by-category.md#e1-s2-19) | TOOL | ENV |
| [E1-S3-04](../1-phoenix/findings/by-category.md#e1-s3-04) | TOOL | ENV |
| [E1-S3-08](../1-phoenix/findings/by-category.md#e1-s3-08) | TOOL | ENV |
| [E1-S5-05](../1-phoenix/findings/by-category.md#e1-s5-05) | TIME | PROCESS |
| [E1-S2-04](../1-phoenix/findings/by-category.md#e1-s2-04) | CI | PROCESS |
| [E1-S2-05](../1-phoenix/findings/by-category.md#e1-s2-05) | CI | PROCESS |

### Findings that are not causes

- **Setup faults we found and corrected** (9): [E1-S1-21](../1-phoenix/findings/by-category.md#e1-s1-21), [E1-S1-22](../1-phoenix/findings/by-category.md#e1-s1-22), [E1-S2-03](../1-phoenix/findings/by-category.md#e1-s2-03), [E1-S2-08](../1-phoenix/findings/by-category.md#e1-s2-08), [E1-S2-09](../1-phoenix/findings/by-category.md#e1-s2-09), [E1-S2-17](../1-phoenix/findings/by-category.md#e1-s2-17), [E1-S5-02](../1-phoenix/findings/by-category.md#e1-s5-02), [E1-S5-03](../1-phoenix/findings/by-category.md#e1-s5-03), [E1-S5-09](../1-phoenix/findings/by-category.md#e1-s5-09)
- **Varied, and no byte changed** (20): [E1-S1-01](../1-phoenix/findings/by-category.md#e1-s1-01), [E1-S1-04](../1-phoenix/findings/by-category.md#e1-s1-04), [E1-S1-05](../1-phoenix/findings/by-category.md#e1-s1-05), [E1-S1-07](../1-phoenix/findings/by-category.md#e1-s1-07), [E1-S1-08](../1-phoenix/findings/by-category.md#e1-s1-08), [E1-S1-17](../1-phoenix/findings/by-category.md#e1-s1-17), [E1-S1-18](../1-phoenix/findings/by-category.md#e1-s1-18), [E1-S1-19](../1-phoenix/findings/by-category.md#e1-s1-19), [E1-S1-20](../1-phoenix/findings/by-category.md#e1-s1-20), [E1-S2-01](../1-phoenix/findings/by-category.md#e1-s2-01), [E1-S2-02](../1-phoenix/findings/by-category.md#e1-s2-02), [E1-S2-10](../1-phoenix/findings/by-category.md#e1-s2-10), [E1-S2-12](../1-phoenix/findings/by-category.md#e1-s2-12), [E1-S2-14](../1-phoenix/findings/by-category.md#e1-s2-14), [E1-S2-15](../1-phoenix/findings/by-category.md#e1-s2-15), [E1-S2-20](../1-phoenix/findings/by-category.md#e1-s2-20), [E1-S3-02](../1-phoenix/findings/by-category.md#e1-s3-02), [E1-S3-07](../1-phoenix/findings/by-category.md#e1-s3-07), [E1-S5-04](../1-phoenix/findings/by-category.md#e1-s5-04), [E1-S5-06](../1-phoenix/findings/by-category.md#e1-s5-06)
- **About how we measured** (25): [E1-S1-16](../1-phoenix/findings/by-category.md#e1-s1-16), [E1-M-01](../1-phoenix/findings/by-category.md#e1-m-01), [E1-M-02](../1-phoenix/findings/by-category.md#e1-m-02), [E1-M-03](../1-phoenix/findings/by-category.md#e1-m-03), [E1-M-04](../1-phoenix/findings/by-category.md#e1-m-04), [E1-M-05](../1-phoenix/findings/by-category.md#e1-m-05), [E1-M-06](../1-phoenix/findings/by-category.md#e1-m-06), [E1-M-07](../1-phoenix/findings/by-category.md#e1-m-07), [E1-M-08](../1-phoenix/findings/by-category.md#e1-m-08), [E1-M-09](../1-phoenix/findings/by-category.md#e1-m-09), [E1-M-10](../1-phoenix/findings/by-category.md#e1-m-10), [E1-M-11](../1-phoenix/findings/by-category.md#e1-m-11), [E1-M-12](../1-phoenix/findings/by-category.md#e1-m-12), [E1-M-13](../1-phoenix/findings/by-category.md#e1-m-13), [E1-M-14](../1-phoenix/findings/by-category.md#e1-m-14), [E1-M-15](../1-phoenix/findings/by-category.md#e1-m-15), [E1-M-16](../1-phoenix/findings/by-category.md#e1-m-16), [E1-M-17](../1-phoenix/findings/by-category.md#e1-m-17), [E1-M-18](../1-phoenix/findings/by-category.md#e1-m-18), [E1-M-19](../1-phoenix/findings/by-category.md#e1-m-19), [E1-M-20](../1-phoenix/findings/by-category.md#e1-m-20), [E1-M-21](../1-phoenix/findings/by-category.md#e1-m-21), [E1-M-22](../1-phoenix/findings/by-category.md#e1-m-22), [E1-M-23](../1-phoenix/findings/by-category.md#e1-m-23), [E1-M-24](../1-phoenix/findings/by-category.md#e1-m-24)

## Experiment 2a: two builds of our own

| Id | Cause type | Packages | n | Cause | Note |
| --- | --- | --- | --- | --- | --- |
| E2a-01 | Date in the package version | Azure SDK, System.ClientModel | 8 | TIME |  |
| E2a-02 | Clock in the package version | IdentityModel 8.23.0 | 5 | TIME |  |
| E2a-03 | Copyright year from the clock | Swashbuckle, Stateless | 4 | TIME |  |
| E2a-04 | npm under the time variation | Swashbuckle ReDoc, SwaggerUI | 2 | METHOD | libfaketime breaks npm; not a cause |
| E2a-05 | Arcade's date-based build number | Build.Framework | 1 | TIME |  |
| E2a-06 | Hash of the project path in the PDB | Quartz | 4 | PATH |  |
| E2a-07 | PDB path not mapped | ClosedXML | 1 | PATH |  |

## Experiment 2b: rebuilds compared with nuget.org

| Id | Cause type | Packages | n | Cause | Missing for the rebuild | Note |
| --- | --- | --- | --- | --- | --- | --- |
| E2b-01 | Arcade's development versioning | Roslyn, EF Core, Sqlite | 17 | TIME | PROCESS | OfficialBuildId missing |
| E2b-02 | Clock in the version | IdentityModel | 9 | TIME | PROCESS | check: is the version enough? |
| E2b-03 | Date suffix on unofficial builds | Azure SDK, System.ClientModel | 8 | TIME | PROCESS | official-build flag missing |
| E2b-04 | Copyright year from the build clock | Swashbuckle, Stateless | 6 | TIME | PROCESS | build date not recorded |
| E2b-05 | Attributes written by the CI script | Bogus, YamlDotNet | 3 | CI | PROCESS |  |
| E2b-06 | Version computed from git | MediatR.Contracts, ExCSS | 2 | CI | SOURCE |  |
| E2b-07 | Targeting pack | SharpZipLib | 2 | TOOL | ENV |  |
| E2b-08 | RepositoryUrl form | two Serilog packages | 2 | CI | SOURCE | URL taken from the checkout |
| E2b-09 | Signing key | RecyclableMemoryStream | 1 | CI | PROCESS |  |
| E2b-10 | Not inspected | Google.Protobuf, ShimSkiaSharp | 5 | ? | ? | not inspected |
