# BAG2JP System Configuration Documentation

## Project Overview

BAG2JP is a PSXRecomp-based project that recompiles the PlayStation 1 game "Bust A Groove 2 (Japan)" to run on modern hardware. It modifies the original disc image using overlays and patches to enhance gameplay while maintaining compatibility with the original game content.

## Main Configuration Files

### 1. Game Configuration (`patches/BAG2JP-game.toml`)

This file contains all core system settings for the recompiled game:

```toml
[game]
name = "BAG2JP"
id = "SLPM-86219"
players = 2
exe = "disc/SLPM_862.19"
disc = "/sessions/rcw-01dqypkmdcqawmgypjuqnq31/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue"
load_address = "0x80010000"
entry_pc = "0x80035D98"
text_size = "0x0004D000"
stack_base = "0x801FFFF0"

[recompiler]
seeds = "seeds/ghidra_funcs.txt"
out_dir = "generated"
strict = true

[runtime]
window_title = "BAG2JP Recompiled"
memcard_dir = "saves"
overlay_cache = true

[video]
renderer = "opengl"
aspect_ratio = "4:3"
internal_resolution = "4k"
render_thread = true
geometry_correction = true
perspective_texturing = true
pgxp_depth_buffer = false
texture_filtering = "xbr"
texture_lod = "mipmap"
anisotropic_filtering = 8
dithering = "off"
antialiasing_mode = "off"
antialiasing = true
fmv_filter = "bicubic"
fmv_chroma_smoothing = true

[widescreen]
native_wide = false
gte_game_mode = true
hud_sprt_squash = false
auto_ui_squash = false
auto_ui_anchor = "in_place"
auto_ui_size = "original"
clear_reveal = true

[controller]
default_mode = "digital"

[netplay]
require_cue = true
required_tracks = 1
required_disc_fp = "40ad17afa68eed98be76728e23b9558229989bce72a2be7f7db469771ff626a8"

[audio]
buffer_ms = 90
```

### 2. User Settings (`installer/settings.toml`)

This file contains user-specific configuration:

```toml
[video]
renderer          = "opengl"
window_width      = 1920
fast_boot         = false
bios_hle          = true
fullscreen        = 0
render_thread = false
present_thread = false
frame_generation = false
vsync             = "on"
frame_interpolation = false
frame_interpolation_fps = 0
aspect_ratio      = "4:3"

[hotkeys]
rewind_pad = 1272
save_state_menu_pad = 2040
fast_forward_speed = 4
fast_forward_mode = "hold"
fast_forward_pad = 1528
fast_forward_toggle_pad = 0

[launcher]
skip_launcher = false

[netplay]
player_name = "Player"
lobby_url = "ws://netplay.retcomm.net:8765"

[disc]
path = "disc_image/game.cue"

[memcard]
dir     = "saves"
card1   = "saves/card1.mcd"
card2   = "saves/card2.mcd"
enable1 = true
enable2 = true

[controller]
p1_device = "keyboard"
p1_mode   = "digital"
p1_deadzone = 3276
p2_device = "none"
p2_mode   = "digital"
p2_deadzone = 3276
multitap  = true
multitap_analog = true
deadzone  = 3276

[localization]
language = "en"
```

## Feature Structure

The project uses a modular approach with features defined in various manifest.toml files under `mods-src/` directory. Examples include:

1. **Bag1 Content**: Imports BAG1 characters, stages, and songs
2. **HD Intro**: Replaces original intro with HD video file
3. **Widescreen Support**: Enhances display capabilities beyond 4:3 
4. **Netplay Support**: Multiplayer functionality

## Mod Structure

Each mod has a manifest.toml file that defines:
- Feature identification
- Plugin information
- Resources and options
- Overlay specifications for in-game modifications
- Target game compatibility

This modular system allows for easy enabling/disabling of specific features and enhances maintainability.
