/* Headless SameBoy harness: run a ROM with scripted input, dump PPU state and screenshots.
   usage: dump <rom> <script> <outprefix>
   script: comma list of <frames>[:button]  (button: start a b up down left right select) */
#define GB_INTERNAL
#include "gb.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static uint32_t fb[160 * 144];
static uint32_t enc(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b) { (void)gb; return (r << 16) | (g << 8) | b; }
static void vblank(GB_gameboy_t *gb, GB_vblank_type_t t) { (void)gb; (void)t; }

static void save_ppm(const char *path) {
    FILE *f = fopen(path, "wb"); fprintf(f, "P6\n160 144\n255\n");
    for (int i = 0; i < 160 * 144; i++) { uint8_t p[3] = { fb[i] >> 16, fb[i] >> 8, fb[i] }; fwrite(p, 1, 3, f); }
    fclose(f);
}
static GB_key_t key_of(const char *s) {
    if (!strcmp(s, "start")) return GB_KEY_START; if (!strcmp(s, "select")) return GB_KEY_SELECT;
    if (!strcmp(s, "a")) return GB_KEY_A; if (!strcmp(s, "b")) return GB_KEY_B;
    if (!strcmp(s, "up")) return GB_KEY_UP; if (!strcmp(s, "down")) return GB_KEY_DOWN;
    if (!strcmp(s, "left")) return GB_KEY_LEFT; return GB_KEY_RIGHT;
}
static void dump_state(GB_gameboy_t *gb, const char *tag) {
    printf("== %s: LCDC=%02X STAT=%02X LY=%d SCX=%d SCY=%d VBK=%02X KEY1=%02X BGP=%02X\n", tag,
        GB_safe_read_memory(gb, 0xFF40), GB_safe_read_memory(gb, 0xFF41), GB_safe_read_memory(gb, 0xFF44),
        GB_safe_read_memory(gb, 0xFF43), GB_safe_read_memory(gb, 0xFF42), GB_safe_read_memory(gb, 0xFF4F),
        GB_safe_read_memory(gb, 0xFF4D), GB_safe_read_memory(gb, 0xFF47));
    printf("BG palette RAM:"); for (int i = 0; i < 64; i += 2) { if (i % 8 == 0) printf(" |"); printf(" %04X", gb->background_palettes_data[i] | (gb->background_palettes_data[i + 1] << 8)); } printf("\n");
    printf("OBJ palette RAM:"); for (int i = 0; i < 24; i += 2) { if (i % 8 == 0) printf(" |"); printf(" %04X", gb->object_palettes_data[i] | (gb->object_palettes_data[i + 1] << 8)); } printf("\n");
    /* tile map rows 0..17 (bank 0 tiles, bank 1 attrs) */
    uint8_t vbk = GB_safe_read_memory(gb, 0xFF4F);
    for (int bank = 0; bank < 2; bank++) {
        GB_write_memory(gb, 0xFF4F, bank);
        printf("map bank %d:\n", bank);
        for (int y = 0; y < 18; y++) { printf("  %2d:", y); for (int x = 0; x < 20; x++) printf(" %02X", GB_safe_read_memory(gb, 0x9800 + y * 32 + x)); printf("\n"); }
    }
    GB_write_memory(gb, 0xFF4F, vbk & 1);
}
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: dump rom script outprefix\n"); return 1; }
    GB_gameboy_t gb;
    GB_init(&gb, GB_MODEL_CGB_E);
    char boot[1024]; snprintf(boot, sizeof boot, "%s", getenv("SAMEBOY_BOOT") ? getenv("SAMEBOY_BOOT") : "cgb_boot.bin");
    if (GB_load_boot_rom(&gb, boot)) { fprintf(stderr, "no boot rom %s\n", boot); return 1; }
    if (GB_load_rom(&gb, argv[1])) { fprintf(stderr, "no rom\n"); return 1; }
    GB_set_pixels_output(&gb, fb);
    GB_set_rgb_encode_callback(&gb, enc);
    GB_set_vblank_callback(&gb, vblank);
    GB_set_color_correction_mode(&gb, GB_COLOR_CORRECTION_DISABLED);
    char *script = strdup(argv[2]); int shot = 0; char path[1024];
    for (char *tok = strtok(script, ","); tok; tok = strtok(NULL, ",")) {
        char *colon = strchr(tok, ':'); int n = atoi(tok); const char *btn = colon ? colon + 1 : NULL;
        if (btn) GB_set_key_state(&gb, key_of(btn), true);
        for (int i = 0; i < n; i++) GB_run_frame(&gb);
        if (btn) GB_set_key_state(&gb, key_of(btn), false);
        snprintf(path, sizeof path, "%s_%02d_%s.ppm", argv[3], shot, btn ? btn : "idle"); save_ppm(path);
        snprintf(path, sizeof path, "%02d_%s", shot, btn ? btn : "idle"); dump_state(&gb, path); shot++;
    }
    GB_free(&gb);
    return 0;
}
