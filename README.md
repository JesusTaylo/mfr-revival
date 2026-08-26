# MFR Revival — Marvel Future Revolution server research

An open, honest attempt to study whether **Marvel Future Revolution** (Netmarble, shut down
2023) could ever run again via a fan-made private server. This repo holds the **research,
dev blogs, and any code** produced along the way.

> **Status:** early research. No playable server exists. This may never fully work — but the
> process is documented so the next person has a head start.

## What we know so far

The game is built on **stock Unreal Engine 4** networking, and the Android client binary is
unpacked and symbol-rich — which makes reverse engineering far more tractable than a fully
custom MMO. Networking splits into two layers:

1. **Platform (HTTPS/REST):** login, account, billing, and the *server list* — Netmarble /
   GalaxyMX backends (now dead). Plain REST, so it can be stubbed locally.
2. **Gameplay (UE4 NetDriver + PacketHandler + OodleNetwork):** UE4's own replication protocol.
   Stock engine = big head start; we reverse Netmarble's game-specific classes on top.

Full write-up: see [`devlog/`](devlog/) and [`notes/technical-findings.md`](notes/technical-findings.md).

## Roadmap (milestones, not promises)

- [ ] Confirm packet-layer crypto (encryption handler vs. just Oodle compression)
- [ ] Trace the login → `GameToken` → server-list flow (from `classes.dex`)
- [ ] Stand up a **fake platform server** and get the client past login
- [ ] Reverse the UE4 game protocol per service (ACCOUNT, CHARACTER, ZONE, ...)
- [ ] Find pre-shutdown **packet captures** (the #1 accelerator — help wanted!)

## Legal

Reverse engineering for interoperability / preservation. **No copyrighted game files** (APK,
`.so`, assets, paks) are hosted here — only original research, notes, and code. Bring your own
legally obtained client.

## Follow / contribute

Dev blogs are posted in [`devlog/`](devlog/). Corrections, ideas, and especially **packet
captures** are very welcome — open an issue.
