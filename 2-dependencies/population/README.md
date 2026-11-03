# Population: the packages Phoenix ships, and what each declares

Both parts of experiment 2 measure packages from this list. This folder
holds the list, one row of facts per package, and the script that read
them. The reading is a census in the plain sense: every package is opened
once and the same facts are noted for each; nothing is built or judged.

## The 341 packages

The self-contained `linux-x64` publish of Phoenix's three programs
(WebAPI, BackgroundJobExecutor, DbMigrator) ships 341 package versions:
337 from the programs' lock files (85 direct, 252 transitive), 3 runtime
and host packs the SDK downloads for the RID, and 1 tool whose output
ships (dotnet-ef). They name 104 distinct repository-and-commit pairs.
`results/shipped-packages.txt` is the list, one per line.

Another 98 package versions in the repository are not in it, each with
its reason recorded: a library's own lock file, test projects, other
platforms, local tools whose output does not ship. The frontend's npm
packages and the .NET SDK itself are out of scope.

## What each package declares

After one locked restore of the three programs, `scripts/census.py` opens
every shipped package in the NuGet cache, with no network and no build,
and reads what the package says about its own origin: the repository and
commit in its `.nuspec`; whether the shipped files are IL or native;
where the PDB is (embedded, in the package, only referenced, none); the
compiler the PDB records; the Reproducible and PdbChecksum debug entries;
Source Link; Authenticode and strong-name signatures. One row per package
in `results/packages.tsv`, and one class:

| class | meaning | packages |
|---|---|---|
| N0 | ships no files (meta or build-time only) | 29 |
| N1 | native code only | 9 |
| C1a | no repository in the `.nuspec` | 9 |
| C1b | a repository, no commit | 13 |
| C2a | no PDB at all | 45 |
| C2b | PDB referenced, not in the package (maybe on a symbol server) | 181 |
| C2c | PDB in the package, no compiler record | 2 |
| R | commit and compiler record both declared | 53 |

Read on `mac`, 13 October 2026, from Phoenix at `79cb67a7` with SDK
10.0.401; its `csc.dll` hash is in the run's `environment.txt`.

## What each part takes

The last two columns of `packages.tsv`, `in_2a` and `in_2b`, say which
rows each part measures. Each part's README says why.

- **2a** needs a repository, a commit and one project file with the
  shipped assembly's name, and derives that itself with its `population.py`
  from `shipped-packages.txt`: 224 of the 341. The 117 that stop: 75 ship
  no assembly of the package's name under `lib/` (27 ship no managed code,
  45 are Humanizer's satellite packages with one `Humanizer.resources.dll`
  per culture, 2 ship theirs under `runtimes/` and 1 under `tools/`), 20
  name no commit, 11 no repository, 8 could not be fetched, 3 have no
  single project with that name.
- **2b** needs a commit and a compiler record, because it derives the SDK
  from the compiler the release names instead of holding one fixed: 198
  of the 303 that ship managed code. The 105 that stop: 22 name no source
  (C1a, C1b) and 83 name no compiler.
- 185 package versions are in both.

## Data and scripts

```
population/
  README.md
  scripts/
    census.py                 reads every shipped package: repository, commit, PDB, compiler, signatures
  results/
    shipped-packages.txt      the 341 packages Phoenix ships, one per line; 2a's only input
    packages.tsv              one row per package: the census facts, its class, and in_2a / in_2b
```

- `results/shipped-packages.txt`: the 341, the only input of 2a's
  `population.py`.
- `results/packages.tsv`: the census row of every package plus `in_2a`
  and `in_2b`; assembled from the run's `census.csv` and the two parts'
  `population.tsv`.
- `scripts/census.py`: the script as it ran on 13 October, not trimmed.
  It needs Phoenix's repository and a restore, which is why its output is
  here and the run is not repeatable from this repository.
- The run itself is in the working repository
  [Speciale2026](https://github.com/peterjuulm/Speciale2026) at `f127442`,
  `dependencies/data/2026-10-13-dependency-census/mac/`: `census.md`,
  `left-out.md`, `census.files.csv` (one row per shipped DLL with its PDB
  identity), `environment.txt`, `kommando.txt`. What the repositories
  declare about their own build environment (`global.json`, CI) is the
  note `dependencies/notes/2026-10-13-declared-env.md`; the symbol-server
  lookup for the C2b packages is `dependencies/notes/2026-10-13-symbol-servers.md`.
