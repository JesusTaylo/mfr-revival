# Technical findings — client v2.0.3

## Build
- Engine: Unreal Engine 4 (custom Netmarble build), uproject codename **"Monster"**
- Analytics SDK: Singular v9.6.0 — build date **2021-01-13**
- Target: `arm64-v8a`; main binary `lib/arm64-v8a/libUE4.so` (~132 MB, **not packed**)
- Netmarble Security present: `libnmsssa.so`, `libnmscrash*`, `*.nmss` (NMSS)

## Networking — Layer 1: Platform (HTTPS/REST via libcurl + OpenSSL)
Baked-in endpoints (all offline now):
- `apis.netmarble.com`, `alpha-apis.netmarble.com`, `dev-apis.netmarble.com`
- `mobileapi.netmarble.com/v2/commonCs/getKey`  (auth key handoff)
- `agreement-rest.netmarble.com`
- `nmbillgw.netmarble.com`  (billing)
- `netmarbleslog.netmarble.com`  (logging)
- `apis.galaxymx.com`, `nmslog.galaxymx.com`  (GalaxyMX game platform)
- `common-api.seed9.com`  (bug tracking)

Auth tokens seen: `GameToken` / `gameToken`, `channelKey`, `getKeySet`.

## Networking — Layer 2: Gameplay (UE4)
- Handlers: `/Script/PacketHandler`, `/Script/OodleHandlerComponent` (OodleNetwork compression)
- No custom encryption HandlerComponent found by name (⚠️ confirm from DefaultEngine.ini in paks)
- Server-authoritative: `MONSTER_SYNC_TO_SERVER`, `SkillMoveServer`, move-checks from server
- Dynamic server discovery: `GenerateServerList`, `OnResponse_ServerList`, gateway/zone system

## Server service map (~53, OpenSSL/TLS noise filtered out)
ACCOUNT, CHARACTER, INVENTORY, ITEM, SHOP, MAIL,
ZONE, ZONE_CREATE, ENTITY, SKILL, MASTERY, SUPERPOWER,
ARENA, FRIENDLY_ARENA, RAID, ALLIANCE_RAID, CITYWAR, CONFLICT,
COOP, BOUNTYHUNT, EPIC_INVASION, IMPACTSTAGE, SQUAD_BATTLE, SQUAD_HQ,
SQUADLEVEL, PARTY, BUDDY, CHAT, ALLIANCE, SIDEKICK,
MISSION, TUTORIAL, TRAINING, TRAINGROUND, ACHIEVE, EVENTACHIEVEMENT,
ATTENDANCE, OMEGACARD, FUTUREPASS, TITLE, WARDROBTHEME, DICTIONARY,
COOLTIME, CONTENTOPEN, ROULETTE_EVENT, SINGLE_REWARD_EVENT, TIME_REWARD_EVENT,
CONTENTS_REWARR_COUNT, GMTOOL (dev)

## Open questions
1. Packet encryption present at PacketHandler layer, or Oodle compression only?
2. Exact UE4 version (to line up with open-source engine source).
3. Login → GameToken → server-list flow details (needs classes.dex decompile).
