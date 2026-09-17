#include <gb/gb.h>
#include <rand.h>
#include "game.h"
#include "sfx.h"

game_t G;

/* row-dirty bookkeeping: cell / 12 -> bit in a 16-bit mask (kept as two byte tables: no variable shifts) */
static const uint16_t row_mask[GH] = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048 };
#define DIRTY_ROW(y)   (G.dirty_rows |= row_mask[y])
#define DIRTY_CELL(i)  DIRTY_ROW((i) / GW)

#define cidx(x, y) ((uint8_t)((y) * GW + (x)))
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

/* ---- entity lists ---- */
static void list_remove(uint8_t *list, uint8_t *n, uint8_t cell) {
    uint8_t k;
    for (k = 0; k < *n; k++) if (list[k] == cell) { list[k] = list[*n - 1]; (*n)--; return; }
}
static void set_cell(uint8_t i, uint8_t type) { G.grid[i] = type; DIRTY_CELL(i); }

static void add_angry(uint8_t i) {
    if (G.n_angry >= MAX_ANGRY) { set_cell(i, C_EMPTY); return; }
    set_cell(i, C_ANGRY); G.gstate[i] = A_IDLE; G.gtimer[i] = HOP_MIN + rnd(128);
    G.angry_list[G.n_angry++] = i;
}
static void remove_angry(uint8_t i) { set_cell(i, C_EMPTY); list_remove(G.angry_list, &G.n_angry, i); }
static void remove_flask(uint8_t i) { set_cell(i, C_EMPTY); list_remove(G.flask_list, &G.n_flask, i); }

/* random empty cell at least `mind` (manhattan) away from the player; 0xFF if none */
static uint8_t random_empty_cell(uint8_t mind) {
    uint8_t tries = 40, x, y, i;
    while (tries--) {
        x = rnd(GW); y = rnd(GH); i = cidx(x, y);
        if (G.grid[i] != C_EMPTY) continue;
        {
            uint8_t dx = x > G.px ? x - G.px : G.px - x;
            uint8_t dy = y > G.py ? y - G.py : G.py - y;
            if (dx + dy < mind) continue;
        }
        return i;
    }
    for (i = 0; i < NCELLS; i++) if (G.grid[i] == C_EMPTY && i != cidx(G.px, G.py)) return i;
    return 0xFF;
}

static void spawn(uint8_t type, uint8_t mind) {
    uint8_t i;
    if (G.n_appear >= MAX_APPEAR) return;
    i = random_empty_cell(mind);
    if (i == 0xFF) return;
    set_cell(i, type); G.gtimer[i] = APPEAR_FRAMES; G.gstate[i] = 0;
    G.appear_list[G.n_appear++] = i;
}

static void spawn_flask(uint8_t level) {
    uint8_t i;
    if (G.n_flask >= MAX_FLASK) return;
    i = random_empty_cell(2);
    if (i == 0xFF) return;
    set_cell(i, C_FLASK); G.gstate[i] = level; G.gtimer[i] = FLASK_UPGRADE;
    G.flask_list[G.n_flask++] = i;
}

static void relocate_star(void) {
    uint8_t r;
    do { r = rnd(GH); } while (r == G.star_row || r == G.py);
    DIRTY_ROW(G.star_row); DIRTY_ROW(r);
    G.star_row = r;
}

void game_init(void) {
    uint8_t i;
    for (i = 0; i < NCELLS; i++) { G.grid[i] = C_EMPTY; G.gstate[i] = 0; G.gtimer[i] = 0; }
    G.trail_len = 0; G.n_angry = 0; G.n_appear = 0; G.n_flask = 0; G.n_friend = 0;
    G.px = 5; G.py = 7; G.dir = D_UP; G.next_dir = D_NONE; G.sub = 0;
    G.jump = 0; G.anim = 0; G.drop_anim = 0; G.pending_grow = 0;
    G.star_row = 1;
    G.saved = 0; G.score = 0;
    G.flask_counter = 0; G.friend_target = FRIEND_BASE;
    G.power_timer = 0; G.power_tick = 0; G.power_mush = 0; G.mult = 1; G.chain = 0;
    G.angry_spawn_timer = ANGRY_SPAWN_MAX; G.mush_timer = MUSH_TIMEOUT; G.friend_timer = 1;
    G.slow_tick = 0;
    G.state = PS_READY; G.state_timer = READY_FRAMES;
    G.palette_set = 0; G.hud_dirty = 1; G.dirty_rows = 0xFFFF; G.flash = 0; G.turn_timer = 0; G.turn_pose = 0;
    G.best_drop = 0; G.best_chain = 0; G.total_kills = 0;
    /* initial loose oppies, already grown */
    for (i = 0; i < FRIEND_BASE; i++) {
        uint8_t c = random_empty_cell(3);
        if (c != 0xFF) { G.grid[c] = C_FRIEND; G.n_friend++; }
    }
}

static void die(void) {
    G.state = PS_DEAD; G.state_timer = 90; G.jump = 0;
    sfx_death();
}

static void power_expire(void) {
    G.power_timer = 0; G.mult = 1; G.chain = 0; G.power_mush = 0;
}

static void kill_enemy(uint8_t i) {
    if (G.grid[i] == C_ANGRY) remove_angry(i); else set_cell(i, C_EMPTY);
    sfx_kill();
    G.chain++;
    G.total_kills++;
    if (G.chain > G.best_chain) G.best_chain = G.chain;
    G.score += (uint32_t)10 * G.chain * G.mult;
    G.hud_dirty = 1;
}

static void pickup_flask(uint8_t i) {
    uint8_t level = G.gstate[i];
    remove_flask(i);
    sfx_flask();
    if (G.power_timer == 0) { G.chain = 0; G.mult = 1; G.power_mush = 0; }
    G.power_timer = POWER_UNITS; G.power_tick = POWER_TICK;
    if (level >= 1) G.mult++;
    if (level >= 2) G.power_mush = 1;
    if (level >= 3) G.friend_target++;
    G.hud_dirty = 1;
}

/* Resolve the contents of the cell the player is standing in (on entry while grounded, or on landing).
   Returns 1 if the player died. */
static uint8_t resolve_cell(uint8_t i, uint8_t *grew) {
    switch (G.grid[i]) {
    case C_FRIEND:
        set_cell(i, C_EMPTY); G.n_friend--; *grew = 1; sfx_pickup(); break;
    case C_TRAIL:
        /* the tail cell is about to be vacated, so entering it is safe */
        if (G.trail_len && i == G.trail[G.trail_len - 1]) break;
        die(); return 1;
    case C_ANGRY:
        if (G.power_timer) { kill_enemy(i); break; }
        die(); return 1;
    case C_MUSH:
        if (G.power_timer && G.power_mush) { kill_enemy(i); break; }
        die(); return 1;
    case C_FLASK:
        pickup_flask(i); break;
    default: break;
    }
    return 0;
}

static void advance_trail(uint8_t old_head, uint8_t grew) {
    uint8_t k;
    if (grew) {
        if (G.trail_len < MAX_TRAIL) G.trail_len++;
        else grew = 0;
    }
    if (G.trail_len == 0) return;
    if (!grew) {
        uint8_t tail = G.trail[G.trail_len - 1];
        if (G.grid[tail] == C_TRAIL) set_cell(tail, C_EMPTY);
    }
    for (k = G.trail_len - 1; k > 0; k--) G.trail[k] = G.trail[k - 1];
    G.trail[0] = old_head;
    set_cell(old_head, C_TRAIL);
}

static void step(void) {
    uint8_t old = cidx(G.px, G.py), ni, grew = 0;
    if (G.next_dir != D_NONE) {
        uint8_t vert = (G.dir == D_UP || G.dir == D_DOWN) ? G.dir : G.next_dir;
        uint8_t horiz = (G.dir == D_LEFT || G.dir == D_RIGHT) ? G.dir : G.next_dir;
        G.turn_pose = (vert == D_UP ? 1 : 0) | (horiz == D_RIGHT ? 2 : 0);
        G.turn_timer = TURN_FRAMES;
        G.dir = G.next_dir; G.next_dir = D_NONE;
    }
    ni = neighbor(G.px, G.py, G.dir);
    if (ni == 0xFF) { die(); return; }
    if (G.pending_grow) { G.pending_grow = 0; grew = 1; }
    if (G.jump) {
        /* airborne: skip contents, but stun an angry oppie we pass over */
        if (G.grid[ni] == C_ANGRY) { G.gstate[ni] = A_STUN; G.gtimer[ni] = STUN_FRAMES; DIRTY_CELL(ni); }
    } else {
        uint8_t g2 = 0;
        if (resolve_cell(ni, &g2)) return;
        grew |= g2;
    }
    /* the head leaves `old`; the trail follows */
    advance_trail(old, grew);
    G.px = ni % GW; G.py = ni / GW;
    /* if the new cell held a pending spawn, it is lost */
    if (G.grid[ni] >= C_APPEAR_FRIEND) { set_cell(ni, C_EMPTY); list_remove(G.appear_list, &G.n_appear, ni); }
}

static void do_drop(void) {
    uint8_t k, nsaved = 0, i;
    G.drop_anim = 16;
    if (G.trail_len == 0) return;
    for (k = 0; k < G.trail_len; k++) {
        i = G.trail[k];
        if (i / GW == G.star_row) {
            set_cell(i, C_EMPTY); nsaved++;
            G.score += (uint32_t)10 * (k + 1);
        } else add_angry(i);
    }
    G.trail_len = 0;
    G.hud_dirty = 1;
    if (nsaved == 0) { sfx_bad_drop(); return; }
    sfx_save();
    G.saved += nsaved;
    if (nsaved > G.best_drop) G.best_drop = nsaved;
    G.mush_timer = MUSH_TIMEOUT;
    /* flask counter */
    {
        uint8_t total = G.flask_counter + nsaved;
        if (total >= FLASK_NEEDED) {
            uint8_t level = total - FLASK_NEEDED;
            if (level > 3) level = 3;
            G.flask_counter = 0;
            spawn_flask(level);
        } else G.flask_counter = total;
    }
    G.palette_set = (uint8_t)(G.saved / 50);
    if (G.palette_set > 3) G.palette_set = 3;
    if (G.saved >= WIN_SAVED) { G.state = PS_WIN; G.state_timer = 120; sfx_win(); return; }
    relocate_star();
}

/* returns the (possibly new) cell of this angry oppie */
static uint8_t update_angry(uint8_t i) {
    uint8_t s = G.gstate[i], st = A_STATE(s);
    if (st == A_STUN) {
        if (--G.gtimer[i] == 0) { G.gstate[i] = A_IDLE; G.gtimer[i] = HOP_MIN + rnd(128); DIRTY_CELL(i); }
        return i;
    }
    if (st == A_IDLE) {
        if (--G.gtimer[i] == 0) { G.gstate[i] = A_LOOK | (rnd(4) << 2); G.gtimer[i] = LOOK_FRAMES; DIRTY_CELL(i); }
        return i;
    }
    /* A_LOOK */
    if (--G.gtimer[i] != 0) return i;
    {
        uint8_t d = A_DIR(s), tries = 4, x = i % GW, y = i / GW, pc = cidx(G.px, G.py);
        while (tries--) {
            uint8_t t = neighbor(x, y, d);
            if (t != 0xFF && G.grid[t] == C_EMPTY && t != pc) {
                set_cell(t, C_ANGRY); G.gstate[t] = A_IDLE; G.gtimer[t] = HOP_MIN + rnd(128);
                set_cell(i, C_EMPTY); G.gstate[i] = 0;
                return t;
            }
            d = (d + 1) & 3;
        }
        G.gstate[i] = A_IDLE; G.gtimer[i] = 30; DIRTY_CELL(i);
        return i;
    }
}

static void update_entities(void) {
    uint8_t k, i;
    for (k = 0; k < G.n_angry; k++) G.angry_list[k] = update_angry(G.angry_list[k]);
    for (k = 0; k < G.n_appear; ) {
        i = G.appear_list[k];
        {
            uint8_t t = --G.gtimer[i];
            if (t == 26 || t == 13) DIRTY_CELL(i);
            if (t != 0) { k++; continue; }
        }
        /* finished growing: remove from the appear list first (add_angry may append elsewhere) */
        G.appear_list[k] = G.appear_list[--G.n_appear];
        switch (G.grid[i]) {
        case C_APPEAR_FRIEND: set_cell(i, C_FRIEND); G.n_friend++; break;
        case C_APPEAR_ANGRY:  add_angry(i); break;
        case C_APPEAR_MUSH:   set_cell(i, C_MUSH); break;
        default: break;
        }
    }
    if (G.slow_tick == 0) {
        for (k = 0; k < G.n_flask; k++) {
            i = G.flask_list[k];
            if (G.gstate[i] < 3 && --G.gtimer[i] == 0) { G.gstate[i]++; G.gtimer[i] = FLASK_UPGRADE; }
        }
    }
}

static void update_spawners(void) {
    /* friendly oppies */
    if (--G.friend_timer == 0) {
        uint8_t k, n = G.n_friend;
        G.friend_timer = 45;
        for (k = 0; k < G.n_appear; k++) if (G.grid[G.appear_list[k]] == C_APPEAR_FRIEND) n++;
        if (n < G.friend_target) spawn(C_APPEAR_FRIEND, 3);
    }
    /* passive angry spawns, faster as the run progresses */
    if (--G.angry_spawn_timer == 0) {
        uint16_t t = ANGRY_SPAWN_MAX - (G.saved << 1);
        if (t < ANGRY_SPAWN_MIN || t > ANGRY_SPAWN_MAX) t = ANGRY_SPAWN_MIN;
        G.angry_spawn_timer = t;
        spawn(C_APPEAR_ANGRY, 4);
    }
    /* the witch */
    if (--G.mush_timer == 0) {
        uint8_t n = 1;
        if (G.saved >= 100) n++;
        if (G.saved >= 150) n++;
        G.mush_timer = MUSH_TIMEOUT;
        sfx_spawn();
        while (n--) spawn(C_APPEAR_MUSH, 3);
    }
}

void game_update(uint8_t joy, uint8_t pressed) {
    if (G.state == PS_DEAD || G.state == PS_WIN) {
        if (G.state_timer) G.state_timer--;
        return;
    }
    if (G.state == PS_READY) {
        if (--G.state_timer == 0) G.state = PS_PLAY;
        (void)joy; (void)pressed;
        return;
    }
    G.slow_tick = (G.slow_tick + 1) & 3;
    /* input: any perpendicular direction that is newly pressed (preferred) or held queues a turn for the
       next cell boundary. Reading held directions too means a d-pad roll (Up still held while Left goes
       down) is never dropped. */
    {
        static const uint8_t jbit[4] = { J_UP, J_RIGHT, J_DOWN, J_LEFT };
        uint8_t d, want = D_NONE, opp = (G.dir + 2) & 3;
        for (d = 0; d < 4; d++) if (d != G.dir && d != opp && (pressed & jbit[d])) want = d;
        if (want == D_NONE) for (d = 0; d < 4; d++) if (d != G.dir && d != opp && (joy & jbit[d])) want = d;
        if (want != D_NONE) G.next_dir = want;
    }
    if ((pressed & J_A) && G.jump == 0) { G.jump = JUMP_FRAMES; sfx_jump(); }
    if (pressed & J_B) do_drop();
    if (G.state != PS_PLAY) return;

    /* movement first, then the jump countdown: a jump started at any point inside a cell
       skips the next cell entered and lands in the one after it */
    G.sub++;
    if (G.sub >= CELL_FRAMES) {
        G.sub = 0;
        step();
        if (G.state != PS_PLAY) return;
        G.anim ^= 1;
    }
    if (G.jump) {
        G.jump--;
        if (G.jump == 0) {
            uint8_t grew = 0;
            if (resolve_cell(cidx(G.px, G.py), &grew)) return;
            if (grew) G.pending_grow = 1; /* landed on a loose oppie: joins the tail on the next step */
        }
    }
    if (G.drop_anim) G.drop_anim--;
    if (G.turn_timer) G.turn_timer--;

    update_entities();
    update_spawners();

    /* vulnerable enemies flash blue/white every 6 frames while a flask is active */
    {
        uint8_t f = G.power_timer ? ((G.frame_count / 6) & 1) : 0;
        if (f != G.flash) { G.flash = f; G.dirty_rows = 0xFFF; }
    }
    /* power timer */
    if (G.power_timer) {
        if (--G.power_tick == 0) {
            G.power_tick = POWER_TICK;
            if (--G.power_timer == 0) power_expire();
            else if (G.power_timer <= 8) sfx_tick();
            G.hud_dirty = 1;
        }
    }
}
