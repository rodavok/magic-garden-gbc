#ifndef GAME_H
#define GAME_H
#include <stdint.h>

/* ---- playfield geometry ---- */
#define GW 12
#define GH 12
#define NCELLS 144
#define MAP_X 4            /* tile column of playfield in the 20x18 map */
#define MAP_Y 3
#define ORG_X 32           /* pixel origin of playfield */
#define ORG_Y 24

/* ---- tuning (all "unknown" values from the brief live here) ---- */
#define CELL_FRAMES      12   /* frames to cross one cell (5 cells/s) */
#define JUMP_FRAMES      24   /* airborne time: clears exactly one cell */
#define MAX_TRAIL        48
#define MAX_ANGRY        64
#define MAX_APPEAR       8
#define MAX_FLASK        6
#define FRIEND_BASE      3    /* loose friendly oppies kept on the field */
#define APPEAR_FRAMES    40
#define LOOK_FRAMES      20
#define STUN_FRAMES      180
#define HOP_MIN          60
#define ANGRY_SPAWN_MAX  600  /* frames between passive angry spawns at start */
#define ANGRY_SPAWN_MIN  240
#define MUSH_TIMEOUT     1200 /* frames without a save before the witch acts */
#define FLASK_NEEDED     6
#define FLASK_UPGRADE    120  /* slow ticks (x4 frames) per flask level gained on the floor */
#define POWER_UNITS      48
#define POWER_TICK       10   /* frames per timer unit -> 8 s */
#define WIN_SAVED        200
#define READY_FRAMES     60

/* ---- cell contents ---- */
enum { C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK, C_APPEAR_FRIEND, C_APPEAR_ANGRY, C_APPEAR_MUSH };
/* angry oppie state (gstate low bits); look dir in bits 2-3 */
enum { A_IDLE, A_LOOK, A_STUN };
#define A_STATE(s)  ((s) & 3)
#define A_DIR(s)    (((s) >> 2) & 3)
/* directions */
enum { D_UP, D_RIGHT, D_DOWN, D_LEFT, D_NONE = 0xFF };
/* play sub-states */
enum { PS_READY, PS_PLAY, PS_DEAD, PS_WIN };

typedef struct {
    uint8_t grid[NCELLS];      /* cell type */
    uint8_t gstate[NCELLS];    /* angry: state; flask: level */
    uint8_t gtimer[NCELLS];    /* angry / appear / flask timers */
    uint8_t trail[MAX_TRAIL];
    uint8_t angry_list[MAX_ANGRY];
    uint8_t appear_list[MAX_APPEAR];
    uint8_t flask_list[MAX_FLASK];
    uint8_t trail_len, n_angry, n_appear, n_flask, n_friend;

    uint8_t px, py, dir, next_dir, sub;
    uint8_t jump;         /* frames airborne remaining */
    uint8_t pending_grow;
    uint8_t anim;
    uint8_t drop_anim;
    uint8_t star_row;

    uint16_t saved;
    uint32_t score;
    uint8_t flask_counter;
    uint8_t friend_target;
    uint8_t power_timer, power_tick, power_mush, mult, chain;
    uint16_t angry_spawn_timer, mush_timer;
    uint8_t friend_timer;
    uint8_t slow_tick;
    uint8_t state;
    uint8_t state_timer;
    uint8_t palette_set;
    uint8_t hud_dirty;
    uint16_t dirty_rows;  /* bit per playfield row needing a redraw */
    /* stats */
    uint8_t best_drop, best_chain;
    uint16_t total_kills;
    uint16_t frame_count;
    uint8_t dbg[6];
} game_t;

extern game_t G;

void game_init(void);
void game_update(uint8_t joy, uint8_t pressed);
/* render.c */
void render_init(void);
void render_prepare(void);
void render_flush(void);
void render_grid_full(void);
void hud_text(uint8_t x, uint8_t y, const char *s);
void hud_number(uint8_t x, uint8_t y, uint32_t v, uint8_t digits);
void hud_draw_all(void);
/* palettes.c */
void palettes_apply(uint8_t set);

#endif
