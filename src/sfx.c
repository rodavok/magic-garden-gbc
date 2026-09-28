#pragma bank 1
#include <gb/gb.h>
#include <gb/hardware.h>
#include "sfx.h"
#include "music.h"
#include "sfx_tables.h"

/* Register-level sound effects.
   Channel 1 carries the melody, so nothing that fires during play is allowed to touch it: every
   gameplay effect lives on channel 2 (the harmony, which sounds on about one row in seven) or on
   channel 4 (drums). Only death uses channel 1, and by then the track is ending.
   Channel 2 has no hardware sweep, so sfx_update() walks the frequency itself, one or two sweep
   steps a frame, writing the pitch without the restart bit so the envelope keeps running.
   The effects measured from the original (pickup, jump, power-up) are per-frame tables from
   tools/sfx_tables.py: one pitch a frame, retriggering only where the table sets a new volume.
   Every effect peaks at about 10 so it stays under the melody (CH1 lead at 15). */
static struct { uint8_t frames, shift, down; uint16_t freq; } sw;
static const sfx_step_t *seq;
static uint8_t seq_left;

void sfx_init(void) {
    NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
    sw.frames = 0; seq_left = 0;
}

static void ch1(uint8_t sweep, uint8_t duty_len, uint8_t env, uint16_t freq) {
    music_sfx_hold(1, 20);
    NR10_REG = sweep; NR11_REG = duty_len; NR12_REG = env;
    NR13_REG = (uint8_t)freq; NR14_REG = 0x80 | (uint8_t)(freq >> 8);
}
static void ch2(uint8_t duty_len, uint8_t env, uint16_t freq, uint8_t frames) {
    sw.frames = 0; seq_left = 0;
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

static void seq_step(void) {
    const sfx_step_t *st = seq++;
    if (st->env) { NR22_REG = st->env; NR23_REG = (uint8_t)st->x; NR24_REG = 0x80 | (uint8_t)(st->x >> 8); }
    else { NR23_REG = (uint8_t)st->x; NR24_REG = (uint8_t)(st->x >> 8); }
    seq_left--;
}
void sfx_prog(uint8_t id) {
    const sfx_prog_t *p = &sfx_progs[id];
    sw.frames = 0;
    music_sfx_hold(2, p->len + 1);
    NR21_REG = p->duty; seq = p->steps; seq_left = p->len;
    seq_step();
}

void sfx_update(void) {
    uint8_t k;
    if (seq_left) { seq_step(); return; }
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

void sfx_pickup(void)   { sfx_prog(SFX_PICKUP_A + (DIV_REG & 3)); }   /* the original picks one of four */
void sfx_save(void)     { ch2sw(0x80, 0xA3, 1400, 6, 0, 18); }   /* 200 Hz sweeping up */
void sfx_bad_drop(void) { ch2sw(0x40, 0xA4, 1700, 5, 1, 18); }   /* 380 Hz sagging down */
void sfx_jump(void)     { sfx_prog(SFX_JUMP); }
void sfx_flask(void)    { sfx_prog(SFX_POWERUP); }
void sfx_kill(void)     { sfx_prog(SFX_EAT); }
void sfx_death(void)    { seq_left = 0; sw.frames = 0; ch4(0xF7, 0x6A); ch1(0x1D, 0x80, 0xF7, 0x500); }
void sfx_tick(void)     { sfx_prog(SFX_TICK); }
