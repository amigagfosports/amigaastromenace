# Autobuild

How LumaVAULT's nightly build (bigguy, 23:00 to 06:00) builds this repository. The form is in lumavault-server
`docs/AUTOBUILD.md`.

## amigaastromenace

The release archive on the open9 stove: scripts/nightly.sh runs package/build-amiga.sh with the night's minutes,
since the kitchen's 2700 s limit is too short beside other builds. The .lha, its .sha256 and build-info.json (which
compiler built it) go to the warehouse's Nightly folder only. Nothing is published.

- frequency: nightly
- kind: app
- script: scripts/nightly.sh
- keep: out/*.lha out/*.sha256 out/build-info.json
- minutes: 120
