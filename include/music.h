#ifndef MUSIC_H
#define MUSIC_H
#include <stdint.h>
enum { SONG_NONE, SONG_GAMEPLAY, SONG_WIN, SONG_LOSE, SONG_END };
void music_play(uint8_t song);      /* start a song (loops unless it is a sting) */
void music_stop(void);
void music_update(void);            /* call once per frame in VBlank */
void music_sfx_hold(uint8_t channels, uint8_t frames);   /* mute driver channels (bit0 CH1 .. bit3 CH4) while an effect plays */
#endif
