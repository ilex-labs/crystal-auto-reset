# Dry run in an emulator

Runs the plugins' own decision code against Pokémon Crystal in a Game Boy emulator, so a change can be checked before it goes on a console.

- **Game:** `pokecrystal11_vc.gbc`, built from [pret/pokecrystal](https://github.com/pret/pokecrystal). This is the build that matches the 3DS Virtual Console release. No ROM is included here; you build it yourself.
- **Emulator:** [PyBoy](https://github.com/Baekalfen/PyBoy).
- **Plugin logic:** `harness.rs` compiles the real `celebi_auto.rs` and `celebi_session.rs` for the host, once per target. Each frame it gets the game's memory, builds the same screen and battle readings as `celebi_auto_runtime.rs`, and returns the buttons the plugin would press.

## Setup

```text
git clone https://github.com/pret/pokecrystal ../pokecrystal
(cd ../pokecrystal && make crystal11_vc)      # needs rgbds 1.0.4, see pokecrystal's INSTALL.md
pip install pyboy
tools/dryrun/build.sh                         # needs Rust nightly-2024-03-21, see docs/BUILDING.md
```

Set `POKECRYSTAL` if the disassembly is somewhere other than `../pokecrystal`. Everything is written to `build/dryrun/`.

## Use

```text
python3 tools/dryrun/dryrun.py newgame
python3 tools/dryrun/dryrun.py save suicune hooh lugia snorlax beasts
python3 tools/dryrun/dryrun.py run lugia --attempts 50
python3 tools/dryrun/dryrun.py run lugia --attempts 5 --force-shiny 3
```

- `newgame` plays through the intro with default answers.
- `save` makes an in-game save at each target's start spot. A post-game save can't be played to from scratch, so it writes the needed party, items, badges and flags into emulator memory, takes the bedroom stairs with the warp redirected to the target map, walks to the start tile by searching real moves, and saves from the Start menu. It also saves a picture of the spot as `build/dryrun/<target>/spot.png`.
- `run` starts the game from that save and lets the plugin logic play it. It prints each stage change and stops on a shiny, a stop, or the attempt limit.
- `--force-shiny N` is a test hook: on attempt N the script writes shiny DVs into the wild Pokémon, to check that the plugin stops. The plugins themselves never write game memory.

## What it doesn't cover

The 3DS side: the Virtual Console hook, how buttons are injected there, and console timing. Only hardware hunts test those.
