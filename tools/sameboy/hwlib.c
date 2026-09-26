/* SameBoy core as a shared library for tools/hw_check.py: run frames, poke RAM, press keys, and count
   every write that real hardware would drop - VRAM while the PPU owns it (mode 3) and CGB palette data
   while it is locked - with the scanline it happened on. PyBoy performs those writes, so it cannot see
   this class of bug.
   build: see tools/hw_check.py (it compiles this on first use) */
#define GB_INTERNAL
#include "gb.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static GB_gameboy_t gb;
static uint32_t fb[160 * 144];
static uint32_t frame_no;
#define LOG_MAX 4096
typedef struct { uint32_t frame; uint16_t addr; uint8_t ly, value, kind; } hw_event_t;   /* kind 1 VRAM, 2 palette; bit 4 VRAM bank 1 */
static hw_event_t events[LOG_MAX];
static uint32_t n_events, n_vram_blocked, n_pal_blocked, n_vram_writes;

static bool on_write(GB_gameboy_t *g, uint16_t addr, uint8_t value) {
    uint8_t kind = 0;
    if (addr >= 0x8000 && addr < 0xA000) {
        n_vram_writes++;
        if (g->vram_write_blocked) { kind = 1 | (g->cgb_vram_bank << 4); n_vram_blocked++; }
    } else if ((addr == 0xFF69 || addr == 0xFF6B) && g->cgb_palettes_blocked) { kind = 2; n_pal_blocked++; }
    if (kind && n_events < LOG_MAX) {
        hw_event_t *e = &events[n_events++];
        e->frame = frame_no; e->addr = addr; e->ly = g->io_registers[GB_IO_LY]; e->value = value; e->kind = kind;
    }
    return true;   /* let it through: SameBoy drops it itself, exactly as the hardware would */
}
static uint32_t enc(GB_gameboy_t *g, uint8_t r, uint8_t gg, uint8_t b) { (void)g; return (r << 16) | (gg << 8) | b; }
static void vblank(GB_gameboy_t *g, GB_vblank_type_t t) { (void)g; (void)t; }

int hw_init(const char *rom, const char *boot) {
    static bool live;
    if (live) GB_free(&gb);
    live = true; frame_no = 0; n_events = n_vram_blocked = n_pal_blocked = n_vram_writes = 0;
    GB_init(&gb, GB_MODEL_CGB_E);
    if (GB_load_boot_rom(&gb, boot)) return 1;
    if (GB_load_rom(&gb, rom)) return 2;
    GB_set_pixels_output(&gb, fb);
    GB_set_rgb_encode_callback(&gb, enc);
    GB_set_vblank_callback(&gb, vblank);
    GB_set_color_correction_mode(&gb, GB_COLOR_CORRECTION_DISABLED);
    GB_set_write_memory_callback(&gb, on_write);
    return 0;
}
void hw_frame(void) { GB_run_frame(&gb); frame_no++; }
uint8_t hw_rd(uint16_t addr) { return GB_safe_read_memory(&gb, addr); }
/* WRAM/HRAM pokes only (the game struct): go straight through the bus */
void hw_wr(uint16_t addr, uint8_t v) { GB_write_memory(&gb, addr, v); }
uint8_t hw_vram(uint8_t bank, uint16_t addr) { return gb.vram[(bank ? 0x2000 : 0) + (addr - 0x8000)]; }
uint8_t hw_bg_palette(uint8_t i) { return gb.background_palettes_data[i]; }
void hw_key(int key, int down) { GB_set_key_state(&gb, (GB_key_t)key, down != 0); }
uint32_t hw_frame_no(void) { return frame_no; }
uint32_t hw_counts(uint32_t *vram_blocked, uint32_t *pal_blocked, uint32_t *vram_writes) {
    *vram_blocked = n_vram_blocked; *pal_blocked = n_pal_blocked; *vram_writes = n_vram_writes; return n_events;
}
void hw_event(uint32_t k, uint32_t *frame, uint16_t *addr, uint8_t *ly, uint8_t *value, uint8_t *kind) {
    hw_event_t *e = &events[k]; *frame = e->frame; *addr = e->addr; *ly = e->ly; *value = e->value; *kind = e->kind;
}
void hw_reset_counts(void) { n_events = n_vram_blocked = n_pal_blocked = n_vram_writes = 0; }
void hw_screen(const char *path) {
    FILE *f = fopen(path, "wb"); fprintf(f, "P6\n160 144\n255\n");
    for (int i = 0; i < 160 * 144; i++) { uint8_t p[3] = { fb[i] >> 16, fb[i] >> 8, fb[i] }; fwrite(p, 1, 3, f); }
    fclose(f);
}
