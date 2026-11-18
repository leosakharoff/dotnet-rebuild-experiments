# Experiment 2a: findings

The causes behind the **25** packages that stayed unreproducible with the deterministic-build configuration, grouped into **7** cause types. Evidence: [Packages not fixed by configuration](../README.md#packages-not-fixed-by-configuration). Results per package: [summary.md](summary.md) and [categories.tsv](categories.tsv).

**Id.** `E2a-04` is cause type 4 in part 2a. **Code.** The cause, from the [codebook](../../../coding/codebook.md); after a slash, what a rebuilder lacked. METHOD marks a row that is about the measurement, not a cause. Experiment 2 counts cause types and packages; experiment 1 counts findings. The two are never added together.

| Id | Cause type | Packages | n | Code | Why the configuration did not fix it |
| --- | --- | --- | --- | --- | --- |
| <a name="e2a-01"></a>**E2a-01** | Date in the package version | Azure SDK, System.ClientModel | 8 | TIME | the value is set before the compiler runs |
| <a name="e2a-02"></a>**E2a-02** | Clock in the package version | IdentityModel 8.23.0 | 5 | TIME | the value is set before the compiler runs |
| <a name="e2a-03"></a>**E2a-03** | Copyright year from the clock | Swashbuckle, Stateless | 4 | TIME | the value is set before the compiler runs |
| <a name="e2a-04"></a>**E2a-04** | npm under the time variation | Swashbuckle ReDoc, SwaggerUI | 2 | METHOD | not a cause: libfaketime breaks npm |
| <a name="e2a-05"></a>**E2a-05** | Arcade's date-based build number | Build.Framework | 1 | TIME | the value is set before the compiler runs |
| <a name="e2a-06"></a>**E2a-06** | Hash of the project path in the PDB | Quartz | 4 | PATH | `PathMap` maps only the path prefix |
| <a name="e2a-07"></a>**E2a-07** | PDB path not mapped | ClosedXML | 1 | PATH | `PathMap` maps only the path prefix |
