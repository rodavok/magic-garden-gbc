#include <gb/gb.h>
#include <string.h>
#include "hUGEDriver.h"
#include "music.h"


/* Song data lives in ROM bank 2; the driver reads it through pointers, so bank 2 is mapped around every
   driver call and bank 1 (graphics, screens) restored afterwards. */
extern const hUGESong_t song_gameplay, song_win, song_lose, song_end;
#define SONG_BANK 2
#define HOME_BANK 1

static uint8_t current, playing;
static uint16_t frames_left;         /* for stings: frames until the song ends */
static uint8_t hold_mask, hold_frames;

static void silence(void) {
    NR12_REG = 0; NR14_REG = 0x80; NR22_REG = 0; NR24_REG = 0x80; NR30_REG = 0; NR42_REG = 0; NR44_REG = 0x80;
}

void music_play(uint8_t song) {
    const hUGESong_t *s = 0;
    current = song; playing = 0; frames_left = 0;
    switch (song) {
    case SONG_GAMEPLAY: s = &song_gameplay; break;
    case SONG_WIN:  s = &song_win;  frames_left = 69 * 11; break;
    case SONG_LOSE: s = &song_lose; frames_left = 13 * 11; break;
    case SONG_END:  s = &song_end;  frames_left = 118 * 11; break;
    default: break;
    }
    silence();
    if (!s) return;
    SWITCH_ROM(SONG_BANK);
    hUGE_init(s);
    SWITCH_ROM(HOME_BANK);
    hold_mask = 0; hold_frames = 0;
    playing = 1;
}

void music_stop(void) {
    playing = 0; current = SONG_NONE;
    silence();
}

void music_sfx_hold(uint8_t channels, uint8_t frames) {
    uint8_t ch;
    if (!playing) return;
    for (ch = 0; ch < 4; ch++) if (channels & (1 << ch)) hUGE_mute_channel(ch, HT_CH_MUTE);
    hold_mask |= channels;
    if (frames > hold_frames) hold_frames = frames;
}

void music_update(void) {
    if (!playing) return;
    if (hold_frames) {
        if (--hold_frames == 0) {
            uint8_t ch;
            for (ch = 0; ch < 4; ch++) if (hold_mask & (1 << ch)) hUGE_mute_channel(ch, HT_CH_PLAY);
            hold_mask = 0;
        }
    }
    SWITCH_ROM(SONG_BANK);
    hUGE_dosound();
    SWITCH_ROM(HOME_BANK);
    if (frames_left && --frames_left == 0) music_stop();
}
