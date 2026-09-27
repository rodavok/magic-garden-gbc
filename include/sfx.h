#ifndef SFX_H
#define SFX_H
#include <stdint.h>
void sfx_init(void);
void sfx_update(void);   /* once a frame: drives the software sweep on channel 2 */
void sfx_pickup(void);
void sfx_save(void);
void sfx_bad_drop(void);
void sfx_jump(void);
void sfx_flask(void);
void sfx_kill(void);
void sfx_death(void);
void sfx_tick(void);
void sfx_prog(uint8_t id);   /* one table from sfx_tables.h (SFX_*) */
#endif
