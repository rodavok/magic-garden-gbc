#include <gb/gb.h>
#include <gb/cgb.h>
#include <rand.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"
#include "sfx.h"

enum { ST_TITLE, ST_PLAY, ST_OVER };

static uint8_t joy_prev;

static void clear_screen(void) {
    uint8_t row[20];
    uint8_t y;
    memset(row, T_BLACK, 20);
    for (y = 0; y < 18; y++) set_bkg_tiles(0, y, 20, 1, row);
    VBK_REG = 1;
    memset(row, 7, 20);
    for (y = 0; y < 18; y++) set_bkg_tiles(0, y, 20, 1, row);
    VBK_REG = 0;
}

static void show_title(void) {
    uint8_t i;
    HIDE_SPRITES;
    DISPLAY_OFF;
    clear_screen();
    hud_text(4, 4, "MAGIC GARDEN");
    hud_text(3, 7, "STOP THE WITCH");
    hud_text(2, 8, "CLOVERANA FROM");
    hud_text(2, 9, "SABOTAGING YOUR");
    hud_text(6, 10, "GARDEN!");
    hud_text(5, 13, "PRESS START");
    hud_text(3, 16, "GBC PORT 2026");
    for (i = 0; i < 40; i++) move_sprite(i, 0, 0);
    DISPLAY_ON;
}

static void start_game(void) {
    initrand(DIV_REG | ((uint16_t)DIV_REG << 8) ^ 0x5A17);
    game_init();
    DISPLAY_OFF;
    render_init();
    render_grid_full();
    hud_draw_all();
    SHOW_SPRITES;
    DISPLAY_ON;
}

void main(void) {
    uint8_t state = ST_TITLE, joy, pressed;
    cpu_fast();
    sfx_init();
    DISPLAY_OFF;
    palettes_apply(0);
    LCDC_REG |= LCDCF_BG8000;
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    set_sprite_data(BG_BASE, BG_TILE_COUNT, bg_tiles);
    SHOW_BKG;
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
