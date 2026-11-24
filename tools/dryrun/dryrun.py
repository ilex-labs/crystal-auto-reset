#!/usr/bin/env python3
"""Dry-run the plugins' decision code against Pokémon Crystal in an emulator.

The game is pokecrystal11_vc.gbc built from pret/pokecrystal, run in PyBoy.
The plugin logic is harness.rs (the real celebi_auto / celebi_session code)
built for the host by build.sh. See README.md in this folder.

  dryrun.py newgame                         start a new game, save an emulator state
  dryrun.py save suicune hooh lugia snorlax beasts
                                            make an in-game save at each start spot
  dryrun.py run lugia --attempts 50         let the plugin hunt for N attempts
  dryrun.py run lugia --force-shiny 3       test hook: shiny DVs on attempt 3

Nothing here is part of the 3DS plugins. The save setup edits emulator
memory (party, items, flags) because a post-game save can't be played to
from scratch; the plugins themselves never write game memory.
"""
import argparse, ctypes, io, os, random, shutil, sys, time
from pyboy import PyBoy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.path.join(ROOT, "build", "dryrun")
PC = os.environ.get("POKECRYSTAL", os.path.join(ROOT, "..", "pokecrystal"))
ROM = os.path.join(PC, "pokecrystal11_vc.gbc")

TARGETS = {
    # map (group, number), warp index to arrive by, start tile, key items
    "suicune": dict(map=(4, 9), warp=12, xy=(37, 8), keys=[], lib="suicune"),
    "hooh":    dict(map=(15, 12), warp=1, xy=(9, 6), keys=[0xB2], lib="hooh"),          # Rainbow Wing
    "lugia":   dict(map=(3, 73), warp=1, xy=(9, 6), keys=[0x47], lib="lugia",           # Silver Wing
                    flash=True, surf_from=(9, 12)),
    "snorlax": dict(map=(12, 3), warp=2, xy=(34, 10), keys=[], lib="snorlax"),
    "beasts":  dict(map=(1, 9), warp=1, xy=(0, 4), keys=[], lib="beastfinder", beasts=True),
}
BUTTONS = [(1, "a"), (2, "b"), (4, "select"), (8, "start"),
           (0x10, "right"), (0x20, "left"), (0x40, "up"), (0x80, "down")]


def symbols():
    out = {}
    for line in open(os.path.join(PC, "pokecrystal11_vc.sym")):
        parts = line.split()
        if len(parts) == 2 and ":" in parts[0]:
            out[parts[1]] = int(parts[0].split(":")[1], 16)
    return out


def emulator(rom):
    pb = PyBoy(rom, window="null", sound_emulated=False)
    pb.set_emulation_speed(0)
    return pb


def press(pb, button, hold=4, wait=20):
    pb.button(button, hold)
    for _ in range(wait):
        pb.tick()


def tap(pb, direction):
    # A short tap turns in place if facing elsewhere, otherwise takes one step.
    pb.button_press(direction); pb.tick(); pb.tick(); pb.button_release(direction)
    for _ in range(24):
        pb.tick()


def has_text(m, text):
    enc = bytes((ord(c) - 65 + 0x80) if c.isupper() else (ord(c) - 97 + 0xA0) if c.islower() else 0x7F
                for c in text)
    return enc in bytes(m[0xC4A0 + i] for i in range(360))


def cmd_newgame(_):
    os.makedirs(WORK, exist_ok=True)
    pb = emulator(ROM)
    for _ in range(0, 7000, 20):          # A through the intro, default answers
        press(pb, "a", wait=20)
    for _ in range(300):
        pb.tick()
    m = pb.memory
    assert (m[0xDCB5], m[0xDCB6]) == (24, 7), "not in the bedroom"
    with open(os.path.join(WORK, "newgame.state"), "wb") as fh:
        pb.save_state(fh)
    pb.stop(save=False)
    print("new game ready")


def cmd_save(args):
    sym = symbols()
    for name in args.targets:
        make_save(name, TARGETS[name], sym)


def make_save(name, t, S):
    out = os.path.join(WORK, name)
    os.makedirs(out, exist_ok=True)
    rom = os.path.join(out, "crystal.gbc")
    shutil.copy(ROM, rom)
    if os.path.exists(rom + ".ram"):
        os.remove(rom + ".ram")
    pb = emulator(rom)
    with open(os.path.join(WORK, "newgame.state"), "rb") as fh:
        pb.load_state(fh)
    m = pb.memory

    # Progress the save needs: badges, Pokedex, Pokegear with every card.
    m[S["wJohtoBadges"]] = 0xFF
    m[S["wStatusFlags"]] |= 1 | (4 if t.get("flash") else 0)   # Pokedex (+ Flash for the dark chamber)
    m[S["wPokegearFlags"]] = 0x8F
    # One Lv35 Lapras with Surf: Lv17-40 lead for the beasts, Surf for Lugia.
    m[S["wPartyCount"]] = 1
    m[S["wPartySpecies"]] = 131
    m[S["wPartySpecies"] + 1] = 0xFF
    lv = 35
    mon = ([131, 0, 0x39, 33, 0, 0, m[S["wPlayerID"]], m[S["wPlayerID"] + 1], 0, 0xA0, 0]
           + [0] * 10 + [0xFF, 0xFF] + [15, 35, 0, 0]
           + [70, 0, 0, 0, lv, 0, 0, 0, 120, 0, 120] + [0, 90] * 5)
    assert len(mon) == 48
    for i, v in enumerate(mon):
        m[S["wPartyMon1"] + i] = v
    for a in (S["wPartyMonOTs"], S["wPartyMonNicknames"]):
        m[a], m[a + 1] = 0x80, 0x50
    m[S["wNumKeyItems"]] = len(t["keys"])
    for i, k in enumerate(t["keys"] + [0xFF]):
        m[S["wKeyItems"] + i] = k
    if t.get("beasts"):
        # Raikou and Entei roaming and unmet; Continue scatters them anyway.
        for base, species, where in ((S["wRoamMon1"], 243, (1, 13)), (S["wRoamMon2"], 244, (1, 14))):
            for i, v in enumerate([species, 40, where[0], where[1], 0, 0, 0]):
                m[base + i] = v
        m[S["wRepelEffect"]] = 250            # Max Repel

    # Take the bedroom stairs, redirecting that warp to the target map so the
    # game loads the target map itself.
    home = (m[S["wMapGroup"]], m[S["wMapNumber"]])
    redirected = False

    def redirect():
        nonlocal redirected
        nxt = (m[S["wNextMapGroup"]], m[S["wNextMapNumber"]])
        if not redirected and nxt[1] and nxt != home:
            m[S["wNextMapGroup"]], m[S["wNextMapNumber"]] = t["map"]
            m[S["wNextWarp"]] = t["warp"]
            redirected = True

    for step in ["right"] * 4 + ["up"] * 3:
        pb.button_press(step)
        for _ in range(16):
            pb.tick(); redirect()
        pb.button_release(step)
        for _ in range(4):
            pb.tick()
    for _ in range(240):
        pb.tick(); redirect()
    assert (m[S["wMapGroup"]], m[S["wMapNumber"]]) == t["map"], "warp redirect failed"

    pos = lambda: (m[S["wXCoord"]], m[S["wYCoord"]])
    if t.get("surf_from"):
        while pos()[1] > t["surf_from"][1]:
            tap(pb, "up")
        tap(pb, "up")
        for _ in range(4):
            if m[S["wPlayerState"]] == 4:
                break
            press(pb, "a", wait=90)
        for _ in range(120):
            pb.tick()
        assert m[S["wPlayerState"]] == 4, "could not Surf"

    # Walk to the start tile: breadth-first search over real moves.
    goal = t["xy"]
    start = io.BytesIO(); pb.save_state(start)
    seen = {pos(): start}
    queue = [pos()]
    while queue and goal not in seen:
        here = queue.pop(0)
        for d in ("up", "down", "left", "right"):
            seen[here].seek(0); pb.load_state(seen[here])
            for _ in range(2):
                before = pos()
                tap(pb, d)
                if pos() != before:
                    break
            if (m[S["wMapGroup"]], m[S["wMapNumber"]]) != t["map"] or m[S["wBattleMode"]]:
                continue
            if pos() not in seen:
                st = io.BytesIO(); pb.save_state(st)
                seen[pos()] = st; queue.append(pos())
    assert goal in seen, f"{name}: start tile unreachable"
    seen[goal].seek(0); pb.load_state(seen[goal])
    if m[S["wPlayerDirection"]] != 4:
        tap(pb, "up")
    assert pos() == goal and m[S["wPlayerDirection"]] == 4
    for _ in range(30):
        pb.tick()
    pb.screen.image.save(os.path.join(out, "spot.png"))

    # Save from the Start menu (6th entry: SAVE).
    press(pb, "start", wait=40)
    for _ in range(10):
        if m[S["wMenuCursorY"]] == 6:
            break
        press(pb, "down", wait=12)
    press(pb, "a", wait=90)
    for _ in range(6):
        if has_text(m, "saved"):
            break
        press(pb, "a", wait=90)
    assert has_text(m, "saved"), "save did not complete"
    for _ in range(200):
        pb.tick()
    pb.stop(save=True)
    print(f"{name}: saved at {goal}")


def cmd_run(args):
    t = TARGETS[args.target]
    lib = ctypes.CDLL(os.path.join(WORK, f"lib{t['lib']}.so"))
    lib.h_service.restype = ctypes.c_uint32
    lib.h_service.argtypes = [ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_uint64,
                              ctypes.POINTER(ctypes.c_uint8)]
    out_dir = os.path.join(WORK, args.target)
    pb = emulator(os.path.join(out_dir, "crystal.gbc"))
    m = pb.memory
    mem = bytearray(0x10000)
    pressed = ctypes.c_uint8(0)
    held, paused, frames, spins, last, forced = 0, False, 0, 0, "", False

    def message():
        buf = ctypes.create_string_buffer(200)
        n = lib.h_message(buf, 200)
        return buf.raw[:n].decode()

    started = time.time()
    while frames < 3000 * (args.attempts + 2):
        mem[0xC000:0xE000] = bytes(m[0xC000:0xE000])
        mem[0xFF00:0x10000] = bytes(m[0xFF00:0x10000])
        action = lib.h_service(bytes(mem), paused, False, random.getrandbits(64), ctypes.byref(pressed))
        want = pressed.value
        for bit, button in BUTTONS:
            if want & bit and not held & bit:
                pb.button_press(button)
            if held & bit and not want & bit:
                pb.button_release(button)
        held = want
        text = message()
        if text != last:
            print(f"f{frames:7d} attempt {lib.h_attempts():4d}  {text}")
            last = text
        stage = text.split("|")[0]
        if stage in ("Shiny", "Stopped"):
            for _, button in BUTTONS:
                pb.button_release(button)
            for _ in range(420):              # let the battle screen draw
                pb.tick()
            pb.screen.image.save(os.path.join(out_dir, "final.png"))
            print(f"stopped on species {m[0xD206]} Lv{m[0xD213]}, DVs {m[0xD20C]:02X} {m[0xD20D]:02X}")
            break
        if (args.force_shiny and lib.h_attempts() == args.force_shiny and m[0xFF70] & 7 == 1
                and m[0xD22D] == 1 and m[0xD206]):
            # Test hook only: make this encounter's DVs shiny.
            if (m[0xD20C], m[0xD20D]) != (0x2A, 0xAA):
                m[0xD20C], m[0xD20D] = 0x2A, 0xAA
                if not forced:
                    print("  [test hook] wrote shiny DVs 2A AA")
                forced = True
        if lib.h_attempts() > args.attempts and stage in ("Reset", "Title"):
            break
        if action == 2:                       # plugin paused the game
            paused = True; spins += 1
            if spins < 5000:
                continue
        spins = 0
        pb.tick(); frames += 1
        paused = action != 1
    print(f"{lib.h_attempts()} attempts, {frames} frames, {time.time() - started:.0f}s")
    pb.stop(save=False)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("newgame")
    s = sub.add_parser("save"); s.add_argument("targets", nargs="+", choices=TARGETS)
    r = sub.add_parser("run"); r.add_argument("target", choices=TARGETS)
    r.add_argument("--attempts", type=int, default=20)
    r.add_argument("--force-shiny", type=int, default=0)
    args = p.parse_args()
    {"newgame": cmd_newgame, "save": cmd_save, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    main()
