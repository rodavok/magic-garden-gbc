#pragma bank 1
#include <gb/gb.h>
#include <gb/hardware.h>
#include "sfx.h"
#include "music.h"

/* Direct register sound effects: channel 1 (sweep pulse), 2 (pulse), 4 (noise). */
void sfx_init(void) {
    NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
}
static void ch1(uint8_t sweep, uint8_t duty_len, uint8_t env, uint16_t freq) {
    music_sfx_hold(1, 20);
    NR10_REG = sweep; NR11_REG = duty_len; NR12_REG = env;
    NR13_REG = (uint8_t)freq; NR14_REG = 0x80 | (uint8_t)(freq >> 8);
}
static void ch2(uint8_t duty_len, uint8_t env, uint16_t freq) {
    music_sfx_hold(2, 16);
    NR21_REG = duty_len; NR22_REG = env;
    NR23_REG = (uint8_t)freq; NR24_REG = 0x80 | (uint8_t)(freq >> 8);
}
static void ch4(uint8_t env, uint8_t poly) {
    music_sfx_hold(8, 24);
    NR41_REG = 0x00; NR42_REG = env; NR43_REG = poly; NR44_REG = 0x80;
}
void sfx_pickup(void)   { ch2(0x80, 0xF1, 0x77D); }
void sfx_save(void)     { ch1(0x13, 0x80, 0xF4, 0x600); }
void sfx_bad_drop(void) { ch1(0x1B, 0x40, 0xF5, 0x520); }
void sfx_jump(void)     { ch1(0x12, 0x80, 0xA2, 0x680); }
void sfx_flask(void)    { ch2(0xC0, 0xF4, 0x6C0); }
void sfx_kill(void)     { ch4(0xF2, 0x40); }
void sfx_death(void)    { ch4(0xF7, 0x6A); ch1(0x1D, 0x80, 0xF7, 0x500); }
void sfx_tick(void)     { ch2(0x40, 0x81, 0x740); }
void sfx_spawn(void)    { ch2(0x80, 0x72, 0x580); }
void sfx_win(void)      { ch1(0x14, 0x80, 0xF7, 0x580); }
