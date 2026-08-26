# MFR Revival — Dev Blog #2: How login actually worked (and a lucky break on encryption)

*Tracing Marvel Future Revolution's authentication from the Android client. What a private
server would actually have to fake.*

## TL;DR

I dug into the client's Java layer (`classes.dex`) and mapped the whole **login → session →
game** handshake. Two big findings:

1. The Netmarble platform talks **protobuf** over a session connection, and I recovered the
   full message list — so the auth protocol is reconstructable, not a black box.
2. The **gameplay packets look compressed-but-not-encrypted** (UE4's OodleNetwork only, no
   encryption handler compiled in). If that holds up, it removes the single scariest wall in
   any MMO revival: breaking packet crypto.

Nothing here means a server exists yet — but the path just got a lot clearer.

## Quick recap (from Dev Blog #1)

MFR is stock **Unreal Engine 4**, always-online, with an unpacked and symbol-rich client.
Networking splits into a **platform layer** (Netmarble backend, HTTPS/REST) and a **game layer**
(UE4 replication). This post is about how those two connect — the login flow.

## The stack is actually three services

Reversing the `com.netmarble.*` SDK, the client depends on **three** distinct backends, in order:

**1. GMC2 — remote config over HTTP (`GMC2Network`).**
Before anything else, the client hits GMC2 (Netmarble's remote-config / gateway service). It
hands back configuration values, the **gateway URL**, IAP keys (`iapKey` / `iapIv`), review
URLs, and the expected **`worldID` pattern**. Strings like `setGateWayUrlForTest`, `GMC2Url=`,
`setConfigByGmc2Value`, `worldID pattern is missing from server`. This is the first thing to
stub — without it the client doesn't even know where to go.

**2. Session server — protobuf over a TCP session (`TCPSession` / `SessionNetwork`).**
This is where the real login happens. The messages are **protobuf** (`com.netmarble.core.nano.*`
— the "nano" protobuf runtime). Recovered message set:

```
BasePacket / BaseProtocol / ClientProtocol / Response   (framing)
SignInReq / SignInRes                                    (login)
PingReq / PingRes                                        (keepalive)
SessionInfo / SessionProperty                            (session state)
GetSessionPropertyReq/Res
SetSessionPropertyReq/Res
DeleteSessionPropertyReq/Res
CloseSessionNtf                                          (server->client)
StartMaintenanceNtf / EndMaintenanceNtf                  (server->client)
```

The sign-in produces the keys the game needs: **`GameToken`**, **`DeviceKey`**, **`WorldID`**,
`playerID`, `channelID`. Channel login itself (Facebook / Google / guest) is handled by
`com.netmarble.auth.*` and feeds into `SignInReq`.

**3. Game server — UE4 NetDriver.**
With a valid `GameToken` + `WorldID`, the UE4 client connects to the actual game server and
starts talking the ~53 `*_SERVER` services from Dev Blog #1 (ACCOUNT, CHARACTER, ZONE, ...).

So the flow is:

```
GMC2 config (HTTP)  ->  Session sign-in (protobuf/TCP)  ->  GameToken+WorldID  ->  UE4 game server
```

## The encryption finding (the lucky break)

The scariest part of any MMO revival is usually packet encryption. So I checked what the UE4
`PacketHandler` actually loads. The only handler component compiled into the binary by name is
**`OodleHandlerComponent`** (that's UE4's *OodleNetwork compression*, not crypto). There's **no
AES/encryption HandlerComponent, no `SetEncryptionKey`, no `EncryptionAck`** — the strings UE4's
built-in packet encryption would leave behind simply aren't there.

**What that suggests:** the game packets were **Oodle-compressed but not encrypted** at the
PacketHandler layer. Security came from the platform (the `GameToken` you can only get by
signing in) plus TLS on the REST/session side — not from scrambling the gameplay packets.

⚠️ **Caveat:** this needs final confirmation from `DefaultEngine.ini` inside the `.pak` files
(the OBB is a zip of `pakchunk*.pak`), which I haven't unpacked yet. An encryption plugin *can*
be wired up purely via config. But if one were compiled in, its class name would show up — and
it doesn't. So: strong signal, not yet a guarantee.

If it holds, it's huge: any future packet captures would be **decompressible** (Oodle network
state derives from the known UE4 setup), and a re-implementation wouldn't need to crack crypto.

## What a private server would actually have to fake

Concretely, the "point the client at yourself" plan now has a shape:

1. **Fake GMC2** (HTTP): return a config blob pointing the gateway at our own server.
2. **Fake Session server** (protobuf/TCP): answer `SignInReq` with a `SignInRes` that mints a
   `GameToken` + `WorldID`, and handle `Ping` / `SessionProperty`.
3. **Reverse & implement the UE4 game server** (the mountain): accept the NetDriver connection,
   Oodle-decompress, and implement the game services one by one.

Steps 1–2 are ordinary server work (HTTP + protobuf). Step 3 is the multi-month/years grind —
but it's stock UE4 replication, and now we know it's likely not encrypted.

## Honest status

- Reconstructable auth protocol (protobuf message list in hand). ✅
- Strong evidence of no packet encryption (pending pak/ini confirmation). ✅⚠️
- Still an always-online MMO: gameplay logic lived server-side, and there are still **no known
  pre-shutdown packet captures**. That remains the #1 accelerator. 🙏

## Next steps

1. Unpack a `.pak` from the OBB and read `DefaultEngine.ini` → confirm the PacketHandler list.
2. Decompile the `nano` protobuf classes into `.proto` files (reconstruct the exact schema).
3. Stand up a throwaway **fake GMC2** endpoint and see how far the client gets before it wants
   the session server.
4. Keep asking around for **captures**.

*Filed under: cautiously optimistic. Poke holes in the encryption claim especially — I want to
be wrong in the safe direction.*
