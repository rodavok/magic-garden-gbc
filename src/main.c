#include <gb/gb.h>
#include <gb/cgb.h>
#include <rand.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"
#include "sfx.h"
#include "save.h"
#include "music.h"

enum { ST_TITLE, ST_SCORES, ST_PLAY, ST_OVER, ST_ENDING };

extern uint8_t menu_sel, end_phase, hint_shown;
void show_title(void); void show_scores(void); void start_game(void);
void title_animate(void); void ending_begin(void); void ending_update(uint8_t pressed); void ending_flush(void);
void clear_hint_row(void);
static uint8_t joy_prev;

void main(void) {
    uint8_t state = ST_TITLE, joy, pressed;
    cpu_fast();
    SWITCH_ROM(1);   /* graphics data lives in bank 1 and stays mapped */
    save_load();
    sfx_init();
    DISPLAY_OFF;
    /* Assume nothing about the state a flash-cart menu or boot ROM left behind:
       scroll, window, both tile-map banks, OAM and palettes are all reset with the LCD off. */
    SCX_REG = 0; SCY_REG = 0; WX_REG = 7; WY_REG = 144;
    LCDC_REG = LCDCF_BG8000 | LCDCF_BGON;   /* LCD off, BG map at 0x9800, tiles at 0x8000, sprites off */
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    set_sprite_data(BG_BASE, BG_TILE_COUNT, bg_tiles);
    VBK_REG = 1; set_sprite_data(0, SIDE_TILE_COUNT, side_tiles); VBK_REG = 0;   /* sidebar grove (attr bit 3) */
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
            if (G.state == PS_WIN) { save_insert(G.score, G.saved, G.best_drop, G.best_chain, G.total_kills); ending_begin(); state = ST_ENDING; }
            render_prepare();
            G.dbg[1] = LY_REG;
            break;
        case ST_ENDING:
            G.frame_count++;
            ending_update(pressed);
            render_prepare();
            break;
        case ST_OVER:
            if (pressed & J_START) { show_title(); state = ST_TITLE; }
            break;
        }
        /* phase 2: VRAM writes in VBlank */
        wait_vbl_done();
        music_update();
        sfx_update();
        if (state == ST_ENDING) {
            render_flush();
            ending_flush();
            if (end_phase == 3 && (pressed & J_START)) { show_title(); state = ST_TITLE; }
        }
        if (state == ST_PLAY) {
            G.dbg[2] = LY_REG;
            if (hint_shown && G.state != PS_WAIT) clear_hint_row();
            render_flush();
            G.dbg[3] = LY_REG;
            if (G.state == PS_DEAD && G.state_timer == 0) {
                uint8_t rank = save_insert(G.score, G.saved, G.best_drop, G.best_chain, G.total_kills);
                hud_text(4, 8, "  GAME OVER ");
                if (rank) hud_text(4, 10, " HIGH SCORE ");
                state = ST_OVER;
            }
        }
    }
}
