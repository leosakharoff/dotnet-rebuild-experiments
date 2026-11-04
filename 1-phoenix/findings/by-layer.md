# Experiment 1 findings, by layer

**View:** by layer · [by cause family](by-family.md)

**93** findings: **47** causes of difference, **21** checks with no difference, **25** about the method. **5** are still open.

Ids are the rows of `notes/findings-table.md` in Speciale2026. Layer 6 groups the release's other outputs, which the findings table files under layers 2 and 4. Hashes made before the move to SDK 10 (12 October 2026) do not compare with later ones.

Each id links to the finding in the family view. 🔴 marks a finding that is still open.

## Layer 1: Build

*Our DLLs and PDBs, deps.json, runtimeconfig.json*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 0 of 1610 files differ<br>• Another build path: all 10 compared files differ<br>• Estonian locale: our 4 assemblies differ | • Every shipped file identical on every axis<br>• 2 development files still hold the path; they do not ship |

**Findings:** [W3](by-family.md#w3) · [W4](by-family.md#w4) · [W5](by-family.md#w5) · [W6](by-family.md#w6) · [W7](by-family.md#w7) · [W26](by-family.md#w26) · [W49](by-family.md#w49) · [W8](by-family.md#w8) 🔴 · [W9](by-family.md#w9) 🔴

## Layer 2: Publish

*The release folder: our assemblies, packages, the runtime*

| Before the fixes | After the fixes |
| --- | --- |
| • Extra and wrong files: a stray lock file, Windows DLLs, libraries listed as 1.0.0<br>• Estonian locale: 10 of 1237 files<br>• SDK 10: 1 file dated with the build time | • 0 of 2121 files differ on SDK 10<br>• 0 of 2227 with the frontend in place (SDK 9)<br>• File modes follow the umask; layer 4 sets them |

**Findings:** [W18](by-family.md#w18) · [W23](by-family.md#w23) · [W24](by-family.md#w24) · [W26](by-family.md#w26) · [W33](by-family.md#w33) · [W50](by-family.md#w50) · [W45](by-family.md#w45) · [W30](by-family.md#w30) 🔴

## Layer 3: Frontend

*npm ci and next build: the static export*

| Before the fixes | After the fixes |
| --- | --- |
| • Same path: 110 of 998 files (random build ID)<br>• 1 build in 4: 4 files (CSS order)<br>• 26 builds: two outputs, 109 of 990 files (page order)<br>• About 1 build in 50: 5 files (chunk ids) | • 0 files differ within one commit<br>• Two open points do not change the bytes of one commit |

**Findings:** [W37](by-family.md#w37) · [W43](by-family.md#w43) · [W47](by-family.md#w47) · [W51](by-family.md#w51) · [W39](by-family.md#w39) · [W40](by-family.md#w40) · [W41](by-family.md#w41) · [W44](by-family.md#w44) 🔴 · [W46](by-family.md#w46) 🔴

## Layer 4: Zip

*The release zips*

| Before the fixes | After the fixes |
| --- | --- |
| • Different in every build, as CI packs them<br>• Times in 1237 of 1847 entries; 140 entries in another order<br>• Under all axes also modes and owner | • Identical in 4 builds with normalised packing |

**Findings:** [W48](by-family.md#w48) · [W30](by-family.md#w30) 🔴

## Layer 5: Container

*The OCI images*

| Before the fixes | After the fixes |
| --- | --- |
| • WebAPI and job worker: times only, 123 of 1408 file entries<br>• MCP images: caches written during the build<br>• Image tags: different in every build | • The same image manifest in two builds<br>• Compare the manifest, not the tag |

**Findings:** [W56](by-family.md#w56) · [W60](by-family.md#w60) · [W62](by-family.md#w62) · [W65](by-family.md#w65) · [W67](by-family.md#w67) · [W68](by-family.md#w68)

## Layer 6: Other outputs

*Migrator, SQL script, checksum file, Windows release, signing*

| Before the fixes | After the fixes |
| --- | --- |
| • Migrator: 93 of 827,679,078 bytes<br>• Checksum file: line order follows the locale<br>• Signing: 177 files and both zips differ | • Migrator, SQL script and Windows release (2132 files) identical<br>• Checksum file fixed with LC_ALL=C<br>• Signed files identical after pasting the release's signatures |

**Findings:** [W52](by-family.md#w52) · [W53](by-family.md#w53) · [W54](by-family.md#w54) · [W61](by-family.md#w61) · [W55](by-family.md#w55) · [W63](by-family.md#w63) · [W66](by-family.md#w66) · [W59](by-family.md#w59) · [W64](by-family.md#w64) · [W69](by-family.md#w69)

## Across machines

*The same commit on GitHub's runner, our Linux laptop and a Mac*

| Measured | Result |
| --- | --- |
| • Two compilers both called 9.0.120 gave different DLLs<br>• GitHub against our laptop: our assemblies differ by the runtime patch the compiler ran on | • Identical with the global.json SDK installed alone<br>• macOS on arm64 against GitHub's Linux: nothing differs<br>• The shared droplet was too small to compile Phoenix |

**Findings:** [E2](by-family.md#e2) · [E3](by-family.md#e3) · [W58](by-family.md#w58) · [W71](by-family.md#w71) · [W14](by-family.md#w14) 🔴
