// Dry-run harness: the plugin's own decision code (celebi_auto / celebi_session),
// fed from an emulator's memory instead of the 3DS VC process. Mirrors
// celebi_auto_runtime::screen() and celebi::observe().
#![allow(dead_code, static_mut_refs)]
extern crate alloc;
#[path = "../../core/src/crystal/celebi_auto.rs"] mod celebi_auto;
#[path = "../../core/src/crystal/celebi_rng/mod.rs"] mod celebi_rng;
#[path = "../../core/src/crystal/celebi_session.rs"] mod celebi_session;
#[path = "../../core/src/crystal/celebi_trace.rs"] mod celebi_trace;
use celebi_auto::*;
use celebi_session::*;

static mut BOT: Bot = Bot::new();
static mut MEM: *const u8 = core::ptr::null();
static mut TEXT_STAGE: Stage = Stage::Stopped;
static mut TEXT_TICK: u8 = 0;
static mut TEXT_NO_SAVE: bool = false;
static mut TEXT_MENU: bool = false;
static mut TEXT_SAVE_INFO: bool = false;
static mut TEXT_GS: bool = false;
static mut LAST_HOST: u8 = 0;
static mut FINAL_DONE: bool = false;

fn r8(a: u32) -> u8 { unsafe { *MEM.add(a as usize) } }
fn r16(a: u32) -> u16 { (r8(a) as u16) << 8 | r8(a + 1) as u16 }

fn screen(stage: Stage) -> Screen {
    let bank = r8(0xd439);
    let pos = r8(0xd43a) as u16 | (r8(0xd43b) as u16) << 8;
    let world = r8(0xcfbc) & 1 != 0 && r8(0xd432) == 2;
    let gs_position = bank == 0x1b && (pos == 0x6e53 || pos == 0x6e54);
    let text_sampled = unsafe {
        if TEXT_STAGE != stage {
            TEXT_STAGE = stage; TEXT_TICK = 0; TEXT_NO_SAVE = false; TEXT_MENU = false;
            TEXT_SAVE_INFO = false; TEXT_GS = false;
        }
        let sample = text_scan_due(stage, TEXT_TICK, gs_position);
        TEXT_TICK = (TEXT_TICK + 1) & 15;
        if sample {
            let mut tiles = [0u8; 360];
            for (i, t) in tiles.iter_mut().enumerate() { *t = r8(0xc4a0 + i as u32); }
            let has = |t: &[u8]| tile_contains(&tiles, t);
            TEXT_NO_SAVE = has(b"NEW GAME") && has(b"OPTION") && !has(b"CONTINUE") && !has(b"PLAYER");
            TEXT_MENU = has(b"CONTINUE") && has(b"NEW GAME");
            TEXT_SAVE_INFO = has(b"PLAYER") && has(b"BADGES");
            TEXT_GS = gs_position && has(b"put in the") && has(b"GS BALL.");
        }
        sample
    };
    Screen {
        wram_bank: r8(0xff70), script_bank: bank, script_pos: pos,
        x: r8(0xdcb8), y: r8(0xdcb7), bank: r8(0xff9d), frame: r8(0xff9b),
        joy: r8(0xffa4), joy_pressed: r8(0xffa7), game_joy: r8(0xffa8), joy_last: r8(0xffa9),
        text_sampled, no_save_menu: unsafe { TEXT_NO_SAVE }, menu: unsafe { TEXT_MENU },
        cursor: r8(0xcfa9), save_info: unsafe { TEXT_SAVE_INFO }, world,
        shrine: if beasts_mode() {
            r8(0xdcb8) <= 1 && (4..=5).contains(&r8(0xdcb7)) && r8(0xd437) == 0
        } else {
            r8(0xdcb8) == START_XY.0 && r8(0xdcb7) == START_XY.1 && r8(0xd4de) & 12 == 4 && r8(0xd437) == 0
        },
        dialog: bank == 0x1b && (0x6e39..=0x6e42).contains(&pos),
        gs_position, gs: gs_position && unsafe { TEXT_GS },
        physical_a: false, physical_x: false, physical_y: false,
        repel: r8(0xdca1), lead_level: r8(0xdcfe),
        lead_alive: r8(0xdd01) != 0 || r8(0xdd02) != 0,
        roam: [
            (r8(0xdfcf), (r8(0xdfd1), r8(0xdfd2)), r8(0xdfd3)),
            (r8(0xdfd6), (r8(0xdfd8), r8(0xdfd9)), r8(0xdfda)),
        ],
        map_music: r8(0xc2c0), menu_y: r8(0xcfa9), pokegear_card: r8(0xcf64),
        tuning_knob: r8(0xd958), script_mode: r8(0xd437),
        ..Screen::default()
    }
}
fn battle_screen() -> Screen {
    Screen { frame: r8(0xff9b), joy: r8(0xffa4), joy_pressed: r8(0xffa7), game_joy: r8(0xffa8),
             joy_last: r8(0xffa9), ..Screen::default() }
}
fn observe(battle: bool) -> Observation {
    Observation {
        rng: None, cpu_mhz: 268,
        tid: if battle { 0 } else { r16(0xd47b) },
        map: if battle { (0, 0) } else { (r8(0xdcb5), r8(0xdcb6)) },
        battle: r8(0xd22d), species: r8(0xd206), battle_start: r8(0xd264),
        battle_ended: r8(0xc734), level: r8(0xd213), hp: r16(0xd216), max_hp: r16(0xd218),
        dvs: [r8(0xd20c), r8(0xd20d)],
    }
}

#[no_mangle] pub extern "C" fn h_seed(e: u64) { unsafe { BOT.set_run_entropy(e) } }

/// One plugin callback. Returns motion (1 run, 2 pause, 3 step);
/// *buttons = JOYP buttons | host buttons (hJoypadDown layout).
#[no_mangle]
pub extern "C" fn h_service(mem: *const u8, paused: bool, physical_b: bool, entropy: u64, buttons: *mut u8) -> u32 {
    unsafe {
        MEM = mem;
        let stage = BOT.stage;
        let critical = stage == Stage::Battle;
        let obs = observe(critical);
        let s = if critical { battle_screen() } else { screen(stage) };
        let previous = BOT.stage;
        if natural_mode() && (previous == Stage::Track || (overworld_mode() && previous == Stage::Load)) {
            BOT.set_run_entropy(entropy);
        }
        let out = BOT.tick(obs, s, paused, true, physical_b);
        if !FINAL_DONE && matches!(BOT.stage, Stage::Stopped | Stage::Shiny | Stage::SaveResult) {
            FINAL_DONE = true;
            BOT.authorize_verified_reset(true);
        }
        if previous == Stage::Reset && BOT.stage == Stage::Title { FINAL_DONE = false; }
        if previous == Stage::Reset && BOT.stage == Stage::Stopped { FINAL_DONE = false; }
        let j = joyp_buttons_for_stage(BOT.stage, out.buttons);
        let h = host_buttons_for_stage(BOT.stage, out.buttons);
        *buttons = j | h;
        match out.motion { Motion::Run => 1, Motion::Pause => 2, Motion::Step => 3 }
    }
}
#[no_mangle] pub extern "C" fn h_stage() -> u32 { unsafe { BOT.stage as u32 } }
#[no_mangle] pub extern "C" fn h_attempts() -> u32 { unsafe { BOT.attempts } }
#[no_mangle] pub extern "C" fn h_found() -> u32 { unsafe { BOT.found_species as u32 } }
#[no_mangle] pub extern "C" fn h_message(buf: *mut u8, n: usize) -> usize {
    unsafe {
        let m = alloc::format!("{:?}|{}", BOT.stage, BOT.message);
        let b = m.as_bytes(); let k = b.len().min(n);
        core::ptr::copy_nonoverlapping(b.as_ptr(), buf, k); k
    }
}
