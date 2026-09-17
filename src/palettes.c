#include <gb/gb.h>
#include <gb/cgb.h>
#include "game.h"

#define C(r,g,b) ((uint16_t)(((r) >> 3) | (((g) >> 3) << 5) | (((b) >> 3) << 10)))
#define WHITE  C(255,255,255)
#define BLACK  C(0,0,0)
#define RED    C(254,98,110)
#define BLUE   C(0,106,180)

/* per palette set: floorA, floorB, star, tree, eyes, ground */
static const uint16_t set_colors[4][6] = {
    { C(99,179,29),   C(254,184,84),  C(164,240,34),  C(204,104,228), C(0,106,180),   C(0,132,86)   },
    { C(164,240,34),  C(232,234,74),  C(88,245,177),  C(224,60,50),   C(255,255,255), C(163,163,36) },
    { C(39,186,219),  C(88,245,177),  C(164,240,34),  C(39,186,219),  C(255,255,255), C(52,0,88)    },
    { C(200,200,200), C(255,255,255), C(164,240,34),  C(255,255,255), C(88,245,177),  C(112,112,112)},
};

static uint16_t bg_pal[32];

static const uint16_t obj_pal[8 * 4] = {
    0, C(52,0,88),   C(150,0,220),  WHITE,   /* 0 gardener */
    0, C(209,15,76), C(254,98,110), WHITE,   /* 1 red flask */
    0, C(0,61,16),   C(164,240,34), WHITE,   /* 2 green flask */
    0, C(0,106,180), C(39,186,219), WHITE,   /* 3 blue flask */
    0, C(254,112,0), C(232,234,74), WHITE,   /* 4 gold flask */
    0, C(20,20,40),  C(52,0,88),    WHITE,   /* 5 shadow */
    0, WHITE, WHITE, WHITE,
    0, WHITE, WHITE, WHITE,
};

void palettes_apply(uint8_t set) {
    const uint16_t *s = set_colors[set & 3];
    uint16_t fa = s[0], fb = s[1], star = s[2];
    /* 0..5: grid object palettes */
    bg_pal[0] = fa;   bg_pal[1] = WHITE; bg_pal[2] = BLACK; bg_pal[3] = RED;
    bg_pal[4] = fb;   bg_pal[5] = WHITE; bg_pal[6] = BLACK; bg_pal[7] = RED;
    bg_pal[8] = fa;   bg_pal[9] = WHITE; bg_pal[10] = BLACK; bg_pal[11] = BLUE;
    bg_pal[12] = fb;  bg_pal[13] = WHITE; bg_pal[14] = BLACK; bg_pal[15] = BLUE;
    bg_pal[16] = star; bg_pal[17] = WHITE; bg_pal[18] = BLACK; bg_pal[19] = RED;
    bg_pal[20] = star; bg_pal[21] = WHITE; bg_pal[22] = BLACK; bg_pal[23] = BLUE;
    /* 6: decoration */
    bg_pal[24] = BLACK; bg_pal[25] = s[5]; bg_pal[26] = s[3]; bg_pal[27] = s[4];
    /* 7: HUD */
    bg_pal[28] = C(64,64,64); bg_pal[29] = C(200,200,200); bg_pal[30] = WHITE; bg_pal[31] = RED;
    set_bkg_palette(0, 8, bg_pal);
    set_sprite_palette(0, 8, obj_pal);
}
