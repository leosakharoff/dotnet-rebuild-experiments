# Experiment 1: the stages before and after the fixes

What each stage looked like before and after the fixes, and the findings behind it. Every finding is listed once, with its code and status, in [findings.md](findings.md). Stage 5 groups the release's other outputs, which the findings table in Speciale2026 files under stages 2 and 4; stage 6 holds the images, which it numbers 5. Hashes made before the move to SDK 10 (12 October 2026) do not compare with later ones.

🔴 marks a finding that is still open.

## Stage 1: Build

*Our DLLs and PDBs, deps.json, runtimeconfig.json*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 0 of 1610 files differ<br>• Another build path: all 10 compared files differ<br>• Estonian locale: our 4 assemblies differ | • Every shipped file identical on every axis<br>• 2 development files still hold the path; they do not ship |

**Findings:** [E1-S1-09](findings.md#e1-s1-09) · [E1-S1-10](findings.md#e1-s1-10) · [E1-S1-11](findings.md#e1-s1-11) · [E1-S1-12](findings.md#e1-s1-12) · [E1-S1-13](findings.md#e1-s1-13) · [E1-S2-11](findings.md#e1-s2-11) · [E1-S1-21](findings.md#e1-s1-21) · [E1-S1-14](findings.md#e1-s1-14) 🔴 · [E1-S1-15](findings.md#e1-s1-15) 🔴

## Stage 2: Publish

*The release folder: our assemblies, packages, the runtime*

| Before the fixes | After the fixes |
| --- | --- |
| • Extra and wrong files: a stray lock file, Windows DLLs, libraries listed as 1.0.0<br>• Estonian locale: 10 of 1237 files<br>• SDK 10: 1 file dated with the build time | • 0 of 2121 files differ on SDK 10<br>• 0 of 2227 with the frontend in place (SDK 9)<br>• File modes follow the umask; stage 4 sets them |

**Findings:** [E1-S2-03](findings.md#e1-s2-03) · [E1-S2-08](findings.md#e1-s2-08) · [E1-S2-09](findings.md#e1-s2-09) · [E1-S2-11](findings.md#e1-s2-11) · [E1-S2-16](findings.md#e1-s2-16) · [E1-S2-18](findings.md#e1-s2-18) · [E1-S2-17](findings.md#e1-s2-17) · [E1-S2-13](findings.md#e1-s2-13) 🔴

## Stage 3: Frontend

*npm ci and next build: the static export*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 110 of 998 files (random build ID)<br>• 1 build in 4: 4 files (CSS order)<br>• 26 builds: two outputs, 109 of 990 files (page order)<br>• About 1 build in 50: 5 files (chunk ids) | • 0 files differ within one commit<br>• Two open points do not change the bytes of one commit |

**Findings:** [E1-S3-01](findings.md#e1-s3-01) · [E1-S3-06](findings.md#e1-s3-06) · [E1-S3-09](findings.md#e1-s3-09) · [E1-S3-10](findings.md#e1-s3-10) · [E1-S3-03](findings.md#e1-s3-03) · [E1-S3-04](findings.md#e1-s3-04) · [E1-S3-05](findings.md#e1-s3-05) · [E1-S3-07](findings.md#e1-s3-07) 🔴 · [E1-S3-08](findings.md#e1-s3-08) 🔴

## Stage 4: Zip

*The release zips*

| Before the fixes | After the fixes |
| --- | --- |
| • Different in every build, as CI packs them<br>• Times in 1237 of 1847 entries; 140 entries in another order<br>• Under all axes also modes and owner | • Identical in 4 builds with normalised packing |

**Findings:** [E1-S4-01](findings.md#e1-s4-01) · [E1-S2-13](findings.md#e1-s2-13) 🔴

## Stage 5: The release

*Migrator, SQL script, checksum file, Windows release, signing*

| Before the fixes | After the fixes |
| --- | --- |
| • Migrator: 93 of 827,679,078 bytes<br>• Checksum file: line order follows the locale<br>• Signing: 177 files and both zips differ | • Migrator, SQL script and Windows release (2132 files) identical<br>• Checksum file fixed with LC_ALL=C<br>• Signed files identical after pasting the release's signatures |

**Findings:** [E1-S5-01](findings.md#e1-s5-01) · [E1-S5-02](findings.md#e1-s5-02) · [E1-S5-03](findings.md#e1-s5-03) · [E1-S5-06](findings.md#e1-s5-06) · [E1-S5-04](findings.md#e1-s5-04) · [E1-S5-07](findings.md#e1-s5-07) · [E1-S5-09](findings.md#e1-s5-09) · [E1-S5-05](findings.md#e1-s5-05) · [E1-S5-08](findings.md#e1-s5-08) · [E1-S5-10](findings.md#e1-s5-10)

## Stage 6: Container

*The OCI images, an extra*

| Before the fixes | After the fixes |
| --- | --- |
| • WebAPI and job worker: times only, 123 of 1408 file entries<br>• MCP images: caches written during the build<br>• Image tags: different in every build | • The same image manifest in two builds<br>• Compare the manifest, not the tag |

**Findings:** [E1-S6-01](findings.md#e1-s6-01) · [E1-S6-02](findings.md#e1-s6-02) · [E1-S6-03](findings.md#e1-s6-03) · [E1-S6-04](findings.md#e1-s6-04) · [E1-S6-05](findings.md#e1-s6-05) · [E1-S6-06](findings.md#e1-s6-06)

## Across machines

*The same commit on GitHub's runner, our Linux laptop and a Mac*

| Measured | Result |
| --- | --- |
| • Two compilers both called 9.0.120 gave different DLLs<br>• GitHub against our laptop: our assemblies differ by the runtime patch the compiler ran on | • Identical with the global.json SDK installed alone<br>• macOS on arm64 against GitHub's Linux: nothing differs<br>• The shared droplet was too small to compile WS.PEMS |

**Findings:** [E1-S1-02](findings.md#e1-s1-02) · [E1-S1-03](findings.md#e1-s1-03) · [E1-S2-19](findings.md#e1-s2-19) · [E1-S2-20](findings.md#e1-s2-20) · [E1-M-06](findings.md#e1-m-06) 🔴
