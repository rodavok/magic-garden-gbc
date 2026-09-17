#pragma bank 1
/* Title, high-score screen, game start, ending sequence. Lives in ROM bank 1 (always mapped). */
#include <gb/gb.h>
#include <gb/cgb.h>
#include <rand.h>
#include <string.h>
#include "game.h"
#include "gfx_data.h"
#include "sfx.h"
#include "save.h"
#include "music.h"

static uint8_t screen_buf[20 * 18];
uint8_t menu_sel;
/* title screen hoppers */
#define N_HOP 3
static uint8_t hop_x[N_HOP], hop_t[N_HOP], hop_dir[N_HOP];
static const uint8_t hop_row[N_HOP] = { 14, 15, 14 };

static void hide_sprites(void) { uint8_t i; for (i = 0; i < 40; i++) move_sprite(i, 0, 0); }

void show_title(void) {
    music_stop();
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
void title_animate(void) {
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

/* digits from most significant: simple repeated subtraction (no 32-bit division) */
static void put_number_ms(uint8_t *buf, uint8_t x, uint8_t y, uint32_t v, uint8_t digits) {
    static const uint32_t pw[6] = { 100000UL, 10000UL, 1000UL, 100UL, 10UL, 1UL };
    uint8_t *p = buf + y * 20 + x; uint8_t k;
    for (k = 6 - digits; k < 6; k++) { uint8_t d = 0; while (v >= pw[k] && d < 9) { v -= pw[k]; d++; } *p++ = FONT_FIRST + d; }
}

void show_scores(void) {
    static const char *rank[5] = { "1ST", "2ND", "3RD", "4TH", "5TH" };
    uint8_t i;
    HIDE_SPRITES;
    hide_sprites();
    memset(screen_buf, T_BLACK, sizeof screen_buf);
    map_text(screen_buf, 4, 1, "HIGH SCORES");
    map_text(screen_buf, 1, 3, "RANK  SCORE  SAVED");
    for (i = 0; i < HS_ENTRIES; i++) {
        map_text(screen_buf, 1, 4 + i, rank[i]);
        put_number_ms(screen_buf, 6, 4 + i, SAVE.table[i].score, 6);
        put_number_ms(screen_buf, 15, 4 + i, SAVE.table[i].saved, 3);
    }
    map_text(screen_buf, 1, 10, "BIGGEST DROP-OFF");
    put_number_ms(screen_buf, 17, 10, SAVE.best_drop, 2);
    map_text(screen_buf, 1, 11, "MOST CLEARED");
    put_number_ms(screen_buf, 17, 11, SAVE.best_chain, 2);
    map_text(screen_buf, 1, 12, "TOTAL CLEARED");
    put_number_ms(screen_buf, 16, 12, SAVE.total_kills, 3);
    map_text(screen_buf, 6, 16, "PRESS B");
    vram_draw_map(screen_buf, 0);
}

/* ---- ending: the garden fills with oppies, Cloverana comes round, credits ---- */
static const char *ending_lines[4][3] = {
    { "PLEASE DON'T BE", "JEALOUS OF ME.", "" },
    { "WE NEED TO HELP EACH", "OTHER, NOT TEAR EACH", "OTHER DOWN." },
    { "I CAN TEACH YOU HOW", "TO GROW A WONDERFUL", "GARDEN OF YOUR OWN!" },
    { "CLOVERANA: YOU'RE", "RIGHT... THANK YOU!", "" },
};
static const char *credits_lines[] = {
    "DIRECTOR", "BENEDIKT CHUN", "", "PROGRAM", "GERRY SMOLSKI", "", "GRAPHICS", "BENEDIKT CHUN", "",
    "SOUND", "THORSON PETTER", "", "LX-II DESIGN", "MEESHA DANRY", "", "SPECIAL THANKS", "JESCA ZARIAN",
    "LANCE THE CAT", "MR. BIG'S BURGERS", "AND YOU, THE PLAYER!", "", "PRESENTED BY", "LX SYSTEMS", "", "THE END",
};
#define CREDITS_N (sizeof(credits_lines) / sizeof(credits_lines[0]))
uint8_t end_phase; static uint8_t end_cell, end_page;
static uint16_t end_timer;

static void ending_panel(const char *a, const char *b, const char *c) {
    hud_text(0, 15, "                    ");
    hud_text(0, 16, "                    ");
    hud_text(0, 17, "                    ");
    hud_text(0, 15, a); hud_text(0, 16, b); hud_text(0, 17, c);
}
void ending_begin(void) {
    end_phase = 0; end_cell = 0; end_timer = 0; end_page = 0;
    music_play(SONG_WIN);
    G.state = PS_WIN; G.drop_anim = 0; G.turn_timer = 0; G.z = 0;
}
/* runs in the logic phase; VRAM text goes through hud_text after wait_vbl_done in the flush phase */
static uint8_t end_text_pending;
uint8_t hint_shown;
void ending_update(uint8_t pressed) {
    switch (end_phase) {
    case 0:   /* fill the arena with friendly oppies, one cell every 5 frames */
        if (++end_timer >= 5) {
            end_timer = 0;
            if (G.grid[end_cell] != C_FRIEND) { G.grid[end_cell] = C_FRIEND; G.dirty_rows |= (uint16_t)1 << (end_cell / GW); }
            if (++end_cell == NCELLS) { end_phase = 1; end_timer = 0; end_text_pending = 1; music_play(SONG_END); }
        }
        break;
    case 1:   /* dialogue pages: A/Start or 240 frames each */
        if (++end_timer >= 240 || (pressed & (J_A | J_START))) {
            end_timer = 0;
            if (++end_page >= 4) { end_phase = 2; end_page = 0; }
            end_text_pending = 1;
        }
        break;
    case 2:   /* credits: three lines at a time, 150 frames per page */
        if (++end_timer >= 150 || (pressed & (J_A | J_START))) {
            end_timer = 0; end_page += 3;
            if (end_page >= CREDITS_N) { end_phase = 3; end_timer = 0; }
            end_text_pending = 1;
        }
        break;
    default:  /* done: wait for Start */
        break;
    }
}
void ending_flush(void) {
    if (!end_text_pending) return;
    end_text_pending = 0;
    if (end_phase == 1) ending_panel(ending_lines[end_page][0], ending_lines[end_page][1], ending_lines[end_page][2]);
    else if (end_phase == 2) ending_panel(end_page < CREDITS_N ? credits_lines[end_page] : "",
                                          end_page + 1 < CREDITS_N ? credits_lines[end_page + 1] : "",
                                          end_page + 2 < CREDITS_N ? credits_lines[end_page + 2] : "");
    else if (end_phase == 3) ending_panel("      YOU WIN!      ", "", "     PRESS START    ");
}

void start_game(void) {
    initrand(DIV_REG | ((uint16_t)DIV_REG << 8) ^ 0x5A17);
    game_init();
    music_play(SONG_GAMEPLAY);
    HIDE_SPRITES;
    hide_sprites();
    wait_vbl_done();
    palettes_apply(0);
    render_init();
    render_grid_full();
    hud_draw_all();
    wait_vbl_done();
    hud_text(0, 17, "PRESS RIGHT OR DOWN ");
    hint_shown = 1;
    SHOW_SPRITES;
}


void clear_hint_row(void) {
    uint8_t row[20]; memset(row, T_PANEL, 20); set_bkg_tiles(0, 17, 20, 1, row); hint_shown = 0; G.hud_dirty = 1;
}
