#include <gb/gb.h>
#include <gb/cgb.h>
#include <rand.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"
#include "sfx.h"

enum { ST_TITLE, ST_PLAY, ST_OVER };

static uint8_t joy_prev;

static uint8_t screen_buf[20 * 18];

static void show_title(void) {
    uint8_t i;
    HIDE_SPRITES;
    for (i = 0; i < 40; i++) move_sprite(i, 0, 0);
    memset(screen_buf, T_BLACK, sizeof screen_buf);
    map_text(screen_buf, 4, 4, "MAGIC GARDEN");
    map_text(screen_buf, 3, 7, "STOP THE WITCH");
    map_text(screen_buf, 2, 8, "CLOVERANA FROM");
    map_text(screen_buf, 2, 9, "SABOTAGING YOUR");
    map_text(screen_buf, 6, 10, "GARDEN!");
    map_text(screen_buf, 5, 13, "PRESS START");
    map_text(screen_buf, 3, 16, "GBC PORT 2026");
    vram_draw_map(screen_buf, 0);
}

static void start_game(void) {
    initrand(DIV_REG | ((uint16_t)DIV_REG << 8) ^ 0x5A17);
    game_init();
    render_init();
    render_grid_full();
    hud_draw_all();
    SHOW_SPRITES;
}

void main(void) {
    uint8_t state = ST_TITLE, joy, pressed;
    cpu_fast();
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
    palettes_apply(0);
    LCDC_REG = LCDCF_ON | LCDCF_BG8000 | LCDCF_BGON;   /* LCD on; from here on VRAM is only touched in VBlank */
    show_title();
    joy_prev = 0;
    while (1) {
        /* phase 1: logic + RAM-side rendering, during the visible frame (from scanline 2) */
        while (LY_REG != 2) ;
        joy = joypad();
        pressed = joy & ~joy_prev;
        joy_prev = joy;
        switch (state) {
        case ST_TITLE:
            if (pressed & J_START) { start_game(); state = ST_PLAY; }
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
