# Releasing

## Which binaries

Release the exact binaries that were tested on hardware. Each one rebuilds byte-for-byte from the commit listed in [docs/BUILDING.md](../docs/BUILDING.md#reproducing-the-tested-binaries); check its SHA-256 against that table before uploading.

A target is only released after a real hunt on hardware. If a later change to shared code is meant to ship, test the new build on a console first (at least one non-shiny cycle, a stop with `B`, and the target's own steps), then record its commit and hash.

## Checks

- Run the host tests and wait for GitHub Actions to pass.
- Every build must pass the audits in `tools/build_legacy.py`.

## GitHub release

1. Tag the release and use the tag as the release title.
2. Upload each `.3gx` and a `SHA256SUMS.txt` that covers them.
3. In the notes, list each file with the commit it was built from and its hardware result.
4. Verify each uploaded asset's SHA-256 against the local file. Leave an unverified build as a draft.
