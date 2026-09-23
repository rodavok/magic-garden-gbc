/* Music test ROM for tools/song_render.py: plays the gameplay song and nothing else.
   -DSOLO=mask keeps only the channels in mask (bit0 CH1 .. bit3 CH4) audible. */
#include <gb/gb.h>
#include "hUGEDriver.h"
#include "music.h"
#ifndef SOLO
#define SOLO 0x0F
#endif
void main(void) {
    uint8_t ch;
    SWITCH_ROM(1);
    NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
    music_play(SONG_GAMEPLAY);
    SWITCH_ROM(2);
    for (ch = 0; ch < 4; ch++) if (!(SOLO & (1 << ch))) hUGE_mute_channel(ch, HT_CH_MUTE);
    SWITCH_ROM(1);
    while (1) { wait_vbl_done(); music_update(); }
}
