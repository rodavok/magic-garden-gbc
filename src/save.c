#pragma bank 1
#include <gb/gb.h>
#include <string.h>
#include "save.h"

save_t SAVE;
static save_t __at(0xA000) sram_rec;   /* MBC5 cartridge RAM, bank 0 */

static uint8_t checksum(const save_t *s) {
    const uint8_t *p = (const uint8_t *)s; uint8_t c = 0x5A, i;
    for (i = 0; i < sizeof(save_t) - 1; i++) c = (uint8_t)(c + p[i] * 3 + 1);
    return c;
}

void save_store(void) {
    SAVE.checksum = checksum(&SAVE);
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy(&sram_rec, &SAVE, sizeof(save_t));
    DISABLE_RAM;
}

void save_load(void) {
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy(&SAVE, &sram_rec, sizeof(save_t));
    DISABLE_RAM;
    if (SAVE.magic[0] != 'M' || SAVE.magic[1] != 'G' || SAVE.magic[2] != '0' || SAVE.magic[3] != '1' || SAVE.checksum != checksum(&SAVE)) {
        memset(&SAVE, 0, sizeof(save_t));
        SAVE.magic[0] = 'M'; SAVE.magic[1] = 'G'; SAVE.magic[2] = '0'; SAVE.magic[3] = '1';
        save_store();
    }
}

uint8_t save_insert(uint32_t score, uint16_t saved, uint8_t drop, uint8_t chain, uint16_t kills) {
    uint8_t rank = 0, i;
    for (i = 0; i < HS_ENTRIES; i++) if (score > SAVE.table[i].score) { rank = i + 1; break; }
    if (rank) {
        for (i = HS_ENTRIES - 1; i >= rank; i--) SAVE.table[i] = SAVE.table[i - 1];
        SAVE.table[rank - 1].score = score; SAVE.table[rank - 1].saved = saved;
    }
    if (drop > SAVE.best_drop) SAVE.best_drop = drop;
    if (chain > SAVE.best_chain) SAVE.best_chain = chain;
    if (kills > SAVE.total_kills) SAVE.total_kills = kills;
    SAVE.games++;
    save_store();
    return rank;
}
