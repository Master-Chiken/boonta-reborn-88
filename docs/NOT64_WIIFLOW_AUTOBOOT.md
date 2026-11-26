# Not64 + WiiFlow Lite: automatic launch of the original N64 game

**Status:** launch path verified in source; physical Wii/vWii validation is pending.

This is a reference/emulation route for a locally owned N64 game image. It is not Boonta Reborn 88's native GameCube/Wii engine or a native recompilation.

## Source-verified launch sequence

1. WiiFlow Lite reads the plugin INI, substitutes path tokens, and creates the DOL argument list.
2. It starts the configured Not64 DOL and passes the arguments.
3. Not64 accepts the `rompath` string and `SkipMenu` integer options.
4. Its menu initialization calls the automatic ROM loader, which opens the ROM directory and selects the matching file.
5. If loading succeeds and `SkipMenu=1`, Not64 starts the game without waiting at its regular menu.

Sources:
- Not64 options and argument parsing: https://github.com/extremscorner/not64/blob/d35a7a1c454eca973995939dbca3f06725cf4a6e/main/main_gc-menu2.cpp
- Not64 auto-path handling: https://github.com/extremscorner/not64/blob/d35a7a1c454eca973995939dbca3f06725cf4a6e/menu/LoadRomFrame.cpp
- Not64 auto-selection and SkipMenu: https://github.com/extremscorner/not64/blob/d35a7a1c454eca973995939dbca3f06725cf4a6e/menu/FileBrowserFrame.cpp
- Not64 menu initialization: https://github.com/extremscorner/not64/blob/d35a7a1c454eca973995939dbca3f06725cf4a6e/menu/MenuContext.cpp
- WiiFlow Lite argument building and plugin launch: https://github.com/Fledge68/WiiFlow_Lite/blob/69c0d4d61984f4ed6fca51b4520320cadfac960d/source/plugin/plugin.cpp and https://github.com/Fledge68/WiiFlow_Lite/blob/69c0d4d61984f4ed6fca51b4520320cadfac960d/source/menu/menu_game_boot.cpp

## WiiFlow Lite plugin INI

A known Not64 plugin configuration is:

```ini
[PLUGIN]
arguments=rompath = "{device}:/{path}/{name}"|SkipMenu = 1
bannersound=ZZ--Sounds/N64.ogg
consolecoverid=Nintendo
covercolor=000000
coverfolder=Nintendo/N64
displayname=Nintendo 64 (Not64)
dolfile=N64/not64.dol
filetypes=.n64|.v64|.z64|.zip
magic=4E4F3634
romdir=not64/roms
rompartition=-1
```

WiiFlow Lite stores plugin arguments as a pipe-separated list. The quoted ROM path allows Not64's option parser to retain spaces in the path. The `romdir` value is relative to the selected ROM partition; do not prefix it with `SD:/` or `USB:/`.

## Suggested first-test layout

Use one FAT-formatted volume and one partition for the Not64 plugin DOL and ROM during the first test:

```text
SD:/
├── wiiflow/
│   └── plugins/
│       └── N64/
│           ├── not64.ini
│           └── not64.dol
└── not64/
    └── roms/
        └── racer.z64
```

The plugin DOL must match the `dolfile` path. An optional separate Homebrew Channel installation can live at `apps/not64/boot.dol`; that is not the path referenced by this plugin example.

## Storage caveats

- **Start with FAT32 on SD or USB**, keeping the plugin DOL and ROM on the same partition.
- Not64's Wii auto-loader rewrites a ROM path beginning with `usb` to its `fat` alias before opening it.
- Avoid NTFS for the first test. WiiFlow Lite can identify NTFS, but the Not64 auto-loader code inspected here specifically converts the `usb` prefix; the complete NTFS auto-launch path is unverified.
- Cross-partition loading should be tested only after the same-partition setup works.
- Not64 uses the first boot argument (the DOL path) to select its SD or FAT settings path. Keeping everything on one device reduces variables.

## Hardware validation checklist

Record each item as **pass**, **fail**, or **not tested**:

1. WiiFlow Lite detects the N64 plugin and lists the local Racer ROM.
2. Selecting Racer launches the configured Not64 DOL.
3. Not64 mounts the intended storage and loads the exact ROM.
4. `SkipMenu=1` bypasses the emulator menu and the original game reaches its own title screen.
5. Controller navigation works in the game's menu.
6. A race starts; steering, acceleration, braking, camera, graphics and audio are observed.
7. A race can be completed; save behavior, exit and relaunch are checked.
8. The same launch succeeds again after a console reboot.

This checklist is not a report of completed testing. No physical Wii/vWii launch has been performed as part of this source review.

The latest published Not64 release at the time of this review is [20260410](https://github.com/extremscorner/not64/releases/tag/20260410), published 2026-04-10. The source review is pinned to Not64 commit `d35a7a1c454eca973995939dbca3f06725cf4a6e` (2026-04-10) and WiiFlow Lite commit `69c0d4d61984f4ed6fca51b4520320cadfac960d` (2026-08-19), so later changes to either `master` branch do not silently alter the references above. Historical compatibility records list Star Wars Episode I: Racer as playable on an older Not64 version but report some graphical defects. This is promising prior evidence, not proof that the 20260410 release works perfectly on every Wii configuration.

## Separation from the native Boonta project

- **Immediate reference route:** run the original game through Not64 and WiiFlow Lite.
- **Long-term native route:** independently reconstruct behavior and data formats, prove MIPS-to-PowerPC feasibility, and implement a native Wii/GameCube GX renderer.

Not64 is an emulator; this method does not convert the N64 ROM into a native Wii DOL. Keep ROMs, saves, emulator binaries and extracted proprietary game assets out of the public repository. A legally obtained ROM stays on the owner's device.
