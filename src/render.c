#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"

static uint8_t cur_set = 0xFF;
#define MAX_ROWS_PER_FRAME 4
static uint8_t rowbuf_t[MAX_ROWS_PER_FRAME][GW], rowbuf_a[MAX_ROWS_PER_FRAME][GW], rowbuf_y[MAX_ROWS_PER_FRAME], n_rows;
static uint8_t hud_ready, hud_saved[3], hud_score[6], hud_dots[5], hud_timer[2], hud_mult[2], pal_pending;

static uint8_t font_tile(char ch) {
    if (ch >= '0' && ch <= '9') return FONT_FIRST + (ch - '0');
    if (ch >= 'A' && ch <= 'Z') return FONT_FIRST + 10 + (ch - 'A');
    switch (ch) {
    case '-': return FONT_FIRST + 36;
    case '!': return FONT_FIRST + 37;
    case '.': return FONT_FIRST + 38;
    case '\'': return FONT_FIRST + 39;
    case ',': return FONT_FIRST + 40;
    case 'x': return FONT_FIRST + 41;
    default: return FONT_FIRST + 42;
    }
}

void hud_text(uint8_t x, uint8_t y, const char *s) {
    uint8_t buf[20], n = 0;
    while (*s && n < 20) buf[n++] = font_tile(*s++);
    set_bkg_tiles(x, y, n, 1, buf);
    VBK_REG = 1;
    memset(buf, 7, n);
    set_bkg_tiles(x, y, n, 1, buf);
    VBK_REG = 0;
}

void hud_number(uint8_t x, uint8_t y, uint32_t v, uint8_t digits) {
    uint8_t buf[8], i;
    for (i = digits; i > 0; i--) { buf[i - 1] = FONT_FIRST + (uint8_t)(v % 10); v /= 10; }
    set_bkg_tiles(x, y, digits, 1, buf);
}

void render_init(void) {
    uint8_t i;
    LCDC_REG |= LCDCF_BG8000;
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    set_sprite_data(BG_BASE, BG_TILE_COUNT, bg_tiles);   /* BG tiles share the 0x8000 space */
    set_bkg_tiles(0, 0, 20, 18, frame_map);
    VBK_REG = 1;
    set_bkg_tiles(0, 0, 20, 18, frame_attr);
    VBK_REG = 0;
    SPRITES_8x16;
    for (i = 0; i < 40; i++) { set_sprite_tile(i, 0); move_sprite(i, 0, 0); }
    set_sprite_prop(0, 0);
    set_sprite_tile(1, SPR_SHADOW); set_sprite_prop(1, 5);
    cur_set = 0xFF;
    G.hud_dirty = 1;
}

/* rebuild one playfield row from the grid into the pending row buffers */
static void prepare_row(uint8_t y) {
    uint8_t *tb = rowbuf_t[n_rows], *ab = rowbuf_a[n_rows];
    uint8_t x, i = y * GW;
    rowbuf_y[n_rows++] = y;
    uint8_t onstar = (y == G.star_row);
    uint8_t floor_t = onstar ? T_STAR : T_FLOOR;
    uint8_t pal = onstar ? 4 : (y & 1);
    uint8_t blue_add = onstar ? 1 : 2;
    for (x = 0; x < GW; x++, i++) {
        uint8_t g = G.grid[i], t = floor_t, a = pal;
        if (g != C_EMPTY) {
            uint8_t s = G.gstate[i];
            switch (g) {
            case C_FRIEND: t = T_OPPIE; break;
            case C_TRAIL:  t = T_OPPIE_HAPPY; break;
            case C_ANGRY:
                a += blue_add;
                if (A_STATE(s) == A_STUN) t = T_OPPIE_STUN;
                else if (A_STATE(s) == A_LOOK) {
                    switch (A_DIR(s)) {
                    case D_UP: t = T_OPPIE_LOOK_U; break;
                    case D_DOWN: t = T_OPPIE_LOOK_D; break;
                    case D_LEFT: t = T_OPPIE_LOOK_L; break;
                    default: t = T_OPPIE_LOOK_L; a |= S_FLIPX; break;
                    }
                } else t = T_OPPIE;
                break;
            case C_MUSH: a += blue_add; t = T_MUSH; break;
            case C_APPEAR_ANGRY: a += blue_add; /* fallthrough */
            case C_APPEAR_FRIEND: {
                uint8_t tm = G.gtimer[i];
                t = tm > 26 ? T_APPEAR0 : (tm > 13 ? T_APPEAR1 : T_APPEAR2);
                break; }
            case C_APPEAR_MUSH: a += blue_add; t = T_MUSH_APPEAR; break;
            default: break;
            }
        }
        tb[x] = t; ab[x] = a;
        if (!onstar) pal ^= 1;
    }
}

/* pick up to MAX_ROWS_PER_FRAME dirty rows; the rest stay flagged for later frames */
static void prepare_grid(void) {
    uint8_t y;
    uint16_t m = G.dirty_rows, bit = 1;
    n_rows = 0;
    if (!m) return;
    for (y = 0; y < GH && n_rows < MAX_ROWS_PER_FRAME; y++, bit <<= 1)
        if (m & bit) { prepare_row(y); G.dirty_rows &= ~bit; }
}

static void flush_rows(void) {
    uint8_t k;
    for (k = 0; k < n_rows; k++) {
        set_bkg_tiles(MAP_X, MAP_Y + rowbuf_y[k], GW, 1, rowbuf_t[k]);
        VBK_REG = 1;
        set_bkg_tiles(MAP_X, MAP_Y + rowbuf_y[k], GW, 1, rowbuf_a[k]);
        VBK_REG = 0;
    }
    n_rows = 0;
}

/* full redraw with the LCD off (used when a game starts) */
void render_grid_full(void) {
    G.dirty_rows = 0xFFF;
    while (G.dirty_rows) { prepare_grid(); flush_rows(); }
}

static void draw_sprites(void) {
    uint8_t tile, sx, sy, i, n = 2, lift = 0;
    int8_t off = (int8_t)((G.sub * 8) / CELL_FRAMES);
    sx = ORG_X + G.px * 8; sy = ORG_Y + G.py * 8 - 8;
    switch (G.dir) {
    case D_UP: sy -= off; tile = G.anim ? SPR_UP1 : SPR_UP0; break;
    case D_DOWN: sy += off; tile = G.anim ? SPR_DOWN1 : SPR_DOWN0; break;
    case D_LEFT: sx -= off; tile = G.anim ? SPR_LEFT1 : SPR_LEFT0; break;
    default: sx += off; tile = G.anim ? SPR_RIGHT1 : SPR_RIGHT0; break;
    }
    if (G.state == PS_READY || G.drop_anim) tile = (G.drop_anim & 4) ? SPR_SPIN : SPR_DOWN0;
    if (G.jump) {
        /* parabolic lift, peak 10 px at mid-jump */
        uint8_t t = G.jump > JUMP_FRAMES / 2 ? JUMP_FRAMES - G.jump : G.jump; /* 0..12 */
        lift = (uint8_t)((t * 10) / (JUMP_FRAMES / 2));
        move_sprite(1, sx + 8, sy + 16);
    } else move_sprite(1, 0, 0);
    if (G.state == PS_DEAD && (G.state_timer & 4)) { move_sprite(0, 0, 0); }
    else { set_sprite_tile(0, tile); move_sprite(0, sx + 8, sy + 16 - lift); }
    /* flasks as sprites */
    for (i = 0; i < G.n_flask; i++, n++) {
        uint8_t c = G.flask_list[i];
        set_sprite_tile(n, SPR_FLASK); set_sprite_prop(n, 1 + G.gstate[c]);
        move_sprite(n, ORG_X + (c % GW) * 8 + 8, ORG_Y + (c / GW) * 8 - 8 + 16);
    }
    for (; n < 10; n++) move_sprite(n, 0, 0);
}

static void digits(uint8_t *out, uint32_t v, uint8_t n) {
    while (n--) { out[n] = FONT_FIRST + (uint8_t)(v % 10); v /= 10; }
}
static void hud_prepare(void) {
    uint8_t i;
    digits(hud_saved, G.saved, 3);
    digits(hud_score, G.score, 6);
    for (i = 0; i < 5; i++) hud_dots[i] = (i < G.flask_counter) ? T_DOT_ON : T_DOT_OFF;
    if (G.power_timer) {
        digits(hud_timer, G.power_timer, 2);
        if (G.mult > 1) { hud_mult[0] = font_tile('x'); hud_mult[1] = FONT_FIRST + (G.mult % 10); }
        else hud_mult[0] = hud_mult[1] = T_PANEL;
    } else { hud_timer[0] = hud_timer[1] = T_PANEL; hud_mult[0] = hud_mult[1] = T_PANEL; }
    hud_ready = 1;
}
static void hud_flush(void) {
    if (!hud_ready) return;
    hud_ready = 0;
    set_bkg_tiles(2, 16, 3, 1, hud_saved);
    set_bkg_tiles(12, 16, 6, 1, hud_score);
    set_bkg_tiles(7, 17, 5, 1, hud_dots);
    set_bkg_tiles(9, 1, 2, 1, hud_timer);
    set_bkg_tiles(13, 17, 2, 1, hud_mult);
}
void hud_draw_all(void) { hud_prepare(); hud_flush(); }

/* Phase 1 (any time in the frame): compute everything, touch only shadow OAM and RAM buffers. */
void render_prepare(void) {
    if (cur_set != G.palette_set) { cur_set = G.palette_set; pal_pending = 1; }
    prepare_grid();
    draw_sprites();
    if (G.hud_dirty) { G.hud_dirty = 0; hud_prepare(); }
}
/* Phase 2 (right after wait_vbl_done): VRAM + palette writes only. */
void render_flush(void) {
    if (pal_pending) { pal_pending = 0; palettes_apply(cur_set); }
    flush_rows();
    hud_flush();
}

