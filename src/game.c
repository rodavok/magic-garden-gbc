#include <gb/gb.h>
#include <rand.h>
#include "game.h"
#include "sfx.h"
#include "music.h"

game_t G;

static const uint16_t row_mask[GH] = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048 };
#define DIRTY_ROW(y)   (G.dirty_rows |= row_mask[y])
#define DIRTY_CELL(i)  DIRTY_ROW((i) / GW)
#define cidx(x, y) ((uint8_t)((y) * GW + (x)))
static const int8_t DX[4] = { 0, 1, 0, -1 };
static const int8_t DY[4] = { -1, 0, 1, 0 };

/* cell index one step from (x,y) in direction d, or 0xFF when that leaves the grid */
static uint8_t neighbor(uint8_t x, uint8_t y, uint8_t d) {
    switch (d) {
    case D_UP:    return y == 0 ? 0xFF : (uint8_t)(cidx(x, y) - GW);
    case D_DOWN:  return y == GH - 1 ? 0xFF : (uint8_t)(cidx(x, y) + GW);
    case D_LEFT:  return x == 0 ? 0xFF : (uint8_t)(cidx(x, y) - 1);
    default:      return x == GW - 1 ? 0xFF : (uint8_t)(cidx(x, y) + 1);
    }
}
static uint8_t rnd(uint8_t n) { return (uint8_t)(rand() % n); }
static uint8_t on_pad(uint8_t i) { return (uint8_t)((G.pad_rows[i / GW] >> (i % GW)) & 1); }

/* ---- entity lists ---- */
static void list_remove(uint8_t *list, uint8_t *n, uint8_t cell) {
    uint8_t k;
    for (k = 0; k < *n; k++) if (list[k] == cell) { list[k] = list[*n - 1]; (*n)--; return; }
}
static void set_cell(uint8_t i, uint8_t type) { G.grid[i] = type; DIRTY_CELL(i); }

static void add_angry(uint8_t i, uint8_t idle) {
    if (G.n_angry >= MAX_ANGRY) { set_cell(i, C_EMPTY); return; }
    set_cell(i, C_ANGRY); G.gstate[i] = A_IDLE; G.gtimer[i] = idle;
    G.angry_list[G.n_angry++] = i;
}
static void remove_angry(uint8_t i) {
    if (G.gstate[i] & A_SPRITE) G.hop_sprites--;
    set_cell(i, C_EMPTY); list_remove(G.angry_list, &G.n_angry, i);
}
static void remove_flask(uint8_t i) {
    uint8_t k;
    for (k = 0; k < G.n_flask; k++) if (G.flask_list[k] == i) {
        G.flask_list[k] = G.flask_list[G.n_flask - 1]; G.flask_fall[k] = G.flask_fall[G.n_flask - 1]; G.n_flask--; break;
    }
    set_cell(i, C_EMPTY);
}

/* the original tries 10 random cells in columns/rows 0..10 that hold nothing, then gives up (potions scan) */
static uint8_t random_free_cell(uint8_t tries, uint8_t scan) {
    uint8_t x, y, i;
    while (tries--) {
        x = rnd(11); y = rnd(11); i = cidx(x, y);
        if (G.grid[i] == C_EMPTY && !(x == G.px && y == G.py)) return i;
    }
    if (scan) for (i = 0; i < NCELLS; i++) if (G.grid[i] == C_EMPTY && i != cidx(G.px, G.py)) return i;
    return 0xFF;
}

static void spawn_friend(void) {
    uint8_t i = random_free_cell(10, 0);
    if (i == 0xFF) return;
    set_cell(i, C_FRIEND); G.n_friend++;
}
static void spawn_appear(uint8_t type, uint8_t tries) {
    uint8_t i;
    if (G.n_appear >= MAX_APPEAR) return;
    i = random_free_cell(tries, 0);
    if (i == 0xFF) return;
    set_cell(i, type); G.gtimer[i] = APPEAR_FRAMES; G.gstate[i] = 0;
    G.appear_list[G.n_appear++] = i;
}
static void spawn_flask(uint8_t level) {
    uint8_t i;
    if (G.n_flask >= MAX_FLASK) return;
    i = random_free_cell(10, 1);
    if (i == 0xFF) return;
    set_cell(i, C_FLASK); G.gstate[i] = level; G.gtimer[i] = FLASK_UPGRADE;
    G.flask_fall[G.n_flask] = POTION_FALL; G.flask_list[G.n_flask++] = i;
}

/* ---- star pads: column 1, column 10, row 1, row 10, or a 4x4 ring / blob at a random spot ---- */
static void make_pad(void) {
    uint8_t size = rnd(8), y, x;
    if (size == G.pad_last_size) size = rnd(8);
    G.pad_last_size = size;
    for (y = 0; y < GH; y++) G.pad_rows[y] = 0;
    switch (size) {
    case 0: for (y = 0; y < GH; y++) G.pad_rows[y] = 1 << 1; break;
    case 1: for (y = 0; y < GH; y++) G.pad_rows[y] = 1 << 10; break;
    case 2: G.pad_rows[1] = 0xFFF; break;
    case 3: G.pad_rows[10] = 0xFFF; break;
    default: {
        uint8_t ring = rnd(2) == 0;
        x = rnd(9); y = rnd(9);
        if (ring) {
            G.pad_rows[y] = 0xF << x; G.pad_rows[y + 3] = 0xF << x;
            G.pad_rows[y + 1] = 0x9 << x; G.pad_rows[y + 2] = 0x9 << x;
        } else {
            G.pad_rows[y] = 0x6 << x; G.pad_rows[y + 3] = 0x6 << x;
            G.pad_rows[y + 1] = 0xF << x; G.pad_rows[y + 2] = 0xF << x;
        }
        break; }
    }
    G.pad_life = PAD_LIFE; G.pad_flash = 0;
    G.dirty_rows = 0xFFF;
}

void game_init(void) {
    uint8_t i;
    for (i = 0; i < NCELLS; i++) { G.grid[i] = C_EMPTY; G.gstate[i] = 0; G.gtimer[i] = 0; }
    G.trail_len = 0; G.n_angry = 0; G.n_appear = 0; G.n_flask = 0; G.n_friend = 0; G.hop_sprites = 0;
    G.clear_n = 0; G.clear_k = 0; G.clear_timer = 0;
    for (i = 0; i < MAX_POPS; i++) G.pops[i].t = 0;
    G.pop_dirty = 0;
    G.px = 1; G.py = 1; G.dir = D_RIGHT; G.dir_choice = D_RIGHT; G.sub = 0; G.turned = 0;
    G.z = 0; G.zvel = 0; G.pending_grow = 0; G.drop_anim = 0; G.turn_timer = 0; G.turn_pose = 0;
    G.pad_last_size = 0xFF; G.pad_anim = 0;
    G.saved = 0; G.score = 0;
    G.flask_counter = 0; G.friend_target = FRIEND_BASE; G.potion_delay = 0; G.potion_type = 0;
    G.power_timer = 0; G.power_mush = 0; G.mult = 1; G.chain = 0;
    G.angry_spawn_timer = 0;
    G.slow_tick = 0;
    G.state = PS_WAIT; G.state_timer = 0;
    G.palette_set = 0; G.hud_dirty = 1; G.dirty_rows = 0xFFF; G.flash = 0;
    G.best_drop = 0; G.best_chain = 0; G.total_kills = 0;
    make_pad();
    spawn_friend(); spawn_friend();
}

static void die(void) {
    G.state = PS_DEAD; G.state_timer = 90; G.z = 0; G.zvel = 0;
    music_play(SONG_LOSE);
    sfx_death();
}

static void power_expire(void) {
    uint8_t k;
    G.power_timer = 0; G.mult = 1; G.chain = 0; G.power_mush = 0;
    for (k = 0; k < G.n_angry; k++) {
        uint8_t i = G.angry_list[k], s = G.gstate[i];
        if (A_STATE(s) != A_HOP && A_STATE(s) != A_STUN) { G.gstate[i] = A_IDLE | (s & A_SPRITE); G.gtimer[i] = ENEMY_IDLE_AFTER_POWER; DIRTY_CELL(i); }
    }
    G.angry_spawn_timer = 1;   /* an enemy spawns as soon as the flask wears off */
}

static void add_pop(uint8_t cell, uint32_t val) {
    uint8_t k;
    for (k = 0; k < MAX_POPS; k++) if (G.pops[k].t == 0) {
        G.pops[k].x = cell % GW; G.pops[k].y = cell / GW; G.pops[k].t = 60; G.pops[k].val = val; G.pop_dirty |= (uint8_t)(1 << k); return;
    }
}
static void kill_enemy(uint8_t i) {
    uint32_t val = (uint32_t)(10 + (uint16_t)G.chain * 10) * G.mult;   /* 32-bit: a long power chain overflows 16 */
    if (G.grid[i] == C_ANGRY) remove_angry(i); else set_cell(i, C_EMPTY);
    sfx_kill();
    add_pop(i, val);
    G.score += val;
    G.chain++;
    G.total_kills++;
    if (G.chain > G.best_chain) G.best_chain = G.chain;
    G.hud_dirty = 1;
}

static void pickup_flask(uint8_t i) {
    uint8_t level = G.gstate[i];
    remove_flask(i);
    sfx_flask();
    if (G.power_timer == 0) G.chain = 0;
    G.power_timer = POWER_FRAMES;
    if (level >= 1) G.mult++;
    if (level >= 2) G.power_mush = 1;
    if (level >= 3) { G.friend_target++; spawn_friend(); }
    G.hud_dirty = 1;
}

/* cell-aligned events on arriving in a cell: loose oppies and the trail (as in the original, these only
   trigger with the player exactly on a cell) */
static uint8_t arrive_cell(uint8_t i, uint8_t *grew) {
    switch (G.grid[i]) {
    case C_FRIEND:
        set_cell(i, C_EMPTY); G.n_friend--; *grew = 1; sfx_pickup();
        if (G.n_friend < G.friend_target) spawn_friend();
        break;
    case C_TRAIL:
        if (G.trail_len && i == G.trail[G.trail_len - 1]) break;   /* the tail is vacated this step */
        die(); return 1;
    default: break;
    }
    return 0;
}

static void advance_trail(uint8_t old_head, uint8_t grew) {
    uint8_t k;
    if (grew) { if (G.trail_len < MAX_TRAIL) G.trail_len++; else grew = 0; }
    if (G.trail_len == 0) return;
    if (!grew) {
        uint8_t tail = G.trail[G.trail_len - 1];
        if (G.grid[tail] == C_TRAIL) set_cell(tail, C_EMPTY);
    }
    for (k = G.trail_len - 1; k > 0; k--) G.trail[k] = G.trail[k - 1];
    G.trail[0] = old_head;
    set_cell(old_head, C_TRAIL);
}

/* B: every trail oppie is judged now (on the pad or not) and resolved one per 10 frames, as the original's
   FollowClear objects do; pending cells are harmless to walk through */
static void do_drop(void) {
    uint8_t k, nsaved = 0, i;
    G.drop_anim = 16;
    if (G.trail_len == 0 || G.clear_n) return;
    for (k = 0; k < G.trail_len; k++) {
        i = G.trail[k];
        G.gstate[i] = (!G.pad_flash && on_pad(i)) ? 1 : 0;
        if (G.gstate[i]) nsaved++;
        set_cell(i, C_CLEARING);
    }
    G.clear_n = G.trail_len; G.clear_k = 0; G.clear_timer = 10;
    G.trail_len = 0;
    G.hud_dirty = 1;
    if (nsaved == 0) { sfx_bad_drop(); return; }
    sfx_save();
    G.saved += nsaved;
    if (nsaved > G.best_drop) G.best_drop = nsaved;
    G.flask_counter += nsaved;
    if (G.flask_counter >= FLASK_NEEDED) {
        uint8_t level = G.flask_counter - FLASK_NEEDED;
        if (level > 3) level = 3;
        G.flask_counter = 0;
        G.potion_type = level; G.potion_delay = POTION_DELAY;
    }
    G.palette_set = (uint8_t)(G.saved / 50);
    if (G.palette_set > 3) G.palette_set = 3;
    G.pad_flash = PAD_FLASH;   /* the pad flashes and a new one appears when it ends */
    G.dirty_rows = 0xFFF;
}
static void update_clearing(void) {
    if (!G.clear_n) return;
    if (--G.clear_timer) return;
    G.clear_timer = 10;
    {
        uint8_t i = G.trail[G.clear_k];
        if (G.grid[i] == C_CLEARING) {
            if (G.gstate[i]) { set_cell(i, C_EMPTY); G.score += (uint32_t)10 * (G.clear_k + 1); add_pop(i, (uint32_t)10 * (G.clear_k + 1)); G.hud_dirty = 1; }
            else add_angry(i, ENEMY_IDLE);
        }
        if (++G.clear_k == G.clear_n) {
            G.clear_n = 0;
            if (G.saved >= WIN_SAVED) { G.state = PS_WIN; G.state_timer = 0; sfx_win(); }
        }
    }
}

/* ---- angry oppies: idle 128 (look at 64), hop 16 frames, stun 240; frozen while a flask is active ---- */
static uint8_t pick_dir(uint8_t i, uint8_t d) {
    uint8_t x = i % GW, y = i / GW, tries = 4;
    while (tries--) {
        uint8_t t = neighbor(x, y, d);
        if (t != 0xFF && G.grid[t] == C_EMPTY) return d;
        d = (d + 1) & 3;
    }
    return D_NONE;
}
static uint8_t update_angry(uint8_t i) {
    uint8_t s = G.gstate[i], st = A_STATE(s), spr = s & A_SPRITE;
    if (st == A_HOP) {
        if (--G.gtimer[i] == 0) {
            if (spr) G.hop_sprites--;
            G.gstate[i] = A_IDLE; G.gtimer[i] = ENEMY_IDLE; DIRTY_CELL(i);
        }
        return i;
    }
    if (G.power_timer) return i;
    if (st == A_STUN) {
        if (--G.gtimer[i] == 0) { G.gstate[i] = A_IDLE; G.gtimer[i] = ENEMY_IDLE; DIRTY_CELL(i); }
        return i;
    }
    if (--G.gtimer[i] == ENEMY_LOOK_AT) {
        uint8_t d = pick_dir(i, rnd(4));
        if (d == D_NONE) { G.gtimer[i] = ENEMY_IDLE; return i; }
        G.gstate[i] = A_LOOK | (d << 2); DIRTY_CELL(i);
        return i;
    }
    if (G.gtimer[i] == 0) {
        uint8_t d = pick_dir(i, A_DIR(s)), t;
        if (d == D_NONE || st != A_LOOK) { G.gstate[i] = A_IDLE; G.gtimer[i] = ENEMY_IDLE; DIRTY_CELL(i); return i; }
        t = neighbor(i % GW, i / GW, d);
        set_cell(i, C_EMPTY); G.gstate[i] = 0;
        set_cell(t, C_ANGRY); G.gstate[t] = A_HOP | (d << 2); G.gtimer[t] = ENEMY_HOP;
        if (G.hop_sprites < MAX_HOP_SPRITES) { G.gstate[t] |= A_SPRITE; G.hop_sprites++; }
        return t;
    }
    return i;
}

static void update_entities(void) {
    uint8_t k, i;
    for (k = 0; k < G.n_angry; k++) G.angry_list[k] = update_angry(G.angry_list[k]);
    for (k = 0; k < G.n_appear; ) {
        i = G.appear_list[k];
        {
            uint8_t t = --G.gtimer[i];
            if ((t % 60) == 0) DIRTY_CELL(i);
            if (t != 0) { k++; continue; }
        }
        G.appear_list[k] = G.appear_list[--G.n_appear];
        if (G.grid[i] == C_APPEAR_ANGRY) add_angry(i, ENEMY_IDLE);
        else if (G.grid[i] == C_APPEAR_MUSH) set_cell(i, C_MUSH);
    }
    for (k = 0; k < G.n_flask; k++) {
        i = G.flask_list[k];
        if (G.flask_fall[k]) G.flask_fall[k]--;
        else if (G.slow_tick == 0 && G.gstate[i] < 3 && --G.gtimer[i] == 0) { G.gstate[i]++; G.gtimer[i] = FLASK_UPGRADE; }
    }
}

static void update_spawners(void) {
    /* passive angry spawn every 240 frames, paused while a flask is active */
    if (!G.power_timer && G.angry_spawn_timer && --G.angry_spawn_timer == 0) {
        G.angry_spawn_timer = ENEMY_SPAWN;
        spawn_appear(C_APPEAR_ANGRY, 10);
    }
    /* flask drop-in */
    if (G.potion_delay && --G.potion_delay == 0) spawn_flask(G.potion_type);
    /* star pad life */
    if (G.pad_flash) {
        if (--G.pad_flash == 0) make_pad();
        else if ((G.pad_flash % 5) == 0) G.dirty_rows = 0xFFF;
    } else if (--G.pad_life == 0) {
        uint8_t n = G.palette_set + 1;   /* 1 mushroom per rank */
        sfx_spawn();
        while (n--) spawn_appear(C_APPEAR_MUSH, 20);
        make_pad();
    }
    if (++G.pad_anim == PAD_TWINKLE) { G.pad_anim = 0; G.dirty_rows = 0xFFF; }
}

/* ---- per-frame collisions in units: player box [1..14], enemies/mushrooms [4..11], flasks [0..15] ---- */
static int16_t abs16(int16_t v) { return v < 0 ? -v : v; }
static uint8_t collide(void) {
    int16_t ax = (int16_t)G.px * CELL_UNITS + DX[G.dir] * (int16_t)G.sub;
    int16_t ay = (int16_t)G.py * CELL_UNITS + DY[G.dir] * (int16_t)G.sub;
    uint8_t k, i;
    /* angry oppies (hoppers use their in-flight position) */
    for (k = 0; k < G.n_angry; k++) {
        uint8_t s; int16_t ex, ey;
        i = G.angry_list[k]; s = G.gstate[i];
        ex = (int16_t)(i % GW) * CELL_UNITS; ey = (int16_t)(i / GW) * CELL_UNITS;
        if (A_STATE(s) == A_HOP) { ex -= DX[A_DIR(s)] * (int16_t)G.gtimer[i]; ey -= DY[A_DIR(s)] * (int16_t)G.gtimer[i]; }
        if (G.z) {
            if (abs16(ax - ex) < 4 && abs16(ay - ey) < 4 && A_STATE(s) != A_STUN && A_STATE(s) != A_HOP) {
                G.gstate[i] = A_STUN | (s & A_SPRITE); G.gtimer[i] = STUN_FRAMES; DIRTY_CELL(i);
            }
            continue;
        }
        if (ax + PLAYER_HI >= ex + ENEMY_LO && ex + ENEMY_HI >= ax + PLAYER_LO &&
            ay + PLAYER_HI >= ey + ENEMY_LO && ey + ENEMY_HI >= ay + PLAYER_LO) {
            if (G.power_timer) { kill_enemy(i); k--; continue; }
            die(); return 1;
        }
    }
    if (G.z) return 0;
    /* mushrooms and flasks in the current and next cell */
    for (k = 0; k < 2; k++) {
        int16_t ex, ey;
        i = k == 0 ? cidx(G.px, G.py) : neighbor(G.px, G.py, G.dir);
        if (i == 0xFF) continue;
        ex = (int16_t)(i % GW) * CELL_UNITS; ey = (int16_t)(i / GW) * CELL_UNITS;
        if (G.grid[i] == C_MUSH) {
            if (ax + PLAYER_HI >= ex + ENEMY_LO && ex + ENEMY_HI >= ax + PLAYER_LO &&
                ay + PLAYER_HI >= ey + ENEMY_LO && ey + ENEMY_HI >= ay + PLAYER_LO) {
                if (G.power_timer && G.power_mush) kill_enemy(i);
                else { die(); return 1; }
            }
        } else if (G.grid[i] == C_FLASK) {
            uint8_t f;
            for (f = 0; f < G.n_flask; f++) if (G.flask_list[f] == i && G.flask_fall[f] == 0) {
                if (ax + PLAYER_HI >= ex && ex + 15 >= ax + PLAYER_LO && ay + PLAYER_HI >= ey && ey + 15 >= ay + PLAYER_LO) pickup_flask(i);
                break;
            }
        }
    }
    return 0;
}

static void step_arrive(void) {
    uint8_t old = cidx(G.px, G.py), ni = neighbor(G.px, G.py, G.dir), grew = 0;
    if (ni == 0xFF) { die(); return; }
    if (G.pending_grow) { G.pending_grow = 0; grew = 1; }
    if (G.z == 0) { uint8_t g2 = 0; if (arrive_cell(ni, &g2)) return; grew |= g2; }
    advance_trail(old, grew);
    G.px = ni % GW; G.py = ni / GW;
    if (G.grid[ni] == C_APPEAR_ANGRY || G.grid[ni] == C_APPEAR_MUSH) { set_cell(ni, C_EMPTY); list_remove(G.appear_list, &G.n_appear, ni); }
}

void game_update(uint8_t joy, uint8_t pressed) {
    static const uint8_t jbit[4] = { J_UP, J_RIGHT, J_DOWN, J_LEFT };
    if (G.state == PS_DEAD || G.state == PS_WIN) { if (G.state_timer) G.state_timer--; return; }
    if (G.state == PS_WAIT) {
        /* the run starts on Right or Down from the top-left corner */
        if (joy & J_RIGHT) { G.dir_choice = D_RIGHT; G.state = PS_PLAY; G.angry_spawn_timer = ENEMY_SPAWN; }
        else if (joy & J_DOWN) { G.dir_choice = D_DOWN; G.state = PS_PLAY; G.angry_spawn_timer = ENEMY_SPAWN; }
        else return;
    }
    G.slow_tick = (G.slow_tick + 1) & 3;

    /* input (grounded only): a fresh press wins, else a single held direction; never a reversal */
    if (G.z == 0) {
        uint8_t d, want = D_NONE, opp = (G.dir + 2) & 3, held = 0, held_d = D_NONE, old = G.dir_choice;
        for (d = 0; d < 4; d++) {
            if (d == opp) continue;
            if (pressed & jbit[d]) want = d;
            if (joy & jbit[d]) { held++; held_d = d; }
        }
        if (want == D_NONE && held == 1 && held_d != opp) want = held_d;
        if (want != D_NONE) G.dir_choice = want;
        if (G.dir_choice != old && G.sub <= LATE_TURN && !G.turned && G.dir_choice != G.dir) G.sub = 0;   /* late turn: snap back */
        if ((pressed & J_A) && G.z == 0) { G.z = JUMP_Z0; G.zvel = JUMP_V0; sfx_jump(); }
        if (pressed & J_B) do_drop();
        if (G.state != PS_PLAY) return;
    }

    /* movement: pick the direction at a boundary, then move one unit */
    if (G.sub == 0) {
        G.turned = (G.dir != G.dir_choice);
        if (G.turned) {
            uint8_t vert = (G.dir == D_UP || G.dir == D_DOWN) ? G.dir : G.dir_choice;
            uint8_t horiz = (G.dir == D_LEFT || G.dir == D_RIGHT) ? G.dir : G.dir_choice;
            G.turn_pose = (vert == D_UP ? 1 : 0) | (horiz == D_RIGHT ? 2 : 0);
            G.turn_timer = 8;
        }
        G.dir = G.dir_choice;
    }
    G.sub++;
    if (G.sub == CELL_UNITS) {
        G.sub = 0;
        step_arrive();
        if (G.state != PS_PLAY) return;
    }
    /* jump physics: v -= 0.1 per frame, z += v, grounded when z <= 0 (30 frames) */
    if (G.z) {
        int16_t z = (int16_t)G.z;
        if (G.zvel > -40) G.zvel--;
        z += G.zvel;
        if (z <= 0) {
            uint8_t grew = 0;
            G.z = 0; G.zvel = 0;
            if (G.sub == 0 && arrive_cell(cidx(G.px, G.py), &grew)) return;
            if (grew) G.pending_grow = 1;
        } else G.z = (uint8_t)z;
    }
    if (collide()) return;
    if (G.drop_anim) G.drop_anim--;
    if (G.turn_timer) G.turn_timer--;

    update_entities();
    update_spawners();
    update_clearing();
    { uint8_t k; for (k = 0; k < MAX_POPS; k++) if (G.pops[k].t) G.pops[k].t--; }

    /* vulnerable enemies flash blue/white every 6 frames while a flask is active */
    {
        uint8_t f = G.power_timer ? ((G.frame_count / 6) & 1) : 0;
        if (f != G.flash) { G.flash = f; G.dirty_rows = 0xFFF; }
    }
    if (G.power_timer) {
        if (--G.power_timer == 0) power_expire();
        else if (G.power_timer == 150 || G.power_timer == 100 || G.power_timer == 50) sfx_tick();
        if ((G.power_timer % 10) == 0) G.hud_dirty = 1;
    }
}
