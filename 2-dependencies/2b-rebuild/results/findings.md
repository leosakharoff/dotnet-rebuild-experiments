# Experiment 2b findings

We derived a build recipe from the release’s recorded commit and the compiler identified in its debug symbols. We built twice from a fresh clone and compared the rebuilt assembly with the one published on nuget.org.

Of 198 attempts, 22 reproduced the published assembly, 14 byte for byte and eight when signatures were excluded. Another 112 yielded no package to compare, 71 because the build produced none and 41 because there was no recipe.

Of the 64 assemblies that differed, nine had the same code and 55 had different code. The table covers those 55. For most, the publisher’s build writes a value that the release records and the project has no input for.

A separate check with the publisher’s build system reproduced 35 more Microsoft packages outside the primary count. See **Builds with other code** in the [experiment README](../README.md) and the per-package [results](summary.md) and [categories](categories.tsv).

| Finding ID | Cause | Packages | Count | Where the difference is | Category | What a rebuilder lacked |
| --- | --- | --- | ---: | --- | --- | --- |
| <a name="e2b-01"></a> **E2b-01** | The official workflow sets `OfficialBuildId`. With that input missing, Arcade uses its development version. Build.Framework falls back to the date. | Roslyn 7, EF Core 7, Sqlite, DiaSymReader, Build.Framework | 17 | The development version writes `42.42.42.42424` to `FileVersion` in place of the shipped value and drops `+<commit>` from the informational version. | CI/CD modification | Build process |
| <a name="e2b-02"></a> **E2b-02** | The preview version includes the build time. | IdentityModel | 9 | Builds A and A2 produced different `8.23.0-preview-<clock>` versions for all nine packages. Whether the version accounts for the full difference is unclear. | Build timestamp | Build process |
| <a name="e2b-03"></a> **E2b-03** | The publisher’s workflow drops the date suffix. The rebuild adds it from the clock. | Azure SDK, System.ClientModel | 8 | The rebuild used `1.50.0-alpha.<date>.1` and the release used `1.50.0`. | CI/CD modification | Build process |
| <a name="e2b-04"></a> **E2b-04** | The build uses the current year for the copyright notice. The release records no build date. | Swashbuckle 5, Stateless | 6 | The copyright year differs between 2024 and 2026. | Build timestamp | Build process |
| <a name="e2b-05"></a> **E2b-05** | The publisher’s workflow runs a script to write assembly attributes. | Bogus, YamlDotNet, FluentModbus | 3 | `GenerateAssemblyInfo=false` disables generation by the project. The rebuild skips the script that supplies the values. | CI/CD modification | Build process |
| <a name="e2b-06"></a> **E2b-06** | MinVer and GitVersion compute versions from the Git checkout. | MediatR.Contracts by MinVer, ExCSS by GitVersion | 2 | MinVer’s tag height differs for MediatR.Contracts. ExCSS records the branch name in its informational version. | CI/CD modification | Source state |
| <a name="e2b-07"></a> **E2b-07** | The rebuild used a different targeting pack. | SharpZipLib, MediatR.Extensions.Microsoft.DependencyInjection | 2 | The display name in `TargetFrameworkAttribute` differs, and so do the assembly’s intermediate instructions. | Build tool version | Environment |
| <a name="e2b-08"></a> **E2b-08** | The build takes the repository URL from the checkout. | Serilog.Settings.Configuration, Serilog.Extensions.Logging | 2 | `RepositoryUrl` differs by the `.git` suffix. | CI/CD modification | Source state |
| <a name="e2b-09"></a> **E2b-09** | Signing uses a key stored outside the repository. | RecyclableMemoryStream | 1 | The strong name and the key in `InternalsVisibleTo` differ. | CI/CD modification | Build process |
| <a name="e2b-10"></a> **E2b-10** | Cause not examined. | Google.Protobuf, ShimSkiaSharp, Identity.Web 3 | 5 | Difference not examined. | Not examined | – |
