# Experiment 1 findings, by stage

**View:** by stage · [by cause category](by-category.md)

**93** findings: **47** causes of difference, **21** checks with no difference, **25** about the method. **5** are still open.

Ids are the rows of `notes/findings-table.md` in Speciale2026. Stage 5 groups the release's other outputs, which the findings table files under stages 2 and 4. Stage 6 holds the images, which the findings table numbers 5. Hashes made before the move to SDK 10 (12 October 2026) do not compare with later ones.

Each id links to the finding in the category view. 🔴 marks a finding that is still open.

## Stage 1: Build

*Our DLLs and PDBs, deps.json, runtimeconfig.json*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 0 of 1610 files differ<br>• Another build path: all 10 compared files differ<br>• Estonian locale: our 4 assemblies differ | • Every shipped file identical on every axis<br>• 2 development files still hold the path; they do not ship |

**Findings:** [W3](by-category.md#w3) · [W4](by-category.md#w4) · [W5](by-category.md#w5) · [W6](by-category.md#w6) · [W7](by-category.md#w7) · [W26](by-category.md#w26) · [W49](by-category.md#w49) · [W8](by-category.md#w8) 🔴 · [W9](by-category.md#w9) 🔴

## Stage 2: Publish

*The release folder: our assemblies, packages, the runtime*

| Before the fixes | After the fixes |
| --- | --- |
| • Extra and wrong files: a stray lock file, Windows DLLs, libraries listed as 1.0.0<br>• Estonian locale: 10 of 1237 files<br>• SDK 10: 1 file dated with the build time | • 0 of 2121 files differ on SDK 10<br>• 0 of 2227 with the frontend in place (SDK 9)<br>• File modes follow the umask; stage 4 sets them |

**Findings:** [W18](by-category.md#w18) · [W23](by-category.md#w23) · [W24](by-category.md#w24) · [W26](by-category.md#w26) · [W33](by-category.md#w33) · [W50](by-category.md#w50) · [W45](by-category.md#w45) · [W30](by-category.md#w30) 🔴

## Stage 3: Frontend

*npm ci and next build: the static export*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 110 of 998 files (random build ID)<br>• 1 build in 4: 4 files (CSS order)<br>• 26 builds: two outputs, 109 of 990 files (page order)<br>• About 1 build in 50: 5 files (chunk ids) | • 0 files differ within one commit<br>• Two open points do not change the bytes of one commit |

**Findings:** [W37](by-category.md#w37) · [W43](by-category.md#w43) · [W47](by-category.md#w47) · [W51](by-category.md#w51) · [W39](by-category.md#w39) · [W40](by-category.md#w40) · [W41](by-category.md#w41) · [W44](by-category.md#w44) 🔴 · [W46](by-category.md#w46) 🔴

## Stage 4: Zip

*The release zips*

| Before the fixes | After the fixes |
| --- | --- |
| • Different in every build, as CI packs them<br>• Times in 1237 of 1847 entries; 140 entries in another order<br>• Under all axes also modes and owner | • Identical in 4 builds with normalised packing |

**Findings:** [W48](by-category.md#w48) · [W30](by-category.md#w30) 🔴

## Stage 5: The release

*Migrator, SQL script, checksum file, Windows release, signing*

| Before the fixes | After the fixes |
| --- | --- |
| • Migrator: 93 of 827,679,078 bytes<br>• Checksum file: line order follows the locale<br>• Signing: 177 files and both zips differ | • Migrator, SQL script and Windows release (2132 files) identical<br>• Checksum file fixed with LC_ALL=C<br>• Signed files identical after pasting the release's signatures |

**Findings:** [W52](by-category.md#w52) · [W53](by-category.md#w53) · [W54](by-category.md#w54) · [W61](by-category.md#w61) · [W55](by-category.md#w55) · [W63](by-category.md#w63) · [W66](by-category.md#w66) · [W59](by-category.md#w59) · [W64](by-category.md#w64) · [W69](by-category.md#w69)

## Stage 6: Container

*The OCI images, an extra*

| Before the fixes | After the fixes |
| --- | --- |
| • WebAPI and job worker: times only, 123 of 1408 file entries<br>• MCP images: caches written during the build<br>• Image tags: different in every build | • The same image manifest in two builds<br>• Compare the manifest, not the tag |

**Findings:** [W56](by-category.md#w56) · [W60](by-category.md#w60) · [W62](by-category.md#w62) · [W65](by-category.md#w65) · [W67](by-category.md#w67) · [W68](by-category.md#w68)

## Across machines

*The same commit on GitHub's runner, our Linux laptop and a Mac*

| Measured | Result |
| --- | --- |
| • Two compilers both called 9.0.120 gave different DLLs<br>• GitHub against our laptop: our assemblies differ by the runtime patch the compiler ran on | • Identical with the global.json SDK installed alone<br>• macOS on arm64 against GitHub's Linux: nothing differs<br>• The shared droplet was too small to compile WS.PEMS |

**Findings:** [E2](by-category.md#e2) · [E3](by-category.md#e3) · [W58](by-category.md#w58) · [W71](by-category.md#w71) · [W14](by-category.md#w14) 🔴
