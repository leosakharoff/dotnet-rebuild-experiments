# Shared build and comparison tools

Both parts of experiment 2 use these tools. They were copied unchanged from
[Speciale2026](https://github.com/peterjuulm/Speciale2026) at `f127442`,
from `dependencies/experiments/nupkg/`.

## Install an SDK

`install-sdk.py` installs a specific .NET SDK into an empty folder from Microsoft's
archive. It verifies the archive's SHA-512 checksum against the release metadata.

```bash
python3 -I install-sdk.py VERSION DIR
```

## Inspect an assembly

`dllreport.cs` reads a DLL and its portable PDB. It produces a text report with separate
hashes for each section, metadata stream and resource, so reports from two builds can be
compared. Run it as a file-based app with the .NET 10 SDK:

```bash
dotnet run dllreport.cs -- DLL [PDB]
```

## Compare without signatures

`stripsign.cs` compares complete DLLs after removing the Authenticode block, strong-name
signature and PE checksum. In the recorded run, it was built as a `net10.0` console
project and invoked from that project:

```bash
dotnet run -- SHIPPED.dll OURS.dll
```
