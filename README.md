# AstroMenace — AmiCradle AC090

**Status:** OPEN8 NATIVE BUILD + RC1 TEST PACKAGE VERIFIED; FIRST-LIGHT GUEST QUALIFICATION PENDING (16 NOV 2026)

## Upstream

- repository: https://github.com/viewizard/astromenace.git
- pinned commit: `bbdb3ac5af2774c92b85c4d9b2a238f606911e66`
- source licence: GPL-3.0-or-later
- notable upstream change: this pin includes the 6 August 2026 GCC 16 startup-hang fix.

## AmiCradle treatment

The target is AmigaOS 3.x / AC090 / 68040 + FPU.

- SDL2 comes from the OpenGPU SDK (`sdl2-config --libs --gl`).
- OpenGL comes from OpenGPU's GL.module (Mesa): virgl on the host GPU where there is one, softpipe on the 68k otherwise.
- audio goes through the SDK's SDL2_mixer to AHI (`audio_amicradle.cpp` replaces the OpenAL backend); the port bundles no second audio stack.
- music themes (13-31 MB once decoded) are decoded on a background thread, the loop part while the intro plays, so starting a theme never stops the game; mixer channels 0-3 are reserved for music, so sound effects never take, halt or re-volume a music channel.
- mipmaps: the GLU shim calls `glGenerateMipmap` once after each upload, not the legacy flag that rebuilds every level on each sub-update.
- built with `-fno-tree-loop-distribute-patterns`, as the OpenGPU SDK asks for GCC 16.
- the build takes the `STOVE` it is given (open9 is current) and records which compiler built it in `build-info.json` (scripts/record_stove.py); there is no compiler certificate check. The release build is `build-amigaos3-runtime-fixed.sh`: it applies the target patches (the VFS, VW3D, VW2D and TGA readers made explicitly little-endian, the `AMICRADLE` define the CMake option alone does not set, the target random seed, the screenshot readback, the optional joystick) and then `build-amigaos3.sh`, and packages a launcher that gives the game a 1 MiB stack plus a ready `gamedata.vfs`. `build-amigaos3.sh` on its own makes a binary without them, which aborts at start on the 68k.

## Running it fast

- A truecolour RTG screen and openrtg.library 0.15 or later, so each frame goes straight to the screen: `GetEnv GLAPresent` says `direct`. Otherwise every frame is read back and copied, about a quarter of the 68k's time.
- SDL2.module 3 with the text-input fix (gfopenrtg #67) for the pilot name. The game needs no relink for it.
- `SDL_OPENGPU_STATS=1` shows what is drawn where. VSync in the game's options does nothing: OpenGPU stores the swap interval but does not wait.
- Known cost: each texture or buffer transfer is a synchronous round trip to the host, and client-side vertex arrays (AstroMenace's 2D and text) are copied every draw. Screens with many strings (the pilot profile) pay that per string.
- Ogg/Vorbis and FreeType are shared SDK dependencies, not private copies carried by the game.
- target-side VFS generation is disabled during cross-build; runtime data packaging is a separate, reproducible release step.

## Installing

`package/build-amiga.sh` (Cradle's `package` target, with `STOVE` and `OUT`)
builds the game as `build-amigaos3-runtime-fixed.sh` does and packs
`AstroMenace-VERSION-68040.lha`. The archive holds the AstroMenace drawer
(the launcher, `AstroMenace.bin`, `gamedata.vfs`, the licences and the
README, with GlowIcons from `icons/`), its icon, and `Install-AstroMenace`.
Unpack it anywhere and double-click Install-AstroMenace: it checks the CPU,
the FPU and the GFOpenGPU modules (SDL2, SDL2_mixer, GL), asks where the
game goes (Work:Games by default) and copies the drawer there. Installing
again over it keeps `config.xml` and the pilot profiles. `package/installer.json`
is its spec (DalsinAI/amicradle's `scripts/ports/port_installer.py` writes
the script and its icon).

## Open8 RC1 engineering test candidate (16 November 2026)

A fresh pinned-source build on daletop produced an AmigaOS HUNK game binary
(`AstroMenace.bin`), the dedicated 1 MiB-stack launcher (`AstroMenace`), and
a prebuilt 518-entry `gamedata.vfs`. Both binaries pass the 68040 FPCR scan.
Twelve focused VFS/Open8 staging tests pass; Open8 receipt verifies 2,756
compiler/runtime files. LHA and ZIP test packages are integrity-verified; the
LHA also extracts byte-identically. See
`evidence/open8-build-20261116.json`.

**This is NOT yet a guest-qualified RC**. Source and data build success is not
proof of title, workshop, first mission, audio, text entry, graphics
performance or clean exit. In particular, the OpenGPU SDL2/GL/SDL2_mixer
client libraries imported into the Open8 stage came from a previously built
SDK donor, and are not newly rebuilt Open8 modules.

## First gate

1. clean GCC16/0009 Kitchen build;
2. title/menu;
3. ship configuration;
4. first mission and rendered 3D scene;
5. keyboard/pad input, including typing the pilot name;
6. audio through OpenAudio;
7. clean exit;
8. `GLAPresent` is `direct`, and the menu and first level hold a measured frame rate.

**DONE means RELEASE.** Compile success alone does not make this port done.
