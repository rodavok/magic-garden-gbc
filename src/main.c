#include <gb/gb.h>
#include <gb/cgb.h>
#include <rand.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"
#include "sfx.h"

enum { ST_TITLE, ST_SCORES, ST_PLAY, ST_OVER };

static uint8_t joy_prev;
static uint8_t screen_buf[20 * 18];
static uint8_t menu_sel;
/* title screen hoppers */
#define N_HOP 3
static uint8_t hop_x[N_HOP], hop_t[N_HOP], hop_dir[N_HOP];
static const uint8_t hop_row[N_HOP] = { 14, 15, 14 };

static void hide_sprites(void) { uint8_t i; for (i = 0; i < 40; i++) move_sprite(i, 0, 0); }

static void show_title(void) {
    HIDE_SPRITES;
    hide_sprites();
    wait_vbl_done();
    palettes_title();
    vram_draw_map(title_map, title_attr);
    SPRITES_8x16;
    set_sprite_tile(0, SPR_OPPIE); set_sprite_prop(0, 6);          /* menu cursor */
    set_sprite_tile(1, SPR_OPPIE); set_sprite_prop(1, 6);
    set_sprite_tile(2, SPR_OPPIE); set_sprite_prop(2, 6);
    set_sprite_tile(3, SPR_OPPIE); set_sprite_prop(3, 6);
    hop_x[0] = 20;  hop_t[0] = 0;  hop_dir[0] = 1;
    hop_x[1] = 90;  hop_t[1] = 9;  hop_dir[1] = 0;
    hop_x[2] = 130; hop_t[2] = 17; hop_dir[2] = 1;
    SHOW_SPRITES;
}

/* hop: 24-frame cycle, parabolic lift up to 6 px, moving while airborne */
static void title_animate(void) {
    uint8_t i;
    move_sprite(0, 3 * 8 + 8, (11 + menu_sel) * 8 + 8);
    for (i = 0; i < N_HOP; i++) {
        uint8_t t = hop_t[i], lift = 0;
        if (t < 16) {
            uint8_t k = t < 8 ? t : 15 - t;           /* 0..7..0 */
            lift = (uint8_t)((k * 6) / 7);
            if (t & 1) { if (hop_dir[i]) { if (++hop_x[i] > 148) hop_dir[i] = 0; } else { if (--hop_x[i] < 4) hop_dir[i] = 1; } }
        }
        hop_t[i] = (t + 1) % 30;
        set_sprite_prop(1 + i, 6 | (hop_dir[i] ? 0 : S_FLIPX));
        move_sprite(1 + i, hop_x[i] + 8, hop_row[i] * 8 + 8 - lift);
    }
}

static void show_scores(void) {
    static const char *rank[5] = { "1ST", "2ND", "3RD", "4TH", "5TH" };
    uint8_t i;
    HIDE_SPRITES;
    hide_sprites();
    memset(screen_buf, T_BLACK, sizeof screen_buf);
    map_text(screen_buf, 4, 2, "HIGH SCORES");
    for (i = 0; i < 5; i++) {
        map_text(screen_buf, 3, 5 + i * 2, rank[i]);
        map_text(screen_buf, 8, 5 + i * 2, "000000");
    }
    map_text(screen_buf, 6, 16, "PRESS B");
    vram_draw_map(screen_buf, 0);
}

static void start_game(void) {
    initrand(DIV_REG | ((uint16_t)DIV_REG << 8) ^ 0x5A17);
    game_init();
    HIDE_SPRITES;
    hide_sprites();
    wait_vbl_done();
    palettes_apply(0);
    render_init();
    render_grid_full();
    hud_draw_all();
    SHOW_SPRITES;
}

void main(void) {
    uint8_t state = ST_TITLE, joy, pressed;
    cpu_fast();
    SWITCH_ROM(1);   /* graphics data lives in bank 1 and stays mapped */
    sfx_init();
    DISPLAY_OFF;
    /* Assume nothing about the state a flash-cart menu or boot ROM left behind:
       scroll, window, both tile-map banks, OAM and palettes are all reset with the LCD off. */
    SCX_REG = 0; SCY_REG = 0; WX_REG = 7; WY_REG = 144;
    LCDC_REG = LCDCF_BG8000 | LCDCF_BGON;   /* LCD off, BG map at 0x9800, tiles at 0x8000, sprites off */
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    set_sprite_data(BG_BASE, BG_TILE_COUNT, bg_tiles);
    fill_bkg_rect(0, 0, 32, 32, T_BLACK);
    VBK_REG = 1; fill_bkg_rect(0, 0, 32, 32, 7); VBK_REG = 0;
    { uint8_t i; for (i = 0; i < 40; i++) { set_sprite_tile(i, 0); set_sprite_prop(i, 0); move_sprite(i, 0, 0); } }
    palettes_title();
    LCDC_REG = LCDCF_ON | LCDCF_BG8000 | LCDCF_BGON;   /* LCD on; from here on VRAM is only touched in VBlank */
    menu_sel = 0;
    show_title();
    joy_prev = 0;
    while (1) {
        /* phase 1: logic + RAM-side rendering, during the visible frame (from scanline 2) */
        while (LY_REG >= 144 || LY_REG < 2) ;   /* start the logic phase at scanline 2, or at once if a flush ran late */
        joy = joypad();
        pressed = joy & ~joy_prev;
        joy_prev = joy;
        switch (state) {
        case ST_TITLE:
            if (pressed & (J_UP | J_DOWN)) menu_sel ^= 1;
            if (pressed & (J_START | J_A)) {
                if (menu_sel == 0) { start_game(); state = ST_PLAY; }
                else { show_scores(); state = ST_SCORES; }
            } else title_animate();
            break;
        case ST_SCORES:
            if (pressed & (J_B | J_START | J_A)) { show_title(); state = ST_TITLE; }
            break;
        case ST_PLAY:
            G.frame_count++;
            G.dbg[0] = LY_REG;
            game_update(joy, pressed);
            render_prepare();
            G.dbg[1] = LY_REG;
            break;
        case ST_OVER:
            if (pressed & J_START) { show_title(); state = ST_TITLE; }
            break;
        }
        /* phase 2: VRAM writes in VBlank */
        wait_vbl_done();
        if (state == ST_PLAY) {
            G.dbg[2] = LY_REG;
            render_flush();
            G.dbg[3] = LY_REG;
            if (G.state == PS_DEAD && G.state_timer == 0) {
                hud_text(4, 8, "  GAME OVER ");
                state = ST_OVER;
            } else if (G.state == PS_WIN && G.state_timer == 0) {
                hud_text(4, 8, "GARDEN SAVED");
                state = ST_OVER;
            }
        }
    }
}
