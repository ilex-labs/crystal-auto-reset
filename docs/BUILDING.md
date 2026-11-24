# Building

All builds come from one Rust core (`core/`) plus a small C/assembly entry layer (`3gx/`). Each build is a Cargo feature that picks the target encounter; `tools/build_legacy.py` compiles it, links it, audits the result and packages the `.3gx`.

## Dependencies

- Python 3.10 or newer
- devkitARM, plus libctru's `source/svc.s`
- 3gxtool
- Rust `nightly-2024-03-21` with the `rust-src` component

On x86_64 Linux, `tools/setup_toolchain_linux.sh` fetches the exact versions used for the released binaries: devkitARM from the `devkitpro/devkitarm` Docker image (layer hashes are checked), libctru's `svc.s`, Rust `nightly-2024-03-21`, and 3gxtool at commit `57e3160ab7`.

```text
tools/setup_toolchain_linux.sh
source .toolchain/env.sh
```

`env.sh` sets `CRYSTAL_RUST_HOST=x86_64-unknown-linux-gnu`. Without it the script uses the Windows toolchain name `nightly-2024-03-21-x86_64-pc-windows-gnu`, as CelebiHunter does.

The script looks for tools on `PATH` and under `.toolchain/`. Set `DEVKITPRO` to your devkitPro directory if needed, or point `CELEBIHUNTER_TOOLCHAIN_ROOT` at a toolchain stored elsewhere. For an offline build with a Cargo vendor directory, set `CELEBIHUNTER_VENDOR_DIR`.

## Commands

Build everything:

```text
python3 tools/build_legacy.py
```

Build one or more targets:

```text
python3 tools/build_legacy.py --suicune
python3 tools/build_legacy.py --hooh --lugia
python3 tools/build_legacy.py --snorlax --beastfinder
```

`--reset` builds CelebiHunter's original Celebi target from this tree. It is kept for comparison with upstream; for an actual Celebi hunt, use CelebiHunter's own Reset v1.0.0 release (see the README).

Outputs go to `dist/<Name>.3gx`, with checksums in `dist/SHA256SUMS.txt`. Every build is audited before it is accepted: it must carry the reset runtime marker, must not link the RNG resolver or the retired DIV gate, must stay within its stack budgets, and must not contain debug or private strings.

## Reproducing the tested binaries

The hardware results in the README were produced with specific binaries. Each one rebuilds byte-for-byte from the commit that added or last changed its target:

| Build | Commit | SHA-256 |
|---|---|---|
| `Suicune.3gx` | `Add Tin Tower Suicune reset variant` | `51979c9a3f9cde91…` |
| `HoOh.3gx`, `Lugia.3gx` | `Add Ho-Oh and Lugia reset variants` | `a0e2209fb6a80bdc…`, `51767e85a70a3e11…` |
| `BeastFinder.3gx` | `Beasts: save inside gate, step out once, reload if no beast arrived` | `68d7c76917245bf0…` |
| `Snorlax.3gx` | `Snorlax: advance the three wake-up text prompts` | `e393bfa1e12e67ac…` |

Check out the commit, build that target with the toolchain above, and compare `dist/SHA256SUMS.txt`. Later commits touch shared code, so tip builds of Suicune, Ho-Oh, Lugia and BeastFinder are not the same files as the ones tested. Snorlax was the last target added, and its tip build is still the tested file.

## Tests

The controller and reset tests are plain Rust and run on the host:

```text
mkdir -p build
rustc --test --edition 2021 tests/celebi.rs -O -o build/celebi_tests
build/celebi_tests
```

CI runs the same suite on every push.

## Releases

Do not include a toolchain, ROM, CIA, native code dump, save, or personal capture in a release.
