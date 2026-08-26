# Protocol notes (reconstructed from client v2.0.3)

Raw facts pulled from `classes.dex` / `libUE4.so`. Fill in the blanks as the client's real
requests show up in the fake-server logs.

## Backends, in connection order

1. **GMC2** — remote config over HTTP (`com.netmarble.base.GMC2Network`).
   Provides: `gatewayUrl` / `IAPGatewayUrl`, config maps (`gmc2Value` / `gmc2Boolean`),
   `iapKey` / `iapIv`, `review_info_url` / `review_url`, `GMC2_AGREEMENT_URL` /
   `GMC2_TERMS_URL`, UI flags (`useDim`, `strokeColor`, `useTitleBar`), worldID pattern.
   - Exact URL path: **UNKNOWN** (get it from logs). Builders seen: `getGMC2Url`, `setGMC2Url`,
     `getGateWayUrl`.

2. **Session server** — protobuf over a TCP session (`TCPSession` / `SessionNetwork`).
   - Connect URL format (confirmed string): **`%s/sessions?gameCode=%s&tls=true`**
     → `<gatewayUrl>/sessions?gameCode=<code>&tls=true`
   - Protobuf messages (`com.netmarble.core.nano`):
     `BasePacket, BaseProtocol, ClientProtocol, Response,`
     `SignInReq, SignInRes, PingReq, PingRes,`
     `SessionInfo, SessionProperty,`
     `GetSessionPropertyReq/Res, SetSessionPropertyReq/Res, DeleteSessionPropertyReq/Res,`
     `CloseSessionNtf, StartMaintenanceNtf, EndMaintenanceNtf`
   - Sign-in yields: `GameToken`, `DeviceKey`, `WorldID` (≤10 chars), `playerID`, `channelID`.

3. **Game server** — UE4 NetDriver (replication). Uses `GameToken` + `WorldID`.
   - Packet layer: `OodleHandlerComponent` (compression). **No encryption handler found**
     (pending DefaultEngine.ini confirmation).
   - ~53 services: ACCOUNT, CHARACTER, INVENTORY, ITEM, SHOP, MAIL, ZONE, ENTITY, SKILL,
     ARENA, RAID, ALLIANCE, PARTY, CHAT, MISSION, ... (full list in `notes/technical-findings.md`).

## Request params seen (platform)

`gameCode`, `market` (e.g. google), `platform` (ANDROID), `sdkVersion`, `deviceKey`,
`language`, plus the session `tls=true`.

## Known unknowns (fill from logs / logcat)

- [ ] Exact GMC2 URL path + query params
- [ ] GMC2 response envelope shape (is it `errorCode`/`data`? something else?)
- [ ] Which fields are mandatory vs optional
- [ ] SignInReq/SignInRes field numbers & types (decompile the nano protobuf → `.proto`)
- [ ] Session framing (how BasePacket wraps messages on the wire)
