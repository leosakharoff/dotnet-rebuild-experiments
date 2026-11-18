# Commits

Every commit on the WS.Phoenix branch `thesis/reproducible-builds`, where
the fixes were made, oldest first. Give a commit to make-lab.sh:

```bash
shared/make-lab.sh 2cd85fd01
```

The measured column marks the two commits each stage is compared on:
before its fixes and after them. A before is the last commit before the
stage's first fix; stage 2 is the exception, see below. Stage 3 was first
measured on its before, `4e5237a33`, on 6 October, and stage 6 on its
before, `100e39127`, on 13 October. When you measure another commit,
mark it here.

The fixes column says which stage's output a commit changes, read from its
subject and the files it changes:
- a stage, from 1-build to 6-images;
- toolchain: the SDK, Node or the runners that every stage builds with;
- check: a CI check that changes no output;
- empty: docs, tests, developer tools and the two merges from main.

The fixes came in the order the findings were made, so from `5031c5afa`
on, the stages 3 to 6 are mixed. A stage's before only has to lack that
stage's own fixes: a fix to the zips or the images does not change the
frontend's input.

Each build.sh is the release job's commands at the stage's after commit,
with every fix. The workflow changed over time, so a build.sh does not
fit every commit, and the befores of stages 2 to 6 do not run with it:
2-publish always pins the locale, 3-frontend needs the `.nvmrc`, and
stages 4 and 5 need `scripts/pack-release-zip.sh`. The befores were
measured with the commands of their time.

Stage 2's before is not stage 1's after: 2-publish/build.sh stops on
`e6e924230` with NETSDK1047. `2570034bd` is the last commit before the
locale pin (E1-S2-11). The fixes between them, E1-S2-03, E1-S2-08 and E1-S2-09, change what
the release ships, which reprotest does not see.

The list is first-parent, so it leaves out the commits the two merges
brought in from main. It came from:

```bash
git log --first-parent --reverse --date=short --format='%h %ad %s' d850ccf86^..2cd85fd01
```

One commit is not on the branch: `b9c0700df`, "Use invariant globalization
in the Windows release job" (5 October 2026), on
`thesis/reproducible-builds-windows`. It starts from `4e5237a33` and was
never merged.

| Commit | Measured | Fixes | Date | Subject |
| --- | --- | --- | --- | --- |
| `d850ccf86` |  |  | 2026-09-15 | Add dependency graph generator and its output |
| `6b7a3254d` | 1-build before | toolchain | 2026-09-15 | Pin SDK to 9.0.120, disable roll-forward |
| `ed249cd44` |  | 1-build | 2026-09-15 | Enable deterministic source paths for all projects |
| `4a6551b45` |  | 1-build | 2026-09-15 | Anchor PathMap to the repository root explicitly |
| `e6e924230` | 1-build after | 1-build | 2026-09-15 | Remove unused Razor pages left from the project template |
| `b0a218239` |  | 2-publish | 2026-09-23 | Remove empty npm lock file from the WebAPI project |
| `84d73a2f6` |  | 2-publish | 2026-09-23 | Lock NuGet dependencies with packages.lock.json |
| `d0a817c93` |  | 2-publish | 2026-09-23 | Set RuntimeIdentifiers on the two programs only |
| `2570034bd` | 2-publish before | 2-publish | 2026-09-23 | Restore with the release version before publishing |
| `4e5237a33` | 2-publish after, 3-frontend before | 2-publish | 2026-09-24 | Pin the build locale in the Linux release jobs |
| `5031c5afa` |  | 3-frontend | 2026-10-07 | Read one APP_VERSION in every build |
| `631294806` |  | toolchain | 2026-10-07 | Pin the frontend's Node to 20.20.2 in one file |
| `eed6c2402` |  | 3-frontend | 2026-10-07 | Import all third-party CSS in _app |
| `a16eb506f` |  | 3-frontend | 2026-10-07 | Keep react-day-picker's CSS off the Tremor calendar |
| `e19ca4146` |  | 3-frontend | 2026-10-12 | Fill in resolved and integrity for 391 frontend lock entries |
| `a16f9a91d` | 4-zip before | 3-frontend | 2026-10-12 | Sort the client's webpack entries by name |
| `06cb5397e` |  | 4-zip | 2026-10-12 | Pack the Linux release zips reproducibly |
| `b744ab91d` |  |  | 2026-10-12 | Find the repository from the test output, not source paths |
| `deaf30900` |  | toolchain | 2026-10-12 | Install the SDK from global.json in every workflow |
| `332752b91` |  | toolchain | 2026-10-12 | Move to .NET 10 with one pinned toolchain |
| `e6ce35498` |  | 2-publish | 2026-10-12 | Turn off static asset compression in the WebAPI |
| `61870435e` |  | 3-frontend | 2026-10-12 | Sort webpack's modules and links before chunking |
| `acbea21c7` |  | 3-frontend | 2026-10-12 | Sort webpack's links with a unique key and fresh caches |
| `833e173aa` | 5-release before | check | 2026-10-12 | Keep the SDK pin and the .NET images in step |
| `21360193c` |  | 5-release | 2026-10-13 | Restore before dotnet ef on a fresh checkout |
| `d15008976` |  | 5-release | 2026-10-13 | Give DatabaseContext one design-time factory |
| `cd36f2419` |  | 5-release | 2026-10-13 | Build the database migrator from src/DbMigrator |
| `82ea130ac` |  | check | 2026-10-13 | Run the migrator against PostgreSQL in the release |
| `459de87e6` |  |  | 2026-10-13 | Merge main into thesis/reproducible-builds |
| `bc0c52f60` |  | 3-frontend | 2026-10-13 | Fill the frontend lock's missing hashes again |
| `805275c4b` |  | 5-release | 2026-10-13 | Keep design-time factories in the startup projects |
| `79cb67a7a` |  | check | 2026-10-13 | Check the release tag and smoke-test both migrator paths |
| `5ec085acb` |  | 4-zip | 2026-10-13 | Pack all release zips with one script |
| `3e4fbc48b` |  |  | 2026-10-13 | Name the solution in the Makefile's dotnet calls |
| `d547d1920` |  |  | 2026-10-13 | Stop the migration scripts when a command fails |
| `a853043fc` |  |  | 2026-10-13 | Restore before dotnet ef in the Makefile and scripts |
| `0b52e1158` |  | 5-release | 2026-10-13 | Keep the host's runtime out of the migrator's restore |
| `100e39127` | 6-images before |  | 2026-10-13 | Name the solution, and restore first, in the docs |
| `fa60ea974` |  | 6-images | 2026-10-13 | Date the release images by the commit |
| `62ac787a4` |  | toolchain | 2026-10-14 | Install exactly the global.json SDK in CI |
| `66bf84581` |  | 5-release | 2026-10-14 | Check that each signed release can be rebuilt |
| `97038d737` |  | 5-release | 2026-10-14 | Fix the locale before SHA256SUMS expands its globs |
| `56f8f5838` |  | 6-images | 2026-10-14 | Build the manual images from the commit, dated by it |
| `3c3759380` |  | 6-images | 2026-10-14 | Pin the MCP images, and drop what records the build |
| `69836c340` |  | 6-images | 2026-10-14 | Let the BuildKit check read buildx to the end |
| `5940c2ecb` |  | 5-release | 2026-10-14 | Check a signed release without a second copy |
| `019c7b49a` |  | 5-release | 2026-10-14 | Take the release's own frontend export on Windows |
| `4b1c71b9a` |  | toolchain | 2026-10-14 | Keep SDK archives only on self-hosted runners |
| `be5fc56e7` |  | check | 2026-10-14 | Validate the backend when the SDK setup changes |
| `28371c9e4` |  | 5-release | 2026-10-14 | Name every SHA256SUMS line by its asset name |
| `f073bf5e4` |  | 6-images | 2026-10-20 | Pin the MCP images' Debian packages and canvas binary |
| `82d35f9df` |  | 6-images | 2026-10-20 | Fail the MCP image builds on a missing index or prebuilt |
| `56e4b4820` |  | 6-images | 2026-10-20 | Pin the BuildKit the release builds its images with |
| `1b9659554` |  |  | 2026-10-21 | Merge main into thesis/reproducible-builds |
| `443f6c756` |  |  | 2026-10-21 | Regenerate the dependency page for .NET 10 |
| `1e28a186b` |  | check | 2026-10-21 | Let Docker pick the migrator smoke test's port |
| `9a2a9ed45` |  | 6-images | 2026-10-21 | Pin the MCP images' Debian release files by hash |
| `672d04a51` |  | 6-images | 2026-10-21 | Pin the scanner that writes the images' SBOMs |
| `cd3f93c1a` |  | toolchain | 2026-10-21 | Pin GitHub's own actions by commit |
| `b4a713168` |  | toolchain | 2026-10-21 | Name the release's GitHub runners by image |
| `7c0089c53` |  | toolchain | 2026-10-21 | Install the SDK from hashes committed beside global.json |
| `12cb488e3` |  | check | 2026-10-21 | Check the NuGet packages that no lock file pins |
| `456504fa2` |  | 3-frontend | 2026-10-21 | Install the frontend's Node by hash, its packages without scripts |
| `9624cd530` |  |  | 2026-10-21 | Give the dev container the SDK that global.json names |
| `56f99a68b` |  | 6-images | 2026-10-21 | Build the images by hand with the release's BuildKit |
| `add59324e` |  | 5-release | 2026-10-21 | Install the signing image's packages from Ubuntu's snapshot |
| `b3e0134ff` |  | toolchain | 2026-10-21 | Restore the release's .NET tools into its own package folder |
| `2cd85fd01` | 3-frontend, 4-zip, 5-release and 6-images after | toolchain | 2026-10-21 | Unpack the SDK on a Python without tarfile's filter |
