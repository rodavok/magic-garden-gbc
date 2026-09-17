#ifndef SAVE_H
#define SAVE_H
#include <stdint.h>
#define HS_ENTRIES 5
typedef struct {
    uint32_t score;
    uint16_t saved;
} hs_entry_t;
typedef struct {
    uint8_t magic[4];
    hs_entry_t table[HS_ENTRIES];
    uint8_t best_drop;      /* biggest drop-off */
    uint8_t best_chain;     /* most enemies cleared at once */
    uint16_t total_kills;   /* most enemies cleared total (best run) */
    uint16_t games;
    uint8_t checksum;
} save_t;
extern save_t SAVE;          /* RAM copy of the battery-backed record */
void save_load(void);        /* read SRAM into SAVE, initialising it if the record is missing or corrupt */
void save_store(void);       /* write SAVE back to SRAM */
uint8_t save_insert(uint32_t score, uint16_t saved, uint8_t drop, uint8_t chain, uint16_t kills);  /* returns rank 1-5 or 0 */
#endif
