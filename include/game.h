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

/* ---- original game constants (UFO 50 Magic Garden, 60 fps, 16-unit cells; 1 unit = 1/2 GBC pixel) ---- */
#define CELL_UNITS       16   /* frames to cross one cell at 1 unit/frame */
#define LATE_TURN        2    /* a new direction chosen within this many units of a boundary snaps back to it */
#define JUMP_Z0          10   /* z in tenths at take-off */
#define JUMP_V0          15   /* z velocity in tenths, minus 1 per frame: airborne 30 frames */
#define MAX_TRAIL        48
#define MAX_ANGRY        64
#define MAX_APPEAR       12
#define MAX_FLASK        6
#define MAX_HOP_SPRITES  6
#define FRIEND_BASE      2    /* loose friendly oppies on the field; +1 per gold flask */
#define APPEAR_FRAMES    240  /* enemies and mushrooms take 4 x 60 frames to grow */
#define ENEMY_IDLE       128  /* idle countdown; it turns to look at 64 and hops at 0 */
#define ENEMY_LOOK_AT    64
#define ENEMY_HOP        16   /* frames to hop one cell */
#define ENEMY_IDLE_AFTER_POWER 120
#define STUN_FRAMES      240
#define ENEMY_SPAWN      240  /* passive angry spawn period (paused while a flask is active) */
#define PAD_LIFE         960  /* star pad lifetime; expiring unused summons mushrooms */
#define PAD_FLASH        40   /* pad flash after a save before the next pad appears */
#define PAD_TWINKLE      20
#define POTION_DELAY     60   /* frames from the save until the flask drops in */
#define POTION_FALL      90   /* units the flask falls before it can be picked up */
#define FLASK_NEEDED     6
#define FLASK_UPGRADE    128  /* slow ticks (x4 frames = 512) per level gained on the floor */
#define POWER_FRAMES     480  /* flask duration; the HUD shows it in tenths */
#define WIN_SAVED        200

/* collision boxes in units, relative to the cell origin */
#define PLAYER_LO 1
#define PLAYER_HI 14
#define ENEMY_LO  4
#define ENEMY_HI  11

/* ---- cell contents ---- */
enum { C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK, C_APPEAR_ANGRY, C_APPEAR_MUSH, C_CLEARING };
#define MAX_POPS 6
typedef struct { uint8_t x, y, t; uint16_t val; } pop_t;
/* angry oppie state (gstate bits 0-1); look/hop dir in bits 2-3; bit 6: rendered as a hop sprite */
enum { A_IDLE, A_LOOK, A_HOP, A_STUN };
#define A_STATE(s)  ((s) & 3)
#define A_DIR(s)    (((s) >> 2) & 3)
#define A_SPRITE    0x40
/* directions */
enum { D_UP, D_RIGHT, D_DOWN, D_LEFT, D_NONE = 0xFF };
/* play sub-states */
enum { PS_WAIT, PS_PLAY, PS_DEAD, PS_WIN };

typedef struct {
    uint8_t grid[NCELLS];      /* cell type */
    uint8_t gstate[NCELLS];    /* angry: state; flask: level */
    uint8_t gtimer[NCELLS];    /* angry / appear / flask timers */
    uint8_t trail[MAX_TRAIL];
    uint8_t angry_list[MAX_ANGRY];
    uint8_t appear_list[MAX_APPEAR];
    uint8_t flask_list[MAX_FLASK];
    uint8_t flask_fall[MAX_FLASK];   /* units still to fall; 0 = on the floor */
    uint8_t trail_len, n_angry, n_appear, n_flask, n_friend, hop_sprites;
    uint8_t clear_n, clear_k, clear_timer;   /* drop-off cascade: one segment every 10 frames */
    pop_t pops[MAX_POPS];
    uint8_t pop_dirty;         /* bit per pop-up whose tiles need composing */

    uint8_t px, py, dir, dir_choice, sub;
    uint8_t turned;
    uint8_t z;            /* height in tenths of a unit; 0 = grounded */
    int8_t zvel;
    uint8_t pending_grow;
    uint8_t drop_anim;
    uint8_t turn_timer, turn_pose;

    uint16_t pad_rows[GH];     /* star pad cells, one bit per column */
    uint16_t pad_life;
    uint8_t pad_flash;         /* frames of victory flash left (pad no longer counts) */
    uint8_t pad_last_size;
    uint8_t pad_anim;

    uint16_t saved;
    uint32_t score;
    uint8_t flask_counter;
    uint8_t friend_target;
    uint8_t potion_delay, potion_type;
    uint16_t power_timer;
    uint8_t power_mush, mult, chain;
    uint16_t angry_spawn_timer;
    uint8_t slow_tick;
    uint8_t state;
    uint8_t state_timer;
    uint8_t palette_set;
    uint8_t hud_dirty;
    uint16_t dirty_rows;
    uint8_t flash;
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
void map_text(uint8_t *buf, uint8_t x, uint8_t y, const char *s);
void vram_draw_map(const uint8_t *map, const uint8_t *attr);
void hud_number(uint8_t x, uint8_t y, uint32_t v, uint8_t digits);
void hud_draw_all(void);
/* palettes.c */
void palettes_apply(uint8_t set);
void palettes_title(void);

#endif
