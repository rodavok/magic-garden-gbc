#pragma bank 1
#include <gb/gb.h>
#include <gb/hardware.h>
#include "sfx.h"
#include "music.h"

/* Register-level sound effects.
   Channel 1 carries the melody, so nothing that fires during play is allowed to touch it: every
   gameplay effect lives on channel 2 (the harmony, which sounds on about one row in seven) or on
   channel 4 (drums). Only death and the win fanfare use channel 1, and by then the track is ending.
   Channel 2 has no hardware sweep, so sfx_update() walks the frequency itself, one or two sweep
   steps a frame, writing the pitch without the restart bit so the envelope keeps running. */
static struct { uint8_t frames, shift, down; uint16_t freq; } sw;

void sfx_init(void) {
    NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
    sw.frames = 0;
}

static void ch1(uint8_t sweep, uint8_t duty_len, uint8_t env, uint16_t freq) {
    music_sfx_hold(1, 20);
    NR10_REG = sweep; NR11_REG = duty_len; NR12_REG = env;
    NR13_REG = (uint8_t)freq; NR14_REG = 0x80 | (uint8_t)(freq >> 8);
}
static void ch2(uint8_t duty_len, uint8_t env, uint16_t freq, uint8_t frames) {
    sw.frames = 0;
    music_sfx_hold(2, frames);
    NR21_REG = duty_len; NR22_REG = env;
    NR23_REG = (uint8_t)freq; NR24_REG = 0x80 | (uint8_t)(freq >> 8);
}
/* channel 2 with a software sweep; `shift` matches NR10's shift field, `down` its direction bit */
static void ch2sw(uint8_t duty_len, uint8_t env, uint16_t freq, uint8_t shift, uint8_t down, uint8_t frames) {
    ch2(duty_len, env, freq, frames);
    sw.freq = freq; sw.shift = shift; sw.down = down; sw.frames = frames;
}
static void ch4(uint8_t env, uint8_t poly) {
    music_sfx_hold(8, 16);
    NR41_REG = 0x00; NR42_REG = env; NR43_REG = poly; NR44_REG = 0x80;
}

void sfx_update(void) {
    uint8_t k;
    if (!sw.frames) return;
    sw.frames--;
    for (k = 0; k < 2; k++) {                     /* the hardware sweep steps at 128 Hz, so twice a frame */
        uint16_t d = sw.freq >> sw.shift;
        if (!d) { sw.frames = 0; return; }
        if (sw.down) {
            if (sw.freq <= d + 64) { sw.frames = 0; return; }
            sw.freq -= d;
        } else {
            sw.freq += d;
            /* GB frequency is 131072/(2048-x), so x runs away near the top: hold at a musical
               ceiling and let the envelope finish rather than sweeping into an overflow silence. */
            if (sw.freq >= 1980) { sw.freq = 1980; sw.frames = 1; break; }
        }
    }
    NR23_REG = (uint8_t)sw.freq;
    NR24_REG = (uint8_t)(sw.freq >> 8);           /* pitch only: no restart, so the envelope continues */
}

void sfx_pickup(void)   { ch2(0x80, 0xF1, 0x77D, 12); }
void sfx_save(void)     { ch2sw(0x80, 0xF3, 1400, 6, 0, 18); }   /* 200 Hz sweeping up */
void sfx_bad_drop(void) { ch2sw(0x40, 0xF4, 1700, 5, 1, 18); }   /* 380 Hz sagging down */
void sfx_jump(void)     { ch2sw(0x80, 0xA2, 1550, 5, 0, 12); }   /* quick chirp up off the ground */
void sfx_flask(void)    { ch2(0xC0, 0xF4, 0x6C0, 16); }
void sfx_kill(void)     { ch4(0xF2, 0x40); }
void sfx_death(void)    { ch4(0xF7, 0x6A); ch1(0x1D, 0x80, 0xF7, 0x500); }
void sfx_tick(void)     { ch2(0x40, 0x81, 0x740, 8); }
void sfx_spawn(void)    { ch2(0x80, 0x72, 0x580, 12); }
void sfx_win(void)      { ch1(0x14, 0x80, 0xF7, 0x580); }
