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

/* write text into a 20-wide RAM screen buffer (no VRAM access) */
void map_text(uint8_t *buf, uint8_t x, uint8_t y, const char *s) {
    uint8_t *p = buf + y * 20 + x;
    while (*s) *p++ = font_tile(*s++);
}

/* Copy a full 20x18 screen (tiles + attributes; attr == NULL means palette 7 everywhere) to VRAM,
   two rows per VBlank, with the LCD left on. Safe on hardware and on emulators that mishandle LCD-off writes. */
void vram_draw_map(const uint8_t *map, const uint8_t *attr) {
    uint8_t y, a7[40];
    memset(a7, 7, 40);
    for (y = 0; y < 18; y += 2) {
        wait_vbl_done();
        set_bkg_tiles(0, y, 20, 2, map + y * 20);
        VBK_REG = 1;
        set_bkg_tiles(0, y, 20, 2, attr ? attr + y * 20 : a7);
        VBK_REG = 0;
    }
}

void hud_text(uint8_t x, uint8_t y, const char *s) {
    uint8_t buf[20], n = 0;
    while (*s && n < 20) buf[n++] = font_tile(*s++);
    if (n == 0) return;   /* a zero width would underflow to 256 tiles in set_bkg_tiles */
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
    SPRITES_8x16;
    for (i = 0; i < 40; i++) { set_sprite_tile(i, 0); move_sprite(i, 0, 0); }
    vram_draw_map(frame_map, frame_attr);
    set_sprite_prop(0, 0); set_sprite_prop(1, 0);
    set_sprite_tile(2, SPR_SHADOW); set_sprite_prop(2, 5);
    cur_set = 0xFF;
    G.hud_dirty = 1;
}

/* rebuild one playfield row from the grid into the pending row buffers */
static void prepare_row(uint8_t y) {
    uint8_t *tb = rowbuf_t[n_rows], *ab = rowbuf_a[n_rows];
    uint8_t x, i = y * GW;
    uint16_t pad = G.pad_rows[y];
    uint8_t pad_visible = G.pad_flash ? ((G.pad_flash / 5) & 1) : 1;
    uint8_t star_t = (G.pad_anim < PAD_TWINKLE / 2) ? T_STAR : T_STAR2;
    rowbuf_y[n_rows++] = y;
    for (x = 0; x < GW; x++, i++, pad >>= 1) {
        uint8_t g = G.grid[i], onstar = (uint8_t)(pad & 1) && pad_visible;
        uint8_t pal = onstar ? 4 : ((x + y) & 1), blue_add = onstar ? 1 : 2;
        uint8_t t = onstar ? star_t : T_FLOOR, a = pal;
        if (g != C_EMPTY) {
            uint8_t st = G.gstate[i];
            switch (g) {
            case C_FRIEND: t = T_OPPIE; break;
            case C_TRAIL:  t = T_OPPIE_HAPPY; break;
            case C_ANGRY:
                if (A_STATE(st) == A_HOP && (st & A_SPRITE)) break;   /* drawn as a sprite while hopping */
                a += blue_add;
                if (A_STATE(st) == A_STUN) t = G.flash ? T_OPPIE_STUN_W : T_OPPIE_STUN;
                else if (A_STATE(st) == A_LOOK) {
                    switch (A_DIR(st)) {
                    case D_UP: t = G.flash ? T_OPPIE_LOOK_U_W : T_OPPIE_LOOK_U; break;
                    case D_DOWN: t = G.flash ? T_OPPIE_LOOK_D_W : T_OPPIE_LOOK_D; break;
                    case D_LEFT: t = G.flash ? T_OPPIE_LOOK_L_W : T_OPPIE_LOOK_L; break;
                    default: t = G.flash ? T_OPPIE_LOOK_L_W : T_OPPIE_LOOK_L; a |= S_FLIPX; break;
                    }
                } else t = G.flash ? T_OPPIE_W : T_OPPIE;
                break;
            case C_MUSH: a += blue_add; t = (G.flash && G.power_mush) ? T_MUSH_W : T_MUSH; break;
            case C_APPEAR_ANGRY: {
                uint8_t lv = (uint8_t)((APPEAR_FRAMES - G.gtimer[i]) / 60);
                a += blue_add;
                t = lv == 0 ? T_APPEAR0 : (lv == 1 ? T_APPEAR1 : (lv == 2 ? T_APPEAR2 : T_OPPIE));
                break; }
            case C_APPEAR_MUSH: {
                uint8_t lv = (uint8_t)((APPEAR_FRAMES - G.gtimer[i]) / 60);
                a += blue_add;
                t = lv == 0 ? T_APPEAR0 : (lv == 1 ? T_APPEAR1 : (lv == 2 ? T_MUSH_APPEAR : T_MUSH));
                break; }
            default: break;
            }
        }
        tb[x] = t; ab[x] = a;
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

/* Straight copies into the tile map during VBlank (GBDK's set_bkg_tiles is several times slower). */
static void flush_rows(void) {
    uint8_t k;
    for (k = 0; k < n_rows; k++) {
        uint8_t *dst = (uint8_t *)(0x9800 + ((uint16_t)(MAP_Y + rowbuf_y[k]) << 5) + MAP_X);
        memcpy(dst, rowbuf_t[k], GW);
        VBK_REG = 1;
        memcpy(dst, rowbuf_a[k], GW);
        VBK_REG = 0;
    }
    n_rows = 0;
}

/* full redraw in VBlank chunks (used when a game starts) */
void render_grid_full(void) {
    G.dirty_rows = 0xFFF;
    while (G.dirty_rows) { prepare_grid(); wait_vbl_done(); flush_rows(); }
}

static void draw_sprites(void) {
    uint8_t tile, prop = 0, sx, sy, i, n = 3, lift = 0, dir = G.dir;
    uint8_t off = G.sub >> 1;
    uint8_t anim = (G.state == PS_PLAY) ? (uint8_t)((G.frame_count / 4) & 3) : 0;
    sx = ORG_X + G.px * 8; sy = ORG_Y + G.py * 8 - 16;   /* 24 px tall, feet in the cell */
    switch (dir) {
    case D_UP: sy -= off; break;
    case D_DOWN: sy += off; break;
    case D_LEFT: sx -= off; break;
    default: sx += off; break;
    }
    if (G.drop_anim) { dir = (G.drop_anim >> 2) & 3; anim = 0; }          /* spin: down, right, up, left */
    if (G.turn_timer && !G.drop_anim && G.state == PS_PLAY) {
        tile = (G.turn_pose & 1) ? SPR_DIAGUP : SPR_DIAGDOWN;
        if (G.turn_pose & 2) prop = S_FLIPX;
    } else {
        switch (dir) {
        case D_UP: tile = SPR_UP0; break;
        case D_DOWN: tile = SPR_DOWN0; break;
        case D_LEFT: tile = SPR_LEFT0; break;
        default: tile = SPR_LEFT0; prop = S_FLIPX; break;
        }
        tile += anim * 4;
    }
    if (G.z) {
        lift = G.z / 20;                       /* tenths of a unit -> pixels */
        move_sprite(2, sx + 8, sy + 16 + 16);  /* shadow at the feet */
    } else move_sprite(2, 0, 0);
    if (G.state == PS_DEAD && (G.state_timer & 4)) { move_sprite(0, 0, 0); move_sprite(1, 0, 0); }
    else {
        set_sprite_tile(0, tile); set_sprite_prop(0, prop); move_sprite(0, sx + 8, sy + 16 - lift);
        set_sprite_tile(1, tile + 2); set_sprite_prop(1, prop); move_sprite(1, sx + 8, sy + 32 - lift);
    }
    /* hopping angry oppies */
    for (i = 0; i < G.n_angry && n < 3 + MAX_HOP_SPRITES; i++) {
        uint8_t c = G.angry_list[i], st = G.gstate[c];
        if (A_STATE(st) == A_HOP && (st & A_SPRITE)) {
            uint8_t hx = ORG_X + (c % GW) * 8, hy = ORG_Y + (c / GW) * 8, back = G.gtimer[c] >> 1;
            uint8_t arc = G.gtimer[c] < 8 ? G.gtimer[c] : 16 - G.gtimer[c];   /* small hop arc */
            switch (A_DIR(st)) {
            case D_UP: hy += back; break;
            case D_DOWN: hy -= back; break;
            case D_LEFT: hx += back; break;
            default: hx -= back; break;
            }
            set_sprite_tile(n, SPR_OPPIE); set_sprite_prop(n, 7);
            move_sprite(n, hx + 8, hy - 8 + 16 - (arc >> 1));
            n++;
        }
    }
    for (; n < 3 + MAX_HOP_SPRITES; n++) move_sprite(n, 0, 0);
    /* flasks (falling ones are drawn above their cell) */
    for (i = 0; i < G.n_flask; i++, n++) {
        uint8_t c = G.flask_list[i];
        set_sprite_tile(n, SPR_FLASK); set_sprite_prop(n, 1 + G.gstate[c]);
        move_sprite(n, ORG_X + (c % GW) * 8 + 8, ORG_Y + (c / GW) * 8 - 8 + 16 - (G.flask_fall[i] >> 1));
    }
    for (; n < 3 + MAX_HOP_SPRITES + MAX_FLASK; n++) move_sprite(n, 0, 0);
}

/* decimal digits by repeated subtraction: no 32-bit division (SDCC's is very slow) */
static const uint32_t pow10[6] = { 100000UL, 10000UL, 1000UL, 100UL, 10UL, 1UL };
static void digits(uint8_t *out, uint32_t v, uint8_t n) {
    uint8_t k, d;
    for (k = 6 - n; k < 6; k++) {
        uint32_t p = pow10[k];
        for (d = 0; v >= p && d < 9; d++) v -= p;
        *out++ = FONT_FIRST + d;
    }
}
static void hud_prepare(void) {
    uint8_t i;
    digits(hud_saved, G.saved, 3);
    digits(hud_score, G.score, 6);
    for (i = 0; i < 5; i++) hud_dots[i] = (i < G.flask_counter) ? T_DOT_ON : T_DOT_OFF;
    if (G.power_timer) {
        digits(hud_timer, (G.power_timer + 9) / 10, 2);
        if (G.mult > 1) { hud_mult[0] = font_tile('x'); hud_mult[1] = FONT_FIRST + (G.mult % 10); }
        else hud_mult[0] = hud_mult[1] = T_PANEL;
    } else { hud_timer[0] = hud_timer[1] = T_BRICK; hud_mult[0] = hud_mult[1] = T_PANEL; }
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
void hud_draw_all(void) { hud_prepare(); wait_vbl_done(); hud_flush(); }

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

