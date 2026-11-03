# The two figures

Both figures are drawn in draw.io. Edit the `.drawio` file and export the
`.drawio.png` at scale 2 (`draw.io -x -f png -s 2 -b 10`). The step numbers in
each figure are the numbers in the tables below.

The finding ids (E, W, R) refer to the [findings table](https://github.com/peterjuulm/Speciale2026/blob/main/notes/findings-table.md) in Speciale2026.
The commits are on the WS.Phoenix branch `thesis/reproducible-builds`.

## Figure 1: build, publish and pack

![The steps of dotnet build, publish and pack](build-publish-pack.drawio.png)

Steps 1 to 6 are `dotnet build`. `dotnet publish` and `dotnet pack` each run
steps 2 to 6 first, then their own step. Step 8 is not dotnet: it is the
release workflow. Files read are on the left, and files written are on the
right.

### The files in figure 1

| Step | File | Who makes it | Who reads it | What it holds, and what that means | What it changes in the build |
| --- | --- | --- | --- | --- | --- |
| 1 | `global.json` | The developers, in the repository | hostfxr, when `dotnet` starts | An SDK version and a roll-forward rule for the SDK | Which SDK folder runs every later step, and so which MSBuild, NuGet and csc. Figure 2 shows this step |
| 2 | `*.csproj` | The developers | MSBuild | The project's SDK (for example `Microsoft.NET.Sdk.Web`), the target framework, the package references and project properties | What is built, for which framework, with which packages |
| 2 | `Directory.Build.props` | The developers | MSBuild imports it before each `.csproj` in the folders below it | Properties for every project at once | One place for settings that must be the same everywhere, for example path mapping, lock files and the version |
| 2 | The SDK's `.props` and `.targets` | Microsoft, inside `sdk//` | MSBuild | The build rules: default values for every property, and the targets that do steps 3 to 9 | What each step does. Another SDK version can do a step in another way |
| 2 | Environment variables and `-p:` flags | The shell, the CI job, or the person who types the command | MSBuild | Each environment variable becomes a property with the same name. A `-p:` flag sets a property and wins over the project files | A variable whose name is a build property changes the build, and no file in the repository shows it |
| 3 | `packages.lock.json` | NuGet writes it at restore; the developers commit it | NuGet | For one project: every package, direct and transitive, with its exact version and a content hash | In locked mode, restore fails if the graph or a hash is different. Without the file, a version such as `13.0.1` means "13.0.1 or higher", and the graph can change |
| 3 | `NuGet.config` | The machine's user or administrator; a repository can have one too | NuGet | The package sources (feeds), their credentials and the cache folder | Which server the packages come from. Phoenix has no `NuGet.config`, so each machine's own file decides |
| 3, 6 | `~/.nuget/packages` | NuGet, when it downloads and unpacks a package | NuGet in step 3; MSBuild in steps 5 to 7 | One folder for each package version, with the package's hash in `.nupkg.metadata` | A package that is already here is not downloaded again. Its files are the ones that the build references and copies |
| 3 | `nuget.org` | Package authors upload; nuget.org adds its signature | NuGet, for each package that is not in the cache | The published `.nupkg` files | The source of every package that the machine does not have yet |
| 3, 4 | `obj/project.assets.json` | NuGet, at the end of step 3 | MSBuild, in steps 4 to 7 | The resolved graph: for each package its version, its hash, and its files for each framework and platform | MSBuild takes the reference DLLs and the files to copy from it. The versions in `deps.json` also come from here |
| 2 | Properties in memory | MSBuild, in step 2 | Every later step | The final value of every property and item after all files are read | Nothing is written to disk. To see the values, use `dotnet build -v:diag` or a binary log |
| 4 | `.git` | git | Source Link, a task in the SDK | The current commit and the remote URL | They go into the PDB's source links and into the informational version. Without `.git`, Source Link knows no source root, so path mapping must be set explicitly |
| 4 | `.editorconfig` | The developers | MSBuild gives it to csc | Code-style and analyzer settings | Which warnings and errors the compiler reports. Source generators can also read settings from it |
| 4, 5 | `obj/*.AssemblyInfo.cs` | MSBuild, in step 4 | csc, in step 5 | C# attributes: version, informational version, company, product | The version strings in the DLL come from this generated file, not from a file in the repository |
| 4, 5 | The csc arguments | MSBuild, in step 4 | csc | Every source file, reference DLL, define and option, for example `/pathmap` and `/deterministic` | The compiler knows only these. A property that does not become an argument does not reach the DLL |
| 5 | `*.cs` | The developers | csc | The source code | The program |
| 5 | The targeting pack | Microsoft; installed with the SDK in `packs/` | csc, as reference DLLs | The .NET API: names and signatures, with no code inside | What the code compiles against. The SDK chooses its version |
| 5, 6 | `obj/X.dll`, `obj/X.pdb` | csc | MSBuild copies them in step 6 | The assembly (IL code and metadata), and its symbols: source paths, compiler version, runtime version | The only files that the build makes from the source. Every other file in the output is copied or generated |
| 6 | The apphost pack | Microsoft; in `packs/` for this machine's platform, from nuget.org for other platforms | MSBuild | A template launcher program | MSBuild copies it and writes the DLL's name into the copy, which becomes `bin/X` |
| 6 | `bin/X.dll`, `X.pdb` | MSBuild, by copying from `obj/` | The host, when the program starts | The same bytes as in `obj/` | The program that runs |
| 6 | `bin/X.deps.json` | MSBuild | hostpolicy, when the program starts | Every library that the program needs, with version, hash and file paths | Which DLL the program loads, and from where |
| 6 | `bin/X.runtimeconfig.json` | MSBuild | hostfxr, when the program starts | The runtime and version to start, the roll-forward rule, and runtime switches | Which runtime the program runs on. Figure 2 shows the same mechanism for the SDK's own programs |
| 6 | `bin/X` (the apphost) | MSBuild | The operating system, when you type `./X` | The launcher with this DLL's name | It finds a .NET root and starts the host, so the program starts without `dotnet` |
| 7 | The runtime pack | Microsoft, on nuget.org | MSBuild, only for `--self-contained` | The whole .NET runtime for one platform: coreclr, the JIT, every `System.*.dll` | It is copied into the release, so the release runs without an installed .NET. The SDK chooses its version |
| 7 | `ClientApp/out/` | The frontend build (`npm ci` and `next build`), a separate CI job | MSBuild | The static website | It is copied into `wwwroot/` and shipped with the backend |
| 7 | `*.json` in the project folder | The developers | The Web SDK | Settings files, such as `appsettings.json` | The Web SDK ships every `.json` file there, also a file that is there by accident |
| 7, 8 | `publish/` | MSBuild, in step 7 | The release job | The complete program for one platform | What is zipped, checksummed and put into images |
| 8 | `*.zip`, `SHA256SUMS`, container images | The release job | Users and operators | The release, and a checksum for each file | What is downloaded and installed, and what a rebuild is compared with |
| 9 | Package fields in `*.csproj` | The developers | NuGet's pack task | Package id, version, authors, licence | They go into the `.nuspec` inside the package |
| 9 | `X.nupkg` | NuGet's pack task | nuget.org, and the restore of other projects | A zip with the DLLs and the `.nuspec` | The package that other projects restore. Signatures are added later, by the author and by nuget.org |

### Problems and fixes in figure 1

| Step | What changed the bytes | What fixed it |
| --- | --- | --- |
| 1 | A loose `global.json` let each machine take its newest SDK. The version number does not identify the compiler binary (E2). | `global.json`: 10.0.401 with `rollForward: disable`. CI installs that SDK by hash. (6b7a3254, 332752b9, 7c0089c5) |
| 2 | Settings came from the shell and the machine: the locale, the home folder, the machine's `NuGet.config`. | The build-wide settings are in `Directory.Build.props`. Each one takes effect in a later step. (ed249cd4, 4a6551b4, 84d73a2f, 5031c5af) |
| 3 | Version ranges let the package graph change (W22). A restore without the version gave `deps.json` the version 1.0.0 (W24). The packs are not in any lock file (W21). | Lock files and locked mode in CI (W22). One restore, with the version (W24). The packs are checked against `nuget-downloads.lock.json` (W21). (84d73a2f, 2570034b, 12cb488e) |
| 4 | Without `.git`, only the NuGet cache was mapped, so the build path stayed in the output (W6). The release's builds got the version in different ways, so the zips, the images and the migrator had different version fields (W45). | `PathMap` anchored to the repository root (W6). One `APP_VERSION` for every build (W45). (4a6551b4, 5031c5af) |
| 5 | The build path went into the PDB, the DLL's debug directory and generated type names (W3–W5). The Razor generator wrote absolute paths (W7). Roslyn 4.12 sorted generated types by culture (W26). The compiler server kept the first build's environment (W27). | `PathMap` (W3–W5). Unused Razor pages deleted (W7). `LC_ALL=C.UTF-8`, not necessary on SDK 10 (W26). In the lab: `dotnet build-server shutdown` (W27). (ed249cd4, e6e92423, 4e5237a3) |
| 6 | Two development files hold the absolute path (W8, W9). | No fix is necessary: they are not in the release. |
| 7 | An empty `package-lock.json` was shipped (W18). The Linux release got Windows DLLs (W23). SDK 10 dated compressed assets with the build time (W50). The frontend export had a random build ID and orders from build timing (W37, W43, W47, W51). | The file deleted (W18). `RuntimeIdentifiers` only on the programs (W23). `CompressionEnabled=false` (W50). Frontend: the build ID from `APP_VERSION`, CSS in `_app.tsx`, sorted webpack entries and modules. (b0a21823, d0a817c9, e6ce3549, 5031c5af, eed6c240, a16f9a91, 61870435) |
| 8 | `zip -r` stored file times, modes from the umask and disk order (W48, W30). `SHA256SUMS` followed the locale (W63). Images recorded the build time and caches (W56, W60). Each signature has its own timestamp (W59). | `scripts/pack-release-zip.sh` (W48). `LC_ALL=C` (W63). `SOURCE_DATE_EPOCH` and `rewrite-timestamp` (W56, W60). A rebuild is compared after the release's signatures are copied onto it (W59). (5ec085ac, 97038d73, fa60ea97, 3c337593, 66bf8458) |
| 9 | Phoenix does not pack. Experiment 2 found that older SDKs give `.psmdcp` a random name. | No Phoenix change. |

### The options in the release commands

`dotnet publish ./src/WebAPI/WebAPI.csproj -c Release -o <folder> -r linux-x64 --self-contained true --no-restore /p:SkipSpaBuild=true`

`publish` is the command. `-c` is an option, and `Release` is its value. Each
option sets an MSBuild property, as `-p:Name=Value` does.

| Option | Property | What it changes |
| --- | --- | --- |
| `-c Release` | `Configuration=Release` | `Optimize=true`, the define `RELEASE`, output in `bin/Release/`. The default is `Debug` for `build`, `run` and `test`, and `Release` for `publish` |
| `-o <folder>` | `PublishDir` | Where the output goes. Not the bytes |
| `-r linux-x64` | `RuntimeIdentifier` | The platform: native files, apphost, runtime pack |
| `--self-contained true` | `SelfContained=true` | The runtime pack is copied into the output (step 7) |
| `--no-restore` | — | Skips step 3; uses the restore that ran before |
| `/p:SkipSpaBuild=true` | Phoenix's own | No `npm ci` and `next build`; the frontend job's export is copied in |

Debug is for working with the debugger: no optimization, so breakpoints and
variables behave as in the source. Release is what ships, so CI tests it too.
Debug and Release give different IL, and the PDB records which one was used.

## Figure 2: the SDK's processes and their runtimes

![How one dotnet build starts its processes and chooses their runtimes](sdk-processes.drawio.png)

One `dotnet build`. Steps 1 to 3 choose the dotnet root and the SDK. Steps 4
to 6 are three separate .NET processes. In step 7, each process chooses its
own runtime when it starts. The dashed box is a runtime that was installed
later, as it was on the GitHub runners.

### The files in figure 2

| Step | File | Who makes it | Who reads it | What it holds, and what that means | What it changes in the build |
| --- | --- | --- | --- | --- | --- |
| 1 | `PATH` | The shell profile, the installer, or the CI job | The shell | A list of folders. The shell runs the first `dotnet` that it finds in them | Which dotnet root the build uses. On Peter's Mac, `PATH` finds `/usr/local/share/dotnet` (only SDK 9.0.102) before `~/.dotnet` |
| 1 | `dotnet` (the host) | Each SDK or runtime installer; there is one in each root | The shell starts it | A small native program | It looks only in its own folder, the dotnet root, for everything that follows |
| 1, 2 | `host/fxr//` | Each SDK or runtime installer adds a version | The host | hostfxr, the library that chooses an SDK and runtimes | The host always loads the highest version, also one that a later runtime install brought |
| 2 | `global.json` | The developers | hostfxr. It looks in the current folder and in each parent folder | The SDK version, and the rule for when that version is not installed | Which folder in `sdk/` runs. With `rollForward: disable`, a missing SDK is an error. Nothing downloads it |
| 2, 3 | `sdk//` | Each SDK installer adds one folder | hostfxr chooses one | The CLI, MSBuild, NuGet, Roslyn and the build rules. Each program has its own `runtimeconfig.json` and `deps.json` | The tools for every step in figure 1 |
| 4–6 | Each tool's `*.runtimeconfig.json` | Microsoft, inside the SDK folder | hostfxr, each time one of the tools starts | The runtime version the tool asks for (10.0.12) and its roll-forward rule. Minor and Major both take the newest installed 10.0.x patch | Which runtime each process gets. The rule allows a newer patch, so the answer depends on what is installed |
| 4–6 | Each tool's `*.deps.json` | Microsoft, inside the SDK folder | hostpolicy, when the tool starts | The tool's own DLLs, in the SDK folder | It fixes the tool's own libraries. Only the runtime under the tool is chosen at start |
| 6 | `DOTNET_ROOT` | The CLI sets it for the processes it starts. The shell or the CI job can also set it | Launchers such as `VBCSCompiler` and `bin/X` | The dotnet root to use | Which root's runtimes a launcher uses. It does not change any `runtimeconfig.json` rule |
| 7 | `shared/Microsoft.NETCore.App//` | Each SDK or runtime installer adds a version. Nothing removes old ones | hostfxr chooses one; hostpolicy loads it | A complete runtime: coreclr, the JIT, every `System.*.dll` | The runtime that runs MSBuild and the compiler. csc writes its version into every PDB |
| 7 | `DOTNET_ROLL_FORWARD` | Not set by default. The shell or the CI job can set it | hostfxr, at the start of every .NET program | A roll-forward rule | It replaces the rule in every `runtimeconfig.json`, for every .NET program in that shell |

### Problems and fixes in figure 2

| Step | What can change the runtime | What fixed it |
| --- | --- | --- |
| 1 | Two dotnet roots on one machine. `PATH` decides which one runs. | CI: the setup action puts its own SDK folder first on `PATH` and sets `DOTNET_ROOT` to it. In the lab: the full path to `dotnet`. (62ac787a) |
| 2 | A runtime installed later brings a newer hostfxr. Without an exact pin, hostfxr takes the newest SDK. | `global.json` with `rollForward: disable`. One SDK in its own folder has only its own hostfxr. (6b7a3254, 332752b9) |
| 3 | Nothing. The pinned folder holds exactly the tools of 10.0.401. | — |
| 4–6 | Each process chooses its runtime again in step 7. Processes 5 and 6 can stay alive from an earlier build, with that build's environment (W27). | In the lab: `dotnet build-server shutdown` and `MSBUILDDISABLENODEREUSE=1`, so each build starts its own processes. |
| 7 | On GitHub, `actions/setup-dotnet` installed the newest LTS runtime, 10.0.13, beside SDK 10.0.401, which brings 10.0.12. Every process took 10.0.13. csc wrote 10.0.13 into each PDB, so CI's assemblies differed from local builds (W58). | `scripts/install-dotnet-sdk.py`: the `global.json` SDK, alone, in an empty folder, checked by hash; it also checks that the folder holds only the SDK's own runtime. Then 10.0.12 is the only runtime the rule can choose. (62ac787a, 7c0089c5) |


### Why one SDK alone is enough

Each tool asks for 10.0.12 and takes the newest installed 10.0.x patch. If the root holds only the SDK and the runtime that came with it, the newest 10.0.x is 10.0.12, so the choice cannot drift. The condition is "one SDK and no other runtime in the root", not only "one SDK". On GitHub, the drift came from an extra runtime, not from an extra SDK. A second SDK of a later patch would do the same, because SDK 10.0.402 brings runtime 10.0.13.

The build must also use that root: `PATH` must find it first, and `DOTNET_ROOT` must name it. The setup action does both.

### A second lock: `DOTNET_ROLL_FORWARD=Disable`

This variable replaces the rule in every `runtimeconfig.json`. With `Disable`, each tool runs on exactly the version it asks for, 10.0.12, or it does not start. On Peter's Mac, we made a copy of the dotnet root with an extra runtime folder named 10.0.13. A test build without the variable ran the CLI and the compiler server on 10.0.13. With `DOTNET_ROLL_FORWARD=Disable`, both ran on 10.0.12. The build succeeded both times (host trace and `lsof`, 3 November 2026).

We do not use it as the fix. It acts on every .NET program in the shell, not only on the SDK. A program that asks for a version that is not installed exactly does not start. The test app asks for 10.0.0, and it failed with `Disable`. Test hosts and `dotnet` tools can fail in the same way. Microsoft recommends `Disable` only for testing.
