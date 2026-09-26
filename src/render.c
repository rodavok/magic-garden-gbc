#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"

static uint8_t cur_set = 0xFF;
#define MAX_ROWS_PER_FRAME 4
static uint8_t rowbuf_t[MAX_ROWS_PER_FRAME][GW], rowbuf_a[MAX_ROWS_PER_FRAME][GW], rowbuf_y[MAX_ROWS_PER_FRAME], n_rows;
static uint8_t hud_ready, hud_saved[6], hud_score[16], hud_flask[4], hud_timer[2], hud_mult[3], pal_pending;
static uint8_t meter_last, hud_col_want, hud_col_have;
/* plaque + flask-liquid colour (BG palette 7 entry 3): pink, or the colour of a flask on its way */
static const uint16_t hud_colors[5] = { RGB8(254,98,110), RGB8(254,98,110), RGB8(164,240,34), RGB8(39,186,219), RGB8(232,234,74) };

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

/* Sidebar characters live in the last object slots (the lowest priority: if a line ever holds more than
   ten objects they drop out, never a gameplay sprite). The cat and the witch never share a scanline. */
#define SLOT_CAT   33
#define SLOT_WITCH 36
#define CAT_X 4
#define CAT_Y 67
#define WITCH_X 136
#define WITCH_Y 30
static uint8_t witch_frame, witch_tick, cat_frame;
/* The cat yawns awake while a new flask is on its way (potion_delay: made, not yet dropped in). */
static void draw_cat(void) {
    uint8_t f = G.potion_delay ? 1 : 0, k, t;
    if (f == cat_frame) return;
    cat_frame = f;
    t = f ? SPR_CAT_YAWN0 : SPR_CAT0;
    for (k = 0; k < 3; k++, t += 2) set_sprite_tile(SLOT_CAT + k, t);
}
/* The original's bgWitch: she zaps (two frames, 10 each) while a mushroom grows and jumps for joy when the
   gardener dies. The appear list is at most 12 entries, and tiles are only rewritten when the frame changes. */
static void draw_witch(void) {
    uint8_t f = 0, k, t;
    if (++witch_tick >= 20) witch_tick = 0;
    if (G.state == PS_DEAD) f = 3;
    else for (k = 0; k < G.n_appear; k++) if (G.grid[G.appear_list[k]] == C_APPEAR_MUSH) { f = 1; break; }
    if (f && witch_tick >= 10) f++;
    if (f == witch_frame) return;
    witch_frame = f;
    t = SPR_WITCH0_0 + (f << 3);
    for (k = 0; k < 4; k++, t += 2) set_sprite_tile(SLOT_WITCH + k, t);
}

void render_init(void) {
    uint8_t i;
    SPRITES_8x16;
    for (i = 0; i < 40; i++) { set_sprite_tile(i, 0); move_sprite(i, 0, 0); }
    vram_draw_map(frame_map, frame_attr);
    set_sprite_prop(0, 0);
    set_sprite_tile(2, SPR_SHADOW); set_sprite_prop(2, 0);   /* the gardener's dark purple */
    for (i = 0; i < 3; i++) {                                  /* sleeping cat, left grove */
        set_sprite_tile(SLOT_CAT + i, SPR_CAT0 + i * 2); set_sprite_prop(SLOT_CAT + i, 5);
        move_sprite(SLOT_CAT + i, CAT_X + i * 8 + 8, CAT_Y + 16);
    }
    for (i = 0; i < 4; i++) {                                  /* Cloverana, right grove */
        set_sprite_prop(SLOT_WITCH + i, 6);
        move_sprite(SLOT_WITCH + i, WITCH_X + (i & 1) * 8 + 8, WITCH_Y + (i & 2) * 8 + 16);
    }
    witch_frame = 0xFF; cat_frame = 0;
    meter_last = 0; hud_col_want = 0; hud_col_have = 0xFF;
    cur_set = 0xFF;
    G.hud_dirty = 1;
}

/* rebuild one playfield row from the grid into the pending row buffers */
static uint8_t star_t;   /* per frame, set by prepare_grid */
/* growth stage 0-3 of an appearing cell: (APPEAR_FRAMES - timer) / 60 without a divide */
static uint8_t appear_stage(uint8_t t) { return t > 180 ? 0 : (t > 120 ? 1 : (t > 60 ? 2 : 3)); }
/* angry oppie tile by [flash][gstate & 15] (state in bits 0-1, look direction in bits 2-3); a
   non-sprite hopper draws as idle, and looking right is looking left flipped */
#define ANGRY_DIR(look, w) T_OPPIE##w, look##w, T_OPPIE##w, T_OPPIE_STUN##w
static const uint8_t angry_tile[2][16] = {
    { ANGRY_DIR(T_OPPIE_LOOK_U, ), ANGRY_DIR(T_OPPIE_LOOK_L, ), ANGRY_DIR(T_OPPIE_LOOK_D, ), ANGRY_DIR(T_OPPIE_LOOK_L, ) },
    { ANGRY_DIR(T_OPPIE_LOOK_U, _W), ANGRY_DIR(T_OPPIE_LOOK_L, _W), ANGRY_DIR(T_OPPIE_LOOK_D, _W), ANGRY_DIR(T_OPPIE_LOOK_L, _W) },
};
static void prepare_row(uint8_t y) {
    uint8_t *tb = rowbuf_t[n_rows], *ab = rowbuf_a[n_rows];
    const uint8_t *gp = &G.grid[y * GW], *sp = &G.gstate[y * GW], *tp = &G.gtimer[y * GW];
    const uint8_t *at = angry_tile[G.flash];
    uint8_t mush_t = (G.flash && G.power_mush) ? T_MUSH_W : T_MUSH;
    uint8_t x, par = y & 1;   /* checkerboard: floor palette 0/1 */
    uint16_t pad = G.pad_rows[y];
    rowbuf_y[n_rows++] = y;
    for (x = 0; x < GW; x++, pad >>= 1, par ^= 1) {
        uint8_t g = *gp++, st = *sp++, tm = *tp++, t, a, blue;
        if (pad & 1) { t = star_t; a = 4; blue = 5; }   /* star pad: palette 4, angry on it 5 */
        else { t = T_FLOOR; a = par; blue = par + 2; }
        switch (g) {
        case C_EMPTY: break;
        case C_FRIEND: t = T_OPPIE; break;
        case C_TRAIL:  t = T_FOLLOW; break;
        case C_CLEARING: if (st) t = T_FOLLOW; else { t = T_OPPIE; a = blue; } break;
        case C_ANGRY:
            if (A_STATE(st) == A_HOP && (st & A_SPRITE)) break;   /* drawn as a sprite while hopping */
            a = blue; t = at[st & 15];
            if ((st & 15) == (A_LOOK | (D_RIGHT << 2))) a |= S_FLIPX;
            break;
        case C_MUSH: a = blue; t = mush_t; break;
        case C_APPEAR_ANGRY: {
            uint8_t lv = appear_stage(tm);
            a = blue; t = lv == 0 ? T_APPEAR0 : (lv == 1 ? T_APPEAR1 : (lv == 2 ? T_APPEAR2 : T_OPPIE));
            break; }
        case C_APPEAR_MUSH: {
            uint8_t lv = appear_stage(tm);
            a = blue; t = lv == 0 ? T_APPEAR0 : (lv == 1 ? T_APPEAR1 : (lv == 2 ? T_MUSH_APPEAR : T_MUSH));
            break; }
        default: break;
        }
        *tb++ = t; *ab++ = a;
    }
}

/* A row costs about 15 scanlines, so during play a new one is only started while the logic phase can
   still finish before VBlank (LY >= 144 means it is already late). The rest stay flagged for later frames. */
#define ROW_LY_LIMIT 118
static void prepare_grid(uint8_t budgeted, uint8_t max_rows) {
    uint8_t y;
    uint16_t m = G.dirty_rows, bit = 1;
    n_rows = 0;
    if (!m) return;
    star_t = (G.pad_invert && (G.pad_flash || G.pad_life <= PAD_WARN)) ? T_STAR_INV : T_STAR;
    for (y = 0; y < GH && n_rows < max_rows; y++, bit <<= 1)
        if (m & bit) {
            if (budgeted && LY_REG >= ROW_LY_LIMIT) break;
            prepare_row(y); G.dirty_rows &= ~bit;
        }
}

/* 12 bytes (one playfield row) into the tile map, unrolled: 5 cycles a byte against memcpy's ~12, which
   left four rows taking 7 of VBlank's 10 lines. dst in DE, src in BC (sdcccall 1); a playfield row sits
   at columns 4-15 of a 32-byte map row, so it never crosses a 256-byte page and inc e is enough. */
static void copy_row(uint8_t *dst, const uint8_t *src) __naked {
    (void)dst; (void)src;
__asm
    ld  h, b
    ld  l, c
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl+)
    ld  (de), a
    inc e
    ld  a, (hl)
    ld  (de), a
    ret
__endasm;
}
#if GW != 12 || MAP_X + GW > 32
#error copy_row copies exactly one 12-cell row within a map row
#endif

/* Straight copies into the tile map during VBlank (GBDK's set_bkg_tiles is several times slower). */
static void flush_rows(void) {
    uint8_t k;
    for (k = 0; k < n_rows; k++) {
        uint8_t *dst = (uint8_t *)(0x9800 + ((uint16_t)(MAP_Y + rowbuf_y[k]) << 5) + MAP_X);
        copy_row(dst, rowbuf_t[k]);
        VBK_REG = 1;
        copy_row(dst, rowbuf_a[k]);
        VBK_REG = 0;
    }
    n_rows = 0;
}

/* full redraw in VBlank chunks (used when a game starts) */
void render_grid_full(void) {
    G.dirty_rows = 0xFFF;
    while (G.dirty_rows) { prepare_grid(0, MAX_ROWS_PER_FRAME); wait_vbl_done(); flush_rows(); }
}

/* digits a pop-up value needs (1-6); two digits share an 8 px tile */
static uint8_t pop_ndigits(uint32_t v) {
    if (v >= 100000UL) return 6;
    if (v >= 10000UL) return 5;
    if (v >= 1000UL) return 4;
    if (v >= 100UL) return 3;
    if (v >= 10UL) return 2;
    return 1;
}

static void draw_sprites(void) {
    uint8_t tile, prop = 0, sx, sy, i, n = 3, lift = 0, dir = G.dir;
    uint8_t off = G.sub >> 1;
    uint8_t anim = (G.state == PS_PLAY) ? (uint8_t)((G.frame_count / 4) & 3) : 0;
    sx = ORG_X + G.px * 8; sy = ORG_Y + G.py * 8 - 8;    /* 16 px tall: feet in the cell, head in the one above */
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
        tile += anim * 2;
    }
    if (G.z) {
        uint8_t z = G.z;                       /* tenths of a unit -> pixels: z / 20 without a divide */
        while (z >= 20) { z -= 20; lift++; }
        move_sprite(2, sx + 8, sy + 8 + 16);   /* shadow at the feet */
    } else move_sprite(2, 0, 0);
    if (G.state == PS_DEAD) {   /* bump: recoil 4 px against the heading, then blink */
        uint8_t back = G.state_timer > 60 ? (uint8_t)((90 - G.state_timer) >> 3) : 4;
        switch (G.dir) { case D_UP: sy += back; break; case D_DOWN: sy -= back; break; case D_LEFT: sx += back; break; default: sx -= back; break; }
        tile = SPR_DOWN0; prop = 0;
    }
    if (G.state == PS_DEAD && G.state_timer < 60 && (G.state_timer & 4)) move_sprite(0, 0, 0);
    else { set_sprite_tile(0, tile); set_sprite_prop(0, prop); move_sprite(0, sx + 8, sy + 16 - lift); }
    /* hopping angry oppies */
    for (i = 0; i < n_hop_cells; i++, n++) {
        uint8_t c = hop_cells[i], st = G.gstate[c];
        uint8_t hx = ORG_X + (cell_x[c] << 3), hy = ORG_Y + (cell_y[c] << 3), back = G.gtimer[c] >> 1;
        uint8_t arc = G.gtimer[c] < 8 ? G.gtimer[c] : 16 - G.gtimer[c];   /* small hop arc */
        switch (A_DIR(st)) {
        case D_UP: hy += back; break;
        case D_DOWN: hy -= back; break;
        case D_LEFT: hx += back; break;
        default: hx -= back; break;
        }
        set_sprite_tile(n, SPR_OPPIE); set_sprite_prop(n, 7);
        move_sprite(n, hx + 8, hy - 8 + 16 - (arc >> 1));
    }
    for (; n < 3 + MAX_HOP_SPRITES; n++) move_sprite(n, 0, 0);
    /* flasks (falling ones are drawn above their cell) */
    for (i = 0; i < G.n_flask; i++, n++) {
        uint8_t c = G.flask_list[i];
        set_sprite_tile(n, SPR_FLASK); set_sprite_prop(n, 1 + G.gstate[c]);
        move_sprite(n, ORG_X + (cell_x[c] << 3) + 8, ORG_Y + (cell_y[c] << 3) - 8 + 16 - (G.flask_fall[i] >> 1));
    }
    for (; n < 3 + MAX_HOP_SPRITES + MAX_FLASK; n++) move_sprite(n, 0, 0);
    /* score pop-ups: 3x5 digits, two per 8 px tile, rising for 60 frames */
    for (i = 0; i < MAX_POPS; i++) {
        pop_t *p = &G.pops[i];
        uint8_t w, px, py, j;
        if (p->t == 0) { move_sprite(n++, 0, 0); move_sprite(n++, 0, 0); move_sprite(n++, 0, 0); continue; }
        w = (uint8_t)((pop_ndigits(p->val) + 1) >> 1);      /* tiles used, 1-3 */
        px = ORG_X + p->x * 8 + 8 + 4 - w * 4;
        py = ORG_Y + p->y * 8 + 16 - (uint8_t)((60 - p->t) >> 2);
        for (j = 0; j < 3; j++, n++) {
            if (j >= w) { move_sprite(n, 0, 0); continue; }
            set_sprite_tile(n, SPR_POP0 + i * 6 + j * 2); set_sprite_prop(n, 7); move_sprite(n, px + j * 8, py);
        }
    }

}

/* decimal digits by repeated subtraction: no 32-bit division (SDCC's is very slow) */
static const uint32_t pow10[8] = { 10000000UL, 1000000UL, 100000UL, 10000UL, 1000UL, 100UL, 10UL, 1UL };
static void digits(uint8_t *out, uint32_t v, uint8_t n) {
    uint8_t k, d;
    for (k = 8 - n; k < 8; k++) {
        uint32_t p = pow10[k];
        for (d = 0; v >= p && d < 9; d++) v -= p;
        *out++ = FONT_FIRST + d;
    }
}
/* tall two-tile digits (bank 1): tops in out[0..n), bottoms in out[n..2n) */
static void tall_digits(uint8_t *out, uint32_t v, uint8_t n) {
    uint8_t k, d, *bot = out + n;
    for (k = 8 - n; k < 8; k++) {
        uint32_t p = pow10[k];
        for (d = B1_DIGIT; v >= p && d < B1_DIGIT + 9; d++) v -= p;
        *out++ = d; *bot++ = d + 10;
    }
}
static uint8_t meter_state(void) { return G.potion_delay ? 6 : (G.flask_counter > 5 ? 5 : G.flask_counter); }
static void hud_prepare(void) {
    uint8_t i, f;
    tall_digits(hud_saved, G.saved, 3);
    tall_digits(hud_score, G.score, 8);
    f = B1_FLASK + (meter_state() << 2);
    for (i = 0; i < 4; i++) hud_flask[i] = f + i;
    if (G.power_timer) {
        digits(hud_timer, (G.power_timer + 9) / 10, 2);
        if (G.mult > 1) {
            uint8_t m = G.mult, tens = 0;
            while (m >= 10) { m -= 10; tens++; }
            hud_mult[0] = font_tile('x');
            if (tens) { hud_mult[1] = FONT_FIRST + tens; hud_mult[2] = FONT_FIRST + m; }
            else { hud_mult[1] = FONT_FIRST + m; hud_mult[2] = T_BLACK; }
        } else hud_mult[0] = hud_mult[1] = hud_mult[2] = T_BLACK;
    } else { hud_timer[0] = hud_timer[1] = T_BRICK; hud_mult[0] = hud_mult[1] = hud_mult[2] = T_BLACK; }
    hud_ready = 1;
}
static void hud_flush(void) {
    if (!hud_ready) return;
    hud_ready = 0;
    /* straight copies into the tile map (attributes are static): 31 tiles, well inside VBlank */
    memcpy((uint8_t *)(0x9800 + 16 * 32 + 2), hud_saved, 3);
    memcpy((uint8_t *)(0x9800 + 17 * 32 + 2), hud_saved + 3, 3);
    memcpy((uint8_t *)(0x9800 + 16 * 32 + 11), hud_score, 8);
    memcpy((uint8_t *)(0x9800 + 17 * 32 + 11), hud_score + 8, 8);
    memcpy((uint8_t *)(0x9800 + 15 * 32 + 7), hud_flask, 2);
    memcpy((uint8_t *)(0x9800 + 16 * 32 + 7), hud_flask + 2, 2);
    memcpy((uint8_t *)(0x9800 + 1 * 32 + 9), hud_timer, 2);
    memcpy((uint8_t *)(0x9800 + 17 * 32 + 7), hud_mult, 3);
}
void hud_draw_all(void) { hud_prepare(); wait_vbl_done(); hud_flush(); G.hud_dirty = 0; }

/* 3x5 digit font, one byte per row, bits 7..5 */
static const uint8_t font3x5[10][5] = {
    { 0xE0, 0xA0, 0xA0, 0xA0, 0xE0 }, { 0x40, 0xC0, 0x40, 0x40, 0xE0 }, { 0xE0, 0x20, 0xE0, 0x80, 0xE0 },
    { 0xE0, 0x20, 0x60, 0x20, 0xE0 }, { 0xA0, 0xA0, 0xE0, 0x20, 0x20 }, { 0xE0, 0x80, 0xE0, 0x20, 0xE0 },
    { 0xE0, 0x80, 0xE0, 0xA0, 0xE0 }, { 0xE0, 0x20, 0x20, 0x20, 0x20 }, { 0xE0, 0xA0, 0xE0, 0xA0, 0xE0 },
    { 0xE0, 0xA0, 0xE0, 0x20, 0xE0 },
};
/* Compose the three 8x16 objects of pop-up k (digits in rows 1-5 of each top tile, colour index 2).
   RAM only, so it runs in phase 1: repeated subtraction of a power of ten is far too slow for VBlank.
   Those 15 bytes (the upper plane of rows 1-5 of the three top tiles) are the only ones a pop-up ever
   sets; the rest of its tiles stay blank from boot, so VBlank uploads just these. */
static uint8_t popbuf[15];                  /* [tile 0-2][row 1-5] */
static uint8_t *pop_dst;                    /* VRAM address of the first of them */
static uint8_t pop_pending = 0xFF;
static uint8_t bob_tick, bob_frame, bob_pending;   /* trail oppie bob: the tile flips every 5 frames */
static void compose_pop(uint8_t k) {
    uint8_t d[6], nd = 0, c, row, i;
    uint32_t v = G.pops[k].val;
    if (v > 999999UL) v = 999999UL;
    memset(popbuf, 0, sizeof popbuf);
    for (i = 2; i < 8; i++) {                       /* most significant first, leading zeros dropped */
        uint32_t p = pow10[i];
        for (c = 0; v >= p && c < 9; c++) v -= p;
        if (c || nd || i == 7) d[nd++] = c;
    }
    for (i = 0; i < nd; i++) {
        uint8_t *b = &popbuf[(i >> 1) * 5], shift = (i & 1) ? 4 : 0;   /* object i/2, digit at x 0 or 4 */
        for (row = 0; row < 5; row++) b[row] |= font3x5[d[i]][row] >> shift;
    }
    pop_dst = (uint8_t *)0x8000 + (uint16_t)(SPR_POP0 + k * 6) * 16 + 3;   /* row 1, upper plane */
    pop_pending = k;
}

/* Phase 1 (any time in the frame): compute everything, touch only shadow OAM and RAM buffers. */
void render_prepare(void) {
    if (cur_set != G.palette_set) { cur_set = G.palette_set; pal_pending = 1; }
    if (G.state == PS_PLAY) {   /* the flask meter fills, then shows a made flask full in its colour */
        uint8_t m = meter_state();
        if (m != meter_last) { meter_last = m; G.hud_dirty = 1; }
        hud_col_want = G.potion_delay ? 1 + G.potion_type : 0;
    }
    if (++bob_tick == 5) { bob_tick = 0; bob_frame ^= 1; bob_pending = 1; }
    draw_sprites();
    draw_witch();
    draw_cat();
    /* GBDK's palette load waits for HBlank before each of its 128 bytes, so it runs far past VBlank (safely);
       rows, HUD and pop-ups written after it would land in the visible frame and be dropped. They wait a frame. */
    if (pal_pending) return;
    /* both are 32-bit decimal conversions: at most one per frame, the HUD waits a frame for a pop-up */
    if (G.pop_dirty && pop_pending == 0xFF) {
        uint8_t k;
        for (k = 0; k < MAX_POPS; k++) if (G.pop_dirty & (1 << k)) { G.pop_dirty &= (uint8_t)~(1 << k); compose_pop(k); break; }
    } else if (G.hud_dirty) { G.hud_dirty = 0; hud_prepare(); }
    /* last: it fills whatever time the frame has left. VBlank (lines 145-153) fits 4 rows (~1.3 lines
       each) and the bob; beside a pop-up upload (~2.5) or the HUD (~3) it fits 2 */
    prepare_grid(1, (pop_pending != 0xFF || hud_ready) ? 2 : MAX_ROWS_PER_FRAME);
}
/* Phase 2 (right after wait_vbl_done): VRAM + palette writes only. */
void render_flush(void) {
    if (pal_pending) { pal_pending = 0; palettes_apply(cur_set); hud_col_have = 0xFF; }
    if (hud_col_want != hud_col_have) { hud_col_have = hud_col_want; set_bkg_palette_entry(7, 3, hud_colors[hud_col_want]); }
    if (pop_pending != 0xFF) {
        uint8_t *d = pop_dst, *b = popbuf, t, r;
        for (t = 0; t < 3; t++, d += 22) for (r = 0; r < 5; r++, d += 2) *d = *b++;   /* next tile: 32 on */
        pop_pending = 0xFF;
    }
    flush_rows();
    hud_flush();
    /* last, and only with VBlank to spare: a late bob waits a frame rather than push the rows out of VBlank */
    if (bob_pending && LY_REG >= 144 && LY_REG < 151) {
        bob_pending = 0;
        memcpy((uint8_t *)0x8000 + (uint16_t)T_FOLLOW * 16, follow_bob + (bob_frame << 4), 16);
    }
}

