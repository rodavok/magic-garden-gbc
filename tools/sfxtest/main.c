/* Sound-effect test ROM for tools/sfx_page.py: after a quiet lead-in, plays every effect in sfx.c in
   turn, one every GAP frames, with no music. The order must match PORT in tools/sfx_page.py. */
#include <gb/gb.h>
#include "sfx.h"
#include "sfx_tables.h"
#define LEAD 240
#define GAP  150
static void pickup_a(void) { sfx_prog(SFX_PICKUP_A); }
static void pickup_b(void) { sfx_prog(SFX_PICKUP_B); }
static void pickup_c(void) { sfx_prog(SFX_PICKUP_C); }
static void pickup_d(void) { sfx_prog(SFX_PICKUP_D); }
static void (* const fx[])(void) = {
    pickup_a, pickup_b, pickup_c, pickup_d, sfx_jump, sfx_bad_drop, sfx_save, sfx_flask, sfx_kill, sfx_tick, sfx_death
};
#define N (sizeof fx / sizeof fx[0])
void main(void) {
    uint16_t t = 0; uint8_t k = 0;
    SWITCH_ROM(1);
    sfx_init();
    while (1) {
        wait_vbl_done();
        sfx_update();
        if (k < N && t == LEAD + (uint16_t)k * GAP) { fx[k](); k++; }
        t++;
    }
}
