# Contributing

Bug reports, hardware results, documentation fixes, and pull requests are welcome.

## Issues

When reporting a problem, include:

- which build (`Suicune`, `HoOh`, `Lugia`, `Snorlax`, `BeastFinder`)
- console model
- CPU mode
- Luma3DS version
- the message on the plugin's screen and the point where it stopped
- a photo or exception screen when available

Do not upload save files or personal data unless they are necessary and you understand what they contain.

## Pull requests

1. Describe the problem and the behavior your change introduces.
2. Keep every build reset-only. Changes that write to the game's RNG, timers, clock or Pokémon data, or that time inputs to pick a result, will not be accepted.
3. Add or update tests in `tests/celebi.rs` when changing input handling.
4. Run the tests and build checks described in [docs/BUILDING.md](docs/BUILDING.md).
5. A new target is only listed as supported after a real hunt on hardware.

## License and modified versions

Crystal Auto Reset is a modified version of [CelebiHunter](https://github.com/Kou1236/CelebiHunter) and is licensed under GPL-3.0-or-later, like the original. If you distribute a modified version:

- keep the license and existing copyright notices;
- state that the version was modified and give the date of the changes;
- provide the corresponding source code for any distributed binaries;
- credit CelebiHunter as the upstream project and link to the original repository;
- keep the PokeReader attribution in the [README credits](README.md#credits);
- do not present a modified build as an official CelebiHunter or Crystal Auto Reset release.
