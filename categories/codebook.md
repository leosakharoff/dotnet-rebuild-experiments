# Codebook for Experiments 1 and 2

Each finding gets up to two categories. **A** says what caused an output difference. **B** records what information or input was missing when rebuilding against a reference. The categories draw on Bajaj et al. 2024 (16 root causes, pp. 24–25), Lamb & Zacchiroli 2021 (pp. 3–5) and Solarin et al. 2026 (Table II, p. 8).

## A. What caused the difference?

| Category | Use when | Example | Literature |
| --- | --- | --- | --- |
| **Build timestamp** | The build clock affects a value in the output, such as a version, copyright year, file timestamp, or signature timestamp. | E1-S5-05; Azure SDK date in version | Bajaj Build Timestamp; Lamb & Zacchiroli |
| **Build path** | The directory from which the build runs affects the output. | E1-S1-06; Quartz path hash | Bajaj Build Path |
| **Locale** | The language or region setting affects the output, for example by changing how names are sorted. | E1-S2-11 | Bajaj Locale |
| **Randomness** | A random value or the completion order of parallel work affects the output. This can happen across builds in the same environment. | E1-S3-01, E1-S3-10 | Bajaj Randomness, Build ID |
| **Filesystem ordering** | The output depends on the order in which the file system lists files. | none in RQ1; 2a's `fileordering` axis | Bajaj Filesystem Ordering |
| **Archive metadata and file permissions** | The file contents match, but metadata such as permissions, ownership, or archive fields other than timestamps differs. | E1-S4-01 | Bajaj Archive Metadata, File Permission |
| **Build tool version** | A different compiler, runtime, or tool affects the output, even if it reports the same version. | E1-S1-02, E1-S1-03; SharpZipLib targeting pack | Solarin RC01 |
| **Package dependency** | A dependency or file selected by name or version supplies different bytes in another build. | E1-S2-07, E1-S6-05 | Bajaj Package Dependency |
| **CI/CD modification** | The publisher’s pipeline changes the output through an additional step or input, such as a generated attribute, a version derived from Git, or a signing key. | Bogus, MediatR.Contracts | Solarin RC02, RC03 |

## B. What was missing for the rebuild?

For comparisons against a separately produced reference, such as a CI artifact, a build from another machine, or a published package, record what the rebuilder lacked.

| Category | Use when |
| --- | --- |
| **Environment** | The record of which toolchain or dependency versions were used was missing. |
| **Source state** | The repository, commit, or other Git metadata needed to recover the source state was missing. |
| **Build process** | A build step or input was missing, such as a CI step, a flag, a key, or a property such as `OfficialBuildId`. |
| **Nothing missing** | The release recorded enough to reconstruct the build. |
| **Not a rebuild** | The comparison used two builds of our own, as in the RQ1 loop and 2a. |

## Findings that are not causes

Keep these findings because they record what was corrected, tested, or learned about the method. Leave A blank.

- **Setup fault** marks a fault in the project or workflow setup that we found and corrected, such as RQ1’s E1-S2-03 and E1-S2-08.
- **No difference found** records a variation that changed no bytes.
- **Measurement** records something that affected how we measured or interpreted a result, such as `libfaketime` under npm in 2a.

## Coding rules

1. Trace the differing value back to the step that set it. If a ZIP entry stores a date taken from the compiler’s clock, assign **Build timestamp**. The ZIP preserves the value the compiler supplied.
2. Assign **Build timestamp** to a timestamp difference wherever it appears, including in an archive or a signature.
3. If two codes describe the same chain of events, assign the one that captures the earliest cause and note the other. Arcade’s versioning gets A = **Build timestamp** because it falls back to the date, and B = **Build process** because `OfficialBuildId` was missing.
4. Assign B = **Not a rebuild** whenever the comparison is between two builds of our own.
5. If no code fits, enter **Unknown** and add a note explaining why.

## Counting and review

In RQ1, record one row per finding. In RQ2, record one row per cause type, with counts of affected packages and repositories. Report the two sets of counts side by side, never added together, following Bajaj’s practice of reporting issues and packages separately.

Claude proposes codes for every finding. Peter independently codes about 20 entries drawn from RQ1, 2a, and 2b, including borderline cases, before seeing Claude’s codes. Report how often the codes agreed, where they differed, and that the sample was Peter’s independent check of AI coding.
