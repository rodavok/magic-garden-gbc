#pragma bank 2
#include "hUGEDriver.h"
#include <stddef.h>

static const unsigned char song_win_c1p0[] = {
    DN(36,1,0x000),DN(40,1,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(38,1,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,1,0x000),DN(36,1,0x000),DN(33,1,0x000),DN(33,1,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(36,1,0x000),DN(90,0,0xE00),
    DN(40,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(31,1,0x000),
    DN(31,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(36,1,0x000),
    DN(90,0,0x000),DN(35,1,0x000),DN(36,1,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(31,1,0x000),DN(31,1,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(38,1,0x000),DN(90,0,0xE00),DN(36,1,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(33,1,0x000),
    DN(36,1,0x000),DN(36,1,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(38,1,0x000),DN(38,1,0x000),DN(36,1,0x000),DN(36,1,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(35,1,0x000),DN(90,0,0xE00),
    DN(31,1,0x000),DN(90,0,0x000),DN(36,1,0x000),DN(40,1,0x000),
};
static const unsigned char song_win_c1p1[] = {
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0xD00),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c2p0[] = {
    DN(24,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(19,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(19,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(19,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(23,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(19,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(26,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c2p1[] = {
    DN(24,2,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c3p0[] = {
    DN(90,0,0x000),DN(19,1,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(5,1,0x000),DN(90,0,0x000),
    DN(7,1,0x000),DN(90,0,0x000),DN(14,1,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(11,1,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(7,1,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(5,1,0x000),DN(90,0,0x000),
    DN(7,1,0x000),DN(90,0,0x000),DN(12,1,0x000),DN(90,0,0x000),
    DN(2,1,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(0,1,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(7,1,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(5,1,0x000),DN(90,0,0x000),
    DN(7,1,0x000),DN(90,0,0x000),DN(14,1,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(7,1,0x000),DN(90,0,0x000),DN(12,1,0x000),DN(90,0,0x000),
    DN(5,1,0x000),DN(90,0,0x000),DN(7,1,0x000),DN(90,0,0x000),
    DN(12,1,0x000),DN(90,0,0x000),DN(2,1,0x000),DN(90,0,0x000),
    DN(7,1,0x000),DN(90,0,0x000),DN(0,1,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c3p1[] = {
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c4p0[] = {
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_c4p1[] = {
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_win_order_cnt = 4;
static const unsigned char* const song_win_order1[] = { song_win_c1p0, song_win_c1p1 };
static const unsigned char* const song_win_order2[] = { song_win_c2p0, song_win_c2p1 };
static const unsigned char* const song_win_order3[] = { song_win_c3p0, song_win_c3p1 };
static const unsigned char* const song_win_order4[] = { song_win_c4p0, song_win_c4p1 };
/* The driver does `dec a` on the instrument id (0 means "no instrument"), so instrument 1 is
   entry [0] here. A leading "unused" row would hand the lead the wrong instrument - which is what
   used to happen: the melody played a decaying 50% patch while the harmony got the loud sustained
   one, and the tune sat underneath its own accompaniment. */
static const hUGEDutyInstr_t song_win_duty[] = {
    {0, 0x40, 0xF0, 0, 128},   /* 1 lead: 25% duty, full volume, sustained - it has to carry */
    {0, 0x80, 0x40, 0, 128},   /* 2 harmony: 50% duty at a quarter of the lead, stays underneath */
};
static const hUGEWaveInstr_t song_win_wave[] = {
    {0, 0x20, 0, 0, 128},      /* 1 bass: triangle at full volume - a different register from the lead, so it does not mask it */
};
static const hUGENoiseInstr_t song_win_noise[] = {
    {0xB1, 0, 0, 0, 0},        /* 1 kick: short */
    {0x71, 0, 0, 0, 0},        /* 2 snare: under the kick so the backbeat does not clutter */
};
static const unsigned char song_win_waves[] = {
    0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,   /* triangle, two cycles so the wave channel matches the pulse octave */
};
const hUGESong_t song_win = { 11, &song_win_order_cnt, song_win_order1, song_win_order2, song_win_order3, song_win_order4, song_win_duty, song_win_wave, song_win_noise, NULL, song_win_waves };

static const unsigned char song_lose_c1p0[] = {
    DN(31,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(35,1,0x000),DN(38,1,0x000),
    DN(38,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0xD00),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_lose_c2p0[] = {
    DN(26,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(19,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_lose_c3p0[] = {
    DN(7,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(0,1,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_lose_c4p0[] = {
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_lose_order_cnt = 2;
static const unsigned char* const song_lose_order1[] = { song_lose_c1p0 };
static const unsigned char* const song_lose_order2[] = { song_lose_c2p0 };
static const unsigned char* const song_lose_order3[] = { song_lose_c3p0 };
static const unsigned char* const song_lose_order4[] = { song_lose_c4p0 };
/* The driver does `dec a` on the instrument id (0 means "no instrument"), so instrument 1 is
   entry [0] here. A leading "unused" row would hand the lead the wrong instrument - which is what
   used to happen: the melody played a decaying 50% patch while the harmony got the loud sustained
   one, and the tune sat underneath its own accompaniment. */
static const hUGEDutyInstr_t song_lose_duty[] = {
    {0, 0x40, 0xF0, 0, 128},   /* 1 lead: 25% duty, full volume, sustained - it has to carry */
    {0, 0x80, 0x40, 0, 128},   /* 2 harmony: 50% duty at a quarter of the lead, stays underneath */
};
static const hUGEWaveInstr_t song_lose_wave[] = {
    {0, 0x20, 0, 0, 128},      /* 1 bass: triangle at full volume - a different register from the lead, so it does not mask it */
};
static const hUGENoiseInstr_t song_lose_noise[] = {
    {0xB1, 0, 0, 0, 0},        /* 1 kick: short */
    {0x71, 0, 0, 0, 0},        /* 2 snare: under the kick so the backbeat does not clutter */
};
static const unsigned char song_lose_waves[] = {
    0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,   /* triangle, two cycles so the wave channel matches the pulse octave */
};
const hUGESong_t song_lose = { 11, &song_lose_order_cnt, song_lose_order1, song_lose_order2, song_lose_order3, song_lose_order4, song_lose_duty, song_lose_wave, song_lose_noise, NULL, song_lose_waves };

static const unsigned char song_end_c1p0[] = {
    DN(31,1,0x000),DN(33,1,0x000),DN(33,1,0x000),DN(38,1,0x000),
    DN(90,0,0xE00),DN(31,1,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(31,1,0x000),DN(31,1,0x000),DN(33,1,0x000),
    DN(33,1,0x000),DN(38,1,0x000),DN(31,1,0x000),DN(31,1,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(50,1,0x000),
    DN(50,1,0x000),DN(33,1,0x000),DN(50,1,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(48,1,0x000),DN(48,1,0x000),DN(33,1,0x000),
    DN(48,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(47,1,0x000),
    DN(47,1,0x000),DN(33,1,0x000),DN(48,1,0x000),DN(90,0,0x000),
    DN(50,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(31,1,0x000),DN(33,1,0x000),DN(33,1,0x000),
    DN(38,1,0x000),DN(90,0,0xE00),DN(31,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(31,1,0x000),
    DN(33,1,0x000),DN(33,1,0x000),DN(38,1,0x000),DN(90,0,0xE00),
};
static const unsigned char song_end_c1p1[] = {
    DN(31,1,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,1,0x000),DN(31,1,0x000),DN(33,1,0x000),DN(33,1,0x000),
    DN(38,1,0x000),DN(31,1,0x000),DN(31,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(31,1,0x000),DN(50,1,0x000),
    DN(33,1,0x000),DN(50,1,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(48,1,0x000),DN(48,1,0x000),DN(33,1,0x000),DN(48,1,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(31,1,0x000),DN(33,1,0x000),
    DN(33,1,0x000),DN(38,1,0x000),DN(90,0,0xE00),DN(31,1,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,1,0x000),DN(33,1,0x000),DN(33,1,0x000),DN(38,1,0x000),
    DN(90,0,0xE00),DN(31,1,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0xD00),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c2p0[] = {
    DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(33,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(31,2,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(31,2,0x000),
    DN(33,2,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(31,2,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),
    DN(33,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c2p1[] = {
    DN(31,2,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),
    DN(33,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(31,2,0x000),DN(90,0,0x000),
    DN(33,2,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(31,2,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0xE00),
    DN(31,2,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c3p0[] = {
    DN(15,1,0x000),DN(90,0,0x000),DN(13,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0x000),
    DN(13,1,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(15,1,0x000),
    DN(15,1,0x000),DN(90,0,0x000),DN(13,1,0x000),DN(90,0,0x000),
    DN(15,1,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(15,1,0x000),DN(15,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0x000),
    DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),DN(15,1,0x000),
    DN(15,1,0x000),DN(90,0,0x000),DN(16,1,0x000),DN(90,0,0x000),
    DN(15,1,0x000),DN(90,0,0x000),DN(16,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(15,1,0x000),DN(19,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(14,1,0x000),
    DN(13,1,0x000),DN(90,0,0x000),DN(16,1,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c3p1[] = {
    DN(15,1,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(14,1,0x000),DN(13,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(14,1,0x000),DN(90,0,0x000),
    DN(13,1,0x000),DN(90,0,0x000),DN(16,1,0x000),DN(90,0,0x000),
    DN(15,1,0x000),DN(90,0,0xE00),DN(90,0,0x000),DN(90,0,0x000),
    DN(14,1,0x000),DN(90,0,0x000),DN(13,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(15,1,0x000),DN(90,0,0xE00),
    DN(90,0,0x000),DN(90,0,0x000),DN(14,1,0x000),DN(90,0,0x000),
    DN(13,1,0x000),DN(90,0,0x000),DN(8,1,0x000),DN(90,0,0x000),
    DN(5,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(5,1,0x000),DN(90,0,0x000),DN(13,1,0x000),DN(90,0,0x000),
    DN(16,1,0x000),DN(90,0,0x000),DN(90,0,0xE00),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c4p0[] = {
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_c4p1[] = {
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(24,1,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(24,1,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(36,2,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
    DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),DN(90,0,0x000),
};
static const unsigned char song_end_order_cnt = 4;
static const unsigned char* const song_end_order1[] = { song_end_c1p0, song_end_c1p1 };
static const unsigned char* const song_end_order2[] = { song_end_c2p0, song_end_c2p1 };
static const unsigned char* const song_end_order3[] = { song_end_c3p0, song_end_c3p1 };
static const unsigned char* const song_end_order4[] = { song_end_c4p0, song_end_c4p1 };
/* The driver does `dec a` on the instrument id (0 means "no instrument"), so instrument 1 is
   entry [0] here. A leading "unused" row would hand the lead the wrong instrument - which is what
   used to happen: the melody played a decaying 50% patch while the harmony got the loud sustained
   one, and the tune sat underneath its own accompaniment. */
static const hUGEDutyInstr_t song_end_duty[] = {
    {0, 0x40, 0xF0, 0, 128},   /* 1 lead: 25% duty, full volume, sustained - it has to carry */
    {0, 0x80, 0x40, 0, 128},   /* 2 harmony: 50% duty at a quarter of the lead, stays underneath */
};
static const hUGEWaveInstr_t song_end_wave[] = {
    {0, 0x20, 0, 0, 128},      /* 1 bass: triangle at full volume - a different register from the lead, so it does not mask it */
};
static const hUGENoiseInstr_t song_end_noise[] = {
    {0xB1, 0, 0, 0, 0},        /* 1 kick: short */
    {0x71, 0, 0, 0, 0},        /* 2 snare: under the kick so the backbeat does not clutter */
};
static const unsigned char song_end_waves[] = {
    0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,   /* triangle, two cycles so the wave channel matches the pulse octave */
};
const hUGESong_t song_end = { 11, &song_end_order_cnt, song_end_order1, song_end_order2, song_end_order3, song_end_order4, song_end_duty, song_end_wave, song_end_noise, NULL, song_end_waves };

