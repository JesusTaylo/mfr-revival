# MFR Revival — Dev Blog #3: The login protocol, reconstructed

*I decompiled the client's protobuf classes and rebuilt the exact session/login protocol.
It compiles. This is the first piece we can implement 1:1 instead of guessing.*

## TL;DR

Using jadx I decompiled the Netmarble session classes and read the protobuf **field numbers
and types straight out of the bytecode** — so this isn't a guess, it's the real schema. The
result is a `session.proto` (in the repo under `proto/`) that **compiles cleanly with protoc**
and defines the entire login/session protocol: sign-in, keepalive, session properties, and
maintenance/disconnect notifications.

Translation: the second backend a private server has to fake (the session server) now has an
exact spec.

## How I got it

The client uses **protobuf-nano** (`com.netmarble.core.nano.*`). Decompiled, each message's
`writeTo` / `mergeFrom` methods literally spell out the wire tags — e.g. `bVar.M0(2, gameToken)`
means *field 2, string*. I read all 19 classes and transcribed them into a clean `.proto`,
then validated it (`protoc` accepts it with zero errors).

## The protocol

**Transport.** The client connects to `<gatewayUrl>/sessions?gameCode=<code>&tls=true` (the
`gatewayUrl` comes from GMC2 — see Dev Blog #2) over a persistent TCP/WebSocket session. *(Exact
framing on the wire still to be confirmed from live logs.)*

**Envelope.** Every frame is a `BasePacket`:

```proto
message BasePacket {
  string service_code = 1;
  int32  msg_type     = 2;   // which message this is
  int64  sequence     = 3;   // pairs request <-> response
  bytes  payload      = 4;   // the inner message (e.g. SignInReq), serialized
  repeated SessionInfo session = 5;
  int32  multicast_type = 6;
  int32  version        = 7;
  repeated SessionProperty session_properties = 8;
  int64  debug          = 99;
}
```

`msg_type` routes everything, and I recovered the full table:

```
SIGN_IN_REQ=100  SIGN_IN_RES=101
PING_REQ=200     PING_RES=201
CLOSE_SESSION_NTF=302
START_MAINTENANCE_NTF=310  END_MAINTENANCE_NTF=311
SET_PROPERTY_REQ=400  ...  GET_PROPERTY_REQ=600 ...
```

**The sign-in itself is tiny:**

```proto
message SignInReq { SessionInfo session = 1; string game_token = 2; }
message SignInRes { int32 error_code = 1; string error_message = 2; SessionInfo session = 3; }
```

So a client signs in by sending its `SessionInfo` (gameCode, pid, cid, **wid**, deviceKey, ...)
plus the **`game_token`** it got from the platform. The server replies `error_code = 0`
(SUCCESS) and echoes back a populated `SessionInfo`. I even have the error table — `INVALID_SESSION=2003`, `VERIFY_FAIL=3000`, `ALREADY_SIGNED_IN=3001`, etc.

**SessionInfo** is the identity blob passed around everywhere:

```proto
message SessionInfo {
  string game_code=1; string pid=2; string cid=3; string wid=4; string sid=5;
  string server_addr=6; string client_addr=7;
  map<string,string> extra_data=8;
  repeated SessionProperty session_properties=9;
  string device_key=10;
}
```

There's also a **`SessionProperty`** key/value system (string/int/long/bool) with get/set/delete
messages, and server→client notifications for **maintenance** windows and forced disconnects
(with causes like `MAINTENANCE`, `WORLD_ID_MISMATCH`, `TRIGGER_RECONNECT`).

## Why this matters

A fake session server can now be built to spec: accept the connection, parse `BasePacket`, and
for `msg_type=100` reply with a `SignInRes{ error_code: 0, session: {...} }`. No reverse
engineering of *this* layer left — just implementation. The scary unknowns are now downstream
(the UE4 game server), not here.

## Honest status

- Session/login protocol: **reconstructed and validated** (`proto/session.proto`). ✅
- GMC2 config gate: fake server built (Dev Blog #2), pending a live client test. 🟡
- UE4 game server: still the mountain, still server-authoritative. ⛰️
- Still no pre-shutdown **packet captures** — and now that we can *speak* the session protocol,
  a capture of even one real sign-in would let us verify our `SessionInfo` fields instantly. 🙏

## Next steps

1. Build a **session server** that speaks `session.proto` (SignIn + Ping to start).
2. Confirm the transport framing (TCP vs WebSocket) from a live client log.
3. Move on to the UE4 game-server handshake once the client gets past sign-in.

*The login door now has a key we cut ourselves. Whether the next door opens is another post.*
