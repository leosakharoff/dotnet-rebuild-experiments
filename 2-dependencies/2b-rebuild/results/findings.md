# Experiment 2b: findings

The causes behind the **55** release builds whose code differs from the published package, grouped into **10** cause types. Evidence: [Builds with other code](../README.md#builds-with-other-code). Results per package: [summary.md](summary.md) and [categories.tsv](categories.tsv).

**Id.** `E2b-04` is cause type 4 in part 2b. **Code.** The cause, from the [codebook](../../../categories/codebook.md); after a slash, what a rebuilder lacked. METHOD marks a row that is about the measurement, not a cause. Experiment 2 counts cause types and packages; experiment 1 counts findings. The two are never added together.

| Id | Cause type | Packages | n | Code | Note |
| --- | --- | --- | --- | --- | --- |
| <a name="e2b-01"></a>**E2b-01** | Arcade's development versioning | Roslyn, EF Core, Sqlite | 17 | TIME / PROCESS | OfficialBuildId missing |
| <a name="e2b-02"></a>**E2b-02** | Clock in the version | IdentityModel | 9 | TIME / PROCESS | check: is the version enough? |
| <a name="e2b-03"></a>**E2b-03** | Date suffix on unofficial builds | Azure SDK, System.ClientModel | 8 | TIME / PROCESS | official-build flag missing |
| <a name="e2b-04"></a>**E2b-04** | Copyright year from the build clock | Swashbuckle, Stateless | 6 | TIME / PROCESS | build date not recorded |
| <a name="e2b-05"></a>**E2b-05** | Attributes written by the CI script | Bogus, YamlDotNet | 3 | CI / PROCESS |  |
| <a name="e2b-06"></a>**E2b-06** | Version computed from git | MediatR.Contracts, ExCSS | 2 | CI / SOURCE |  |
| <a name="e2b-07"></a>**E2b-07** | Targeting pack | SharpZipLib | 2 | TOOL / ENV |  |
| <a name="e2b-08"></a>**E2b-08** | RepositoryUrl form | two Serilog packages | 2 | CI / SOURCE | URL taken from the checkout |
| <a name="e2b-09"></a>**E2b-09** | Signing key | RecyclableMemoryStream | 1 | CI / PROCESS |  |
| <a name="e2b-10"></a>**E2b-10** | Not inspected | Google.Protobuf, ShimSkiaSharp | 5 | ? / ? | not inspected |
