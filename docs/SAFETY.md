# Safety and recovery

The plugins only press buttons and soft reset. They never write to your save. The one save you make yourself, at the start position, is the save every attempt reloads, so protect it.

## Before installation

1. Save at the start position for your target (see the README) and close the game.
2. Create a new Checkpoint backup.
3. Copy the untouched backup to a computer.
4. Use a separately named test backup for any restore experiment.
5. Back up any existing Crystal-specific or global `.3gx` before replacing it.

## After a shiny

The plugin stops on the shiny's battle screen and never saves. Press `R` to hand control back, catch it, and save in game yourself.

## If the game crashes

1. Do not overwrite the untouched backup.
2. Reboot the console.
3. Remove the installed `.3gx` from `sd:/luma/plugins/0004000000172800/` if the game cannot start normally.
4. Confirm that the unmodified game opens and the in-game save loads.
5. Restore with Checkpoint only when a full rollback is actually intended.

A Checkpoint restore replaces the complete save. Any progress made after the selected backup will be lost.
