# MFR Revival — Dev Blog #1: Cracking open the client

*Marvel Future Revolution private-server feasibility study. First look at the APK.*

## TL;DR

I cracked open the MFR Android client (v2.0.3) and mapped how it talks to the network.
Good news: it's built on **stock Unreal Engine 4 networking** and the binary is **wide open
and readable** — full class names, enums, and a complete list of the game's server services.
Bad news: it's a textbook **always-online MMO** — the gameplay logic lived server-side, the
game server address was handed out dynamically at login, and all of Netmarble's backend is
dead. No magic shortcut, but the client tells us a *lot*.

## What I actually looked at

The `.apk` is 1.75 GB, but almost all of that is `assets/main.obb.png` (1.6 GB of game
assets, disguised) — useless for networking. The parts that matter:

- `lib/arm64-v8a/libUE4.so` (132 MB) — the whole game. Netcode + crypto live here.
- `classes.dex` (8.2 MB) — the Android/Java wrapper (Netmarble SDK, login glue).
- `assets/UE4CommandLine.txt` → `../../../Monster/Monster.uproject` (internal codename: **"Monster"**).
- Build tag: **Singular SDK v9.6.0**, built **13 Jan 2021**.

Netmarble's own security libs are present (`libnmsssa.so`, the `.nmss` files = **NMSS**,
Netmarble Security Service). Worth keeping in mind, but the main `libUE4.so` is **not packed**
at the string level — it read clean, which is the single luckiest break so far.

## The architecture (two layers)

MFR's networking splits cleanly in two:

**1. Platform layer — HTTPS/REST (libcurl + OpenSSL).** Login, account, agreements,
billing, logging, and *the server list*. Talks to Netmarble/GalaxyMX backends. Endpoints
baked into the binary:

- `apis.netmarble.com`, `alpha-apis.netmarble.com`, `dev-apis.netmarble.com`
- `mobileapi.netmarble.com/v2/commonCs/getKey`  ← auth key handoff
- `agreement-rest.netmarble.com`, `nmbillgw.netmarble.com` (billing), `netmarbleslog.netmarble.com`
- `apis.galaxymx.com`, `nmslog.galaxymx.com` (GalaxyMX = the game platform backend)

Auth flow uses a **`GameToken` / `channelKey`** obtained from the platform. All of this is
plain REST — which means it can be **stubbed/faked locally** once we point the client at our
own server (the classic "point the client at yourself" trick).

**2. Game layer — Unreal Engine 4 NetDriver + PacketHandler.** Real-time gameplay rides
UE4's own replication protocol. Confirmed handlers: **`/Script/PacketHandler`** +
**`/Script/OodleHandlerComponent`** (OodleNetwork compression). No *custom* encryption
handler was compiled in by name — so packet crypto is likely either stock or absent at that
layer (⚠️ needs confirming from `DefaultEngine.ini` inside the paks, which I haven't pulled yet).

**Why layer 2 matters:** it's *stock UE4*, which is open-source. We're not reversing a
from-scratch protocol — we're reversing Netmarble's game-specific replicated classes on top
of a documented engine. That's a massive head start.

## The game's service map

The client references a complete taxonomy of server services (~53 real ones, after filtering
out OpenSSL noise). This is basically the game server's API surface:

```
ACCOUNT      CHARACTER    INVENTORY    ITEM        SHOP        MAIL
ZONE         ZONE_CREATE  ENTITY       SKILL       MASTERY     SUPERPOWER
ARENA        FRIENDLY_ARENA  RAID      ALLIANCE_RAID  CITYWAR   CONFLICT
COOP         BOUNTYHUNT   EPIC_INVASION  IMPACTSTAGE  SQUAD_BATTLE  SQUAD_HQ
SQUADLEVEL   PARTY        BUDDY        CHAT         ALLIANCE    SIDEKICK
MISSION      TUTORIAL     TRAINING     TRAINGROUND  ACHIEVE     EVENTACHIEVEMENT
ATTENDANCE   OMEGACARD    FUTUREPASS   MASTERY      TITLE       WARDROBTHEME
DICTIONARY   COOLTIME     CONTENTOPEN  ROULETTE_EVENT  SHOP     GMTOOL (dev)
```

Plus `MONSTER_SYNC_TO_SERVER`, server-authoritative movement/combat move-checks
(`EPSCheckMoveType::MONSTER_SYNC_TO_SERVER`, `SkillMoveServer`) — i.e. the server was the
referee for everything. Worst case for a revival, but exactly what the client symbols help
us reconstruct.

## Honest verdict

- **Favorable:** stock UE4 (open-source base), unpacked & symbol-rich client, and a fully
  enumerated service map. This is about the best *structure* you can hope for in an MMO revival.
- **The wall:** every one of those ~53 services' actual message contents and logic lived on
  dead servers. Rebuilding means reversing the client's serialization for each, service by
  service — and there are **no known pre-shutdown packet captures** (still the #1 thing that
  would accelerate everything).
- **Scale reality:** Marvel Heroes took a team ~2.5 years, *and* that game kept more logic
  client-side than MFR did. Solo + no captures, "log in and stand in an empty zone" is a
  serious multi-month goal; a playable game is a long, long road.

## Next steps

1. Pull `DefaultEngine.ini` / netcode config from the paks to confirm the PacketHandler
   component list (is there packet encryption or just Oodle?).
2. Decompile `classes.dex` (jadx) to trace the exact login → `GameToken` → server-list flow.
3. Map the UE4 version precisely to line up with the matching open-source engine source.
4. Stand up a **fake platform server** (stub the REST endpoints) and redirect the client to it —
   goal: get the client past login and *asking* for a game server. First real milestone.
5. Keep hunting for **packet captures**. Still the make-or-break.

*Filed under: this might not work, but we'll learn a ton trying. Poke holes in anything here.*
