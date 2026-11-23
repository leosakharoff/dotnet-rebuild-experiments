# Experiment 1 findings

Experiment 1 produced 93 findings: 34 causes of differences, 4 findings [merged](#merged-findings) into one of those causes, 9 setup faults, 20 checks that found no difference and 26 findings about how we measured.
We saw 26 of the 34 causes as differing bytes. We found the other 8 by inspecting the build: [E1-S2-06](#e1-s2-06), [E1-S2-07](#e1-s2-07), [E1-S3-04](#e1-s3-04), [E1-S3-05](#e1-s3-05), [E1-S5-07](#e1-s5-07), [E1-S5-10](#e1-s5-10), [E1-S6-03](#e1-s6-03), [E1-S6-06](#e1-s6-06).
Four measurement findings describe limitations.
In `E1-S3-02`, `S3` means stage 3 and `02` means finding 2. The prefix `E1-M` identifies a measurement finding.
The [identifier table](../../categories/codes.tsv) lists the old identifiers. The [stage guide](stages.md) shows each stage before and after the fixes. The [rebuilds](rebuilds.md) record the three rebuilds of the published release.

**Outcome** says how each cause was dealt with. *Code and settings*: WS.PEMS's source code or project configuration changed (project files, lock files, version pins). *Build scripts*: the CI workflow, release scripts or Dockerfiles changed (commands, flags, environment variables, installation, packing). *Verifier action*: the release stays as it is, and someone who rebuilds it to check it must take an extra step. *Files outside the release*: the difference is in a development file that does not ship, so no fix is needed.

## Causes of differences

### Stage 1. Build

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s1-02"></a> **E1-S1-02** | The same source produced different assemblies on two machines. Arch and Microsoft both called their compiler 9.0.120. The debug symbols recorded each compiler's commit ([E1-S1-03](#e1-s1-03)). | Build tool version | Pinned the development kit to 10.0.401 in `global.json`, disabled roll-forward and installed it by hash in the release workflow. | Verifier action. A verifier needs Microsoft's SDK build, not only its version number; the build scripts now install it by hash. |
| <a name="e1-s1-09"></a> **E1-S1-09** | All four debug symbol files recorded absolute source paths, so changing the build folder changed them ([E1-S1-06](#e1-s1-06)). In an export without `.git`, `ContinuousIntegrationBuild` left them unmapped ([E1-S1-12](#e1-s1-12)). | Build path | Mapped the source paths with `PathMap`. | Code and settings. Mapped the source paths with PathMap. |
| <a name="e1-s1-10"></a> **E1-S1-10** | The assembly stored the path to its debug symbols. Two extra characters in that path shifted every address that followed. | Build path | Mapped the path with `PathMap`. | Code and settings. Mapped the debug symbol path with PathMap. |
| <a name="e1-s1-11"></a> **E1-S1-11** | The names of four generated regular expression types included a hash of the source file’s path. | Build path | Mapped the source path with `PathMap`. | Code and settings. Mapped the source path with PathMap. |
| <a name="e1-s1-13"></a> **E1-S1-13** | Razor wrote the absolute `.cshtml` path into generated C# code, beyond the reach of `PathMap`. | Build path | Deleted two unused Razor pages. | Code and settings. Removed two unused Razor pages. |
| <a name="e1-s1-14"></a> **E1-S1-14** | `spa.proxy.json` contained the path to `ClientApp/`. | Build path | None needed. | Files outside the release. The development file does not ship. |
| <a name="e1-s1-15"></a> **E1-S1-15** | `staticwebassets.runtime.json` contained paths to `obj/` and the NuGet cache. | Build path | None needed. | Files outside the release. The development file does not ship. |

### Stage 2. Publish

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s2-04"></a> **E1-S2-04** | The release workflow passed its version string to every assembly. | CI/CD modification | None needed. | Verifier action. A verifier needs the release's version string. |
| <a name="e1-s2-05"></a> **E1-S2-05** | Publishing with `-r linux-x64` put the platform in the debug symbol path and the executable header. | CI/CD modification | None needed. | Verifier action. A verifier must use the release's publish command. |
| <a name="e1-s2-06"></a> **E1-S2-06** | Microsoft’s runtime packs supplied 323 of the web application’s 746 files. The package lock files did not record them. | Package dependency | Checked the packs by hash against `nuget-downloads.lock.json`. | Build scripts. No lock file records the runtime packs, so the build scripts check them by hash. |
| <a name="e1-s2-07"></a> **E1-S2-07** | NuGet lock files record a content hash for every package. Restoring from those hashes reproduced the release. | Package dependency | Added lock files and enabled locked restores in the release workflow. | Code and settings. The release workflow also enforces a locked restore. |
| <a name="e1-s2-11"></a> **E1-S2-11** | Under Estonian settings, Roslyn reordered the types it generated for collection expressions. That changed 10 of 1,237 files. | Locale | Set `LC_ALL=C.UTF-8`. | Build scripts. Set LC_ALL=C.UTF-8 as a workaround for the compiler defect. |
| <a name="e1-s2-18"></a> **E1-S2-18** | Version 10 of the development kit stamped compressed copies of static files with the time it wrote them. | Build timestamp | Turned off compression with `CompressionEnabled=false`. | Code and settings. Static asset compression turned off in the web application. |
| <a name="e1-s2-19"></a> **E1-S2-19** | The compiler ran on different runtime patches on the GitHub runner and our machine, 10.0.13 and 10.0.12. The assemblies differed. | Build tool version | Installed only the kit named in `global.json` in an empty folder. Checked its hash and that only its own runtime was present. | Build scripts. Installed the kit named in global.json alone and checked its hash and runtime. |

### Stage 3. Frontend

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s3-01"></a> **E1-S3-01** | Next.js wrote a new random build identifier into paths and pages on every build. This changed 110 of 998 files. | Randomness | Used the release version from `APP_VERSION` as the build identifier. | Code and settings. The build ID is set to the release version. |
| <a name="e1-s3-03"></a> **E1-S3-03** | The frontend imported seven files from outside `ClientApp/`. | Package dependency | No code change. Rebuild from an export of the whole commit. | Verifier action. Rebuild the frontend from an export of the whole commit. |
| <a name="e1-s3-04"></a> **E1-S3-04** | The release requested Node `20.x`, which specified only the major version. | Build tool version | Pinned an exact version in `.nvmrc`. Every workflow reads it and installs Node by hash. | Code and settings. Each workflow also reads the Node pin and installs Node by hash. |
| <a name="e1-s3-05"></a> **E1-S3-05** | Of 1,509 package lock entries, 391 lacked a content hash. For those entries, npm trusted the registry. | Package dependency | Filled in the missing hashes. | Code and settings. Added the missing hashes to the package lock file. |
| <a name="e1-s3-06"></a> **E1-S3-06** | Build timing probably changed the order of shared style sheets. Four of 998 files differed in one of four builds. | Randomness | Imported all third-party style sheets in one place, `_app.tsx`. | Code and settings. Moved the third-party style imports into _app.tsx. |
| <a name="e1-s3-08"></a> **E1-S3-08** | The release’s version of npm dropped `libc` from 30 entries when it wrote the lock file. That could change which packages npm installs. The export of a given commit stayed the same. | Build tool version | Pinned npm 11.21.2 by hash in `package.json` (`packageManager`). The frontend workflow and the WebAPI Dockerfile install exactly that npm and check its version. npm 11 keeps `libc` when it writes the lock. | Code and settings. Every build installs the pinned npm. So far checked on macOS only. |
| <a name="e1-s3-09"></a> **E1-S3-09** | Webpack ordered pages by build timing. Across 26 builds, it produced two outputs that differed in 109 of 990 files. | Randomness | Added a plugin that sorts page entries by name before webpack creates chunks. | Code and settings. Added a plugin to sort page entries. |
| <a name="e1-s3-10"></a> **E1-S3-10** | In about one build in 50, two identical chunks swapped identifiers because webpack ordered modules by timing. | Randomness | Extended the sorting plugin to modules and their links. | Code and settings. Extended the plugin to sort modules and their links. |

### Stage 4. Zip

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s4-01"></a> **E1-S4-01** | The archive changed on every build even though each file’s contents matched. Entry times, order, permissions and ownership differed; the permissions followed the umask ([E1-S2-13](#e1-s2-13)). Between two builds without variation, only the times and the order differed. | Build timestamp | Standardised all four in `scripts/pack-release-zip.sh`. | Build scripts. Changed the repository's release packing script. |

### Stage 5. Release

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s5-01"></a> **E1-S5-01** | `ef bundle` built the migration program in a random folder under `/tmp`. Of 827,679,078 bytes, 93 differed. | Build path | Moved the migration program into the repository as a project so that `PathMap` applied. | Code and settings. Moved the migration program into the repository so PathMap applied. |
| <a name="e1-s5-05"></a> **E1-S5-05** | Signing added a timestamped signature to each of 177 files. Signing twice gave different bytes. | Build timestamp | For comparison, copied the original release signatures onto the rebuilt files. | Verifier action. Copy the release signatures onto the rebuilt files before comparing them. |
| <a name="e1-s5-07"></a> **E1-S5-07** | The order of files in `SHA256SUMS` could depend on the language setting used to sort them. Three language settings gave the same order. | Locale | Set `LC_ALL=C` when sorting the file list. | Build scripts. Set LC_ALL=C when sorting the checksum list, as a precaution. |
| <a name="e1-s5-08"></a> **E1-S5-08** | On a shared runner, the Windows job picked up a frontend export left by another job. Found in the published v1.0.50. | Package dependency | Made the Windows job download the export for its own release every time. | Build scripts. The Windows job downloads the frontend export for its own release. |
| <a name="e1-s5-10"></a> **E1-S5-10** | On a shared runner, `dotnet tool restore` could run a tool from another job’s folder. | Build tool version | Gave the migration job its own home folder for the command-line tools. | Build scripts. The migration job uses its own tool home folder. |

### Stage 6. Images

| Finding ID | What we found | Cause | What we changed | Outcome |
| --- | --- | --- | --- | --- |
| <a name="e1-s6-01"></a> **E1-S6-01** | Only timestamps differed in the web application and job worker images. | Build timestamp | Set `SOURCE_DATE_EPOCH` and enabled BuildKit’s `rewrite-timestamp`. | Build scripts. Set SOURCE_DATE_EPOCH and enabled rewrite-timestamp. |
| <a name="e1-s6-02"></a> **E1-S6-02** | A test report left in the `MCP` images listed different test durations, in a different order, in each build. Font caches and Node’s compile cache, also left by build steps, were removed without establishing why they differed. | Randomness | Removed those files in each step that created them. | Build scripts. Each image build step removes the files it creates as side effects. |
| <a name="e1-s6-03"></a> **E1-S6-03** | The manual image script built the migrations image without the timestamp settings of [E1-S6-01](#e1-s6-01). Not measured before the fix. | Build timestamp | Applied the same `SOURCE_DATE_EPOCH` and `rewrite-timestamp` settings. | Build scripts. Applied the timestamp settings in the manual image script. |
| <a name="e1-s6-04"></a> **E1-S6-04** | Image tags pointed to attestations containing the build time and a random identifier. The tags changed on every build. | Build timestamp | Use the image manifest for the comparison. | Verifier action. Compare the image manifest. |
| <a name="e1-s6-05"></a> **E1-S6-05** | The `MCP` images installed Debian packages from the live archive. | Package dependency | Installed the packages from a dated snapshot. | Build scripts. The image build installs Debian packages from a dated snapshot. |
| <a name="e1-s6-06"></a> **E1-S6-06** | `canvas` downloaded a prebuilt binary from GitHub without checking its contents. | Package dependency | Added the binary by its `SHA-256` hash. | Build scripts. The image build checks the prebuilt canvas binary by its SHA-256. |

## Merged findings

These findings described a cause that another finding already counts. They keep their identifiers and are not counted again.

| Finding ID | What we found | Merged into |
| --- | --- | --- |
| <a name="e1-s1-03"></a> **E1-S1-03** | Two compilers with the same Roslyn code produced the same instructions, yet 70 of 4,096 bytes differed. The debug symbols recorded the compiler commit, and the assembly recorded the symbols’ hash. | [E1-S1-02](#e1-s1-02) |
| <a name="e1-s1-06"></a> **E1-S1-06** | Changing the build folder changed the assembly and its debug symbols. Both contained absolute paths. | [E1-S1-09](#e1-s1-09), [E1-S1-10](#e1-s1-10) |
| <a name="e1-s2-13"></a> **E1-S2-13** | With `umask 0002`, 142 release files had different permissions. | [E1-S4-01](#e1-s4-01) |
| <a name="e1-s1-12"></a> **E1-S1-12** | In a source export without `.git`, `ContinuousIntegrationBuild` mapped only the NuGet cache. Source Link missed the source root. The same files and hashes differed as before, so this explains why our first fix failed. | [E1-S1-09](#e1-s1-09), [E1-S1-10](#e1-s1-10), [E1-S1-11](#e1-s1-11) |

## Compared with CI or another machine

A rebuild by someone else would hit these causes unless they had something the release does not record. The last column names what was missing, in the three gaps of Solarin et al. (2026): environment, source state and build process.

| Finding ID | Cause | What a rebuilder lacked |
| --- | --- | --- |
| [E1-S1-02](#e1-s1-02) | Build tool version | Environment |
| [E1-S2-04](#e1-s2-04) | CI/CD modification | Build process |
| [E1-S2-05](#e1-s2-05) | CI/CD modification | Build process |
| [E1-S2-06](#e1-s2-06) | Package dependency | Environment |
| [E1-S2-19](#e1-s2-19) | Build tool version | Environment |
| [E1-S3-03](#e1-s3-03) | Package dependency | Source state |
| [E1-S3-04](#e1-s3-04) | Build tool version | Environment |
| [E1-S3-08](#e1-s3-08) | Build tool version | Environment |
| [E1-S5-05](#e1-s5-05) | Build timestamp | Build process |
| [E1-S5-08](#e1-s5-08) | Package dependency | Build process |

## Setup faults

| Finding ID | What we found | What we changed | Outcome |
| --- | --- | --- | --- |
| <a name="e1-s1-21"></a> **E1-S1-21** | The explicit `PathMap` also rewrote `[CallerFilePath]`. The tests could no longer find the solution folder. | The tests find the repository root from their own output folder, `AppContext.BaseDirectory`. | Corrected. |
| <a name="e1-s1-22"></a> **E1-S1-22** | On older Python versions, the branch’s installer rejected every development kit archive. | Made the installer accept only relative names without `..`. | Corrected. |
| <a name="e1-s2-03"></a> **E1-S2-03** | An empty `package-lock.json` had been committed by mistake and shipped in the release. | Deleted the file. | Corrected. |
| <a name="e1-s2-08"></a> **E1-S2-08** | Setting `RuntimeIdentifiers` on every project made the libraries platform-specific. The Linux release included Windows libraries. | Set `RuntimeIdentifiers` only on the programs. | Corrected. |
| <a name="e1-s2-09"></a> **E1-S2-09** | A restore without the release version flags listed our libraries as version 1.0.0 in `deps.json`. | Ran one restore and supplied the release version. | Corrected. |
| <a name="e1-s2-17"></a> **E1-S2-17** | The release builds obtained their version in different ways. | Used one `APP_VERSION` for every build. | Corrected. |
| <a name="e1-s5-02"></a> **E1-S5-02** | On .NET 10, the migration jobs failed before compilation because `dotnet ef` needed a restore first. | Ran a locked restore of the solution before `dotnet ef` in both jobs. | Corrected. |
| <a name="e1-s5-03"></a> **E1-S5-03** | The migration program’s locked restore failed on macOS. The development kit added the Mac platform, which was missing from the lock file. | Set `UseDefaultPublishRuntimeIdentifier=false` in the migration project. | Corrected. |
| <a name="e1-s5-09"></a> **E1-S5-09** | Three paths in `SHA256SUMS` included a folder absent from the GitHub release. The downloaded files could not be verified. | Hashed the files in `db/` from inside `db/`, so every line names a release asset. | Corrected. |

## Checks that found no difference

| Finding ID | What we varied or checked | What happened |
| --- | --- | --- |
| <a name="e1-s1-01"></a> **E1-S1-01** | Built the empty class twice from scratch with the same path, machine and development kit. | The assembly and its debug symbols were identical. |
| <a name="e1-s1-04"></a> **E1-S1-04** | Built with Microsoft’s compiler on macOS and Linux. The compiler binaries differed. | The output bytes matched. They followed the Roslyn commit rather than the compiler file’s hash. |
| <a name="e1-s1-05"></a> **E1-S1-05** | Checked when the executable header’s `TimeDateStamp` changed. | It is part of a content hash. It changed only with the content. |
| <a name="e1-s1-08"></a> **E1-S1-08** | Built the whole solution twice from scratch at the same path. | All 1,610 files matched. |
| <a name="e1-s1-17"></a> **E1-S1-17** | Checked how MSBuild orders source files. | MSBuild sorted source files before compilation, so their directory order could not matter. |
| <a name="e1-s1-18"></a> **E1-S1-18** | Built with and without the compiler server. | All 639 files matched. |
| <a name="e1-s1-19"></a> **E1-S1-19** | Restored packages from an empty cache on another machine. | Every package resolved to the same version and content hash. |
| <a name="e1-s1-20"></a> **E1-S1-20** | Varied nine settings in stage 1 and ran the compiler under the varied settings. | No differences appeared. |
| <a name="e1-s2-01"></a> **E1-S2-01** | Published twice from scratch with the release commands. | All 1,238 files matched. |
| <a name="e1-s2-02"></a> **E1-S2-02** | Checked which paths from the build appeared in the published files. | Neither development file ([E1-S1-14](#e1-s1-14), [E1-S1-15](#e1-s1-15)) shipped. The published endpoints file contained no paths. |
| <a name="e1-s2-10"></a> **E1-S2-10** | Changed the build folder for the final source tree. | No differences appeared. |
| <a name="e1-s2-12"></a> **E1-S2-12** | Moved the clock forward 398 days and varied the default file permissions and executable search path. The compiler ran under the varied settings. | File contents matched. The permissions themselves are covered in [E1-S4-01](#e1-s4-01). |
| <a name="e1-s2-14"></a> **E1-S2-14** | Checked the source of 311 `Last-Modified` dates. | The dates came from a NuGet package archive and were independent of the build clock. |
| <a name="e1-s2-15"></a> **E1-S2-15** | Varied the time zone, environment, home folder, processor count and user. | No differences appeared. |
| <a name="e1-s2-16"></a> **E1-S2-16** | Varied eleven settings together, the language set to Estonian among them. | The release equalled the Estonian-only build: no other setting changed a byte. The one cause is [E1-S2-11](#e1-s2-11). |
| <a name="e1-s2-20"></a> **E1-S2-20** | Compared macOS on `arm64` with GitHub’s Linux runner on `x86-64`. | The compared outputs matched, including the frontend and release archives. |
| <a name="e1-s3-02"></a> **E1-S3-02** | Built the frontend twice at the same path and compared the outputs with the build identifier masked. | The outputs were identical. |
| <a name="e1-s3-07"></a> **E1-S3-07** | Compared the minifier’s short names in the runtime chunk within and between commits. | Names changed only between commits. Rebuilding the same commit preserved them. |
| <a name="e1-s5-04"></a> **E1-S5-04** | Built the Windows release on Linux as its release job does. Compared the baseline with all settings varied and with Estonian alone. | All 2,132 files matched. |
| <a name="e1-s5-06"></a> **E1-S5-06** | Compared the database script from two exports at different paths under different language and time zone settings. | The scripts were identical. |

## Findings about how we measured

| Finding ID | What we found | What we changed | Outcome |
| --- | --- | --- | --- |
| <a name="e1-s1-07"></a> **E1-S1-07** | Time, language, default file permissions, executable search path and file order changed no byte of the empty class. As in [E1-S1-16](#e1-s1-16), the compiler server most likely kept the first build’s environment. | Withdrew the result. Stage 1 was checked again with the compiler under the varied settings ([E1-S1-20](#e1-s1-20)) and for file order ([E1-S1-17](#e1-s1-17)). | Result withdrawn. |
| <a name="e1-s1-16"></a> **E1-S1-16** | Stage 1 initially passed checks for time, language, default file permissions and executable search path. The compiler server had kept the first build’s environment. | Withdrew the result. See the correction in [E1-M-07](#e1-m-07). | Result withdrawn. |
| <a name="e1-m-01"></a> **E1-M-01** | On the command line, `PathMap` silently ignored `$(MSBuildProjectDirectory)`. | Use the shell’s `$PWD` for the path. | Verifier action. |
| <a name="e1-m-02"></a> **E1-M-02** | Sorting the same file list under two language settings produced differently ordered lists of hashes. | Set `LC_ALL=C` in every step that sorts. | Verifier action. |
| <a name="e1-m-03"></a> **E1-M-03** | Deleting only `bin/` did not trigger a rebuild. MSBuild copied the old files back from `obj/`. | Deleted both `bin/` and `obj/` before each build. | Verifier action. |
| <a name="e1-m-04"></a> **E1-M-04** | Deleting `obj/` between builds also removed the restore output. Both builds failed. | Made each run clean, restore and build. | Verifier action. |
| <a name="e1-m-05"></a> **E1-M-05** | The clean step missed the test project, so it compiled in only one of the two builds. | Added the test project's `bin/` and `obj/` to the clean step. | Verifier action. |
| <a name="e1-m-06"></a> **E1-M-06** | A shared machine with one processor and one gigabyte of memory could not compile the project in three hours. | Used a larger machine. | Limitation we report. A verifier needs several gigabytes of memory. |
| <a name="e1-m-07"></a> **E1-M-07** | In `reprotest`, the second build reused the first build’s compiler server. The compiler never saw the varied environment. | Ran `dotnet build-server shutdown` before each build and set `MSBUILDDISABLENODEREUSE=1`. | Fixed in the measurement procedure. Each build started its own processes. |
| <a name="e1-m-08"></a> **E1-M-08** | Even outside the settings being varied, `reprotest` used one processor, `TZ=GMT+12`, `LANG=C.UTF-8` and a `HOME` inside the build folder. | None needed. | No fix needed. |
| <a name="e1-m-09"></a> **E1-M-09** | With MSBuild node reuse disabled, no compiler server or worker survived between builds in any of 32 runs. | Disabled MSBuild node reuse. | Verifier action. |
| <a name="e1-m-10"></a> **E1-M-10** | A process’s working directory did not identify its build. Its `HOME` did. | Identified each build by its `HOME`. | Verifier action. Use `HOME` to distinguish the builds. |
| <a name="e1-m-11"></a> **E1-M-11** | The first stage 2 measurement omitted the frontend export that the release workflow copies into `wwwroot/`. | Repeated the measurement with the export in place. | Fixed in the measurement procedure. |
| <a name="e1-m-12"></a> **E1-M-12** | Even with `--no-cache`, BuildKit reused a cached `WORKDIR` step. Using one builder could hide a timestamp difference. | None needed. | No fix needed. |
| <a name="e1-m-13"></a> **E1-M-13** | The `aslr` setting left address space layout randomisation on in both builds. Only `kernel` turned it off. | Read the `aslr` results as no-ops. | Limitation we report. |
| <a name="e1-m-14"></a> **E1-M-14** | The `kernel` setting changed both the reported kernel version and address space layout randomisation. | None needed. | No fix needed. |
| <a name="e1-m-15"></a> **E1-M-15** | Two settings also changed other variables. `build_path` moved `HOME`, and `user_group` replaced `PATH`. | None needed. | No fix needed. |
| <a name="e1-m-16"></a> **E1-M-16** | Builds inherited the entire environment of the shell that started `reprotest`, including 105 variables in our case. | Start `reprotest` under `env -i`. | Verifier action. |
| <a name="e1-m-17"></a> **E1-M-17** | Other language variables from the calling shell still applied under the fixed `reprotest` setting. Only `LC_ALL`, `LC_MESSAGES` and `LANG` determined the language used by the internationalisation library. | None needed. | No fix needed. |
| <a name="e1-m-18"></a> **E1-M-18** | After a passing run, `reprotest` replaced the second build’s output with a link to the first. | Compare hashes across runs as well as checking the verdicts. | No fix needed. |
| <a name="e1-m-19"></a> **E1-M-19** | If the newest source file was over 398 days old, `reprotest` silently skipped the clock shift for `time`. | Checked every log for the clock shift. | Verifier action. |
| <a name="e1-m-20"></a> **E1-M-20** | The `reprotest` log listed the settings and values varied in each build. Its exit code distinguished a match, a difference and a failed run. | None needed. | No fix needed. |
| <a name="e1-m-21"></a> **E1-M-21** | Between `reprotest` builds, npm, pip, gem, Maven and Go left no processes running. The .NET compiler server stayed alive. | For the compiler server change, see [E1-M-07](#e1-m-07). | No fix needed for the other tools. |
| <a name="e1-m-22"></a> **E1-M-22** | The `time` setting could not shift the clock for a statically linked program. Go’s compiler read the real time. | None. Shifting this clock needs another method, such as a virtual machine with a shifted clock. | Limitation we report. |
| <a name="e1-m-23"></a> **E1-M-23** | Under the `time` setting, pip failed the transport security check when connecting to the Python Package Index. The build failed. | None. The build would need no network access or a smaller shift. | Limitation we report. |
| <a name="e1-m-24"></a> **E1-M-24** | Maven continued using the real `~/.m2` folder even when `reprotest` changed `HOME`. | None needed. | No fix needed. |
