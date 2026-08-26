# `server/` — Fake backend (Milestone 1)

First step of "point the client at yourself": a **fake GMC2 server** that also **logs every
request the client makes**. Right now it does one job — get the client to talk to *us* instead
of Netmarble's dead servers, and show us exactly what it asks for.

> This is a **data-gathering tool + best-guess responder**, not a working server. The response
> values are reconstructed from the client binary (see `notes-protocol.md`) and *will* need
> tuning once we see the real client's requests in the logs. That iteration is the whole point.

## Run it

Needs only Python 3 (no dependencies):

```bash
python fake_gmc2.py --port 8080 --gateway http://<TU_IP_LOCAL>:9000
```

- `--gateway` is the address we tell the client to use for the session server (your PC's LAN
  IP + the port where the session server will eventually live). Find your IP with `ipconfig`
  (Windows) / `ip addr` (Linux).
- The server replies to **any** path with the GMC2 config and prints every request.

## Point the client at it

The client wants to reach hosts like `apis.netmarble.com` / `apis.galaxymx.com`. You need to
redirect those to your PC. Options, easiest first:

1. **Proxy (recommended for discovery):** run an intercepting proxy (mitmproxy / Fiddler /
   Charles) on your PC, set it as the device/emulator's HTTP proxy, and forward the Netmarble
   hosts to `127.0.0.1:8080`. A proxy also **shows you the requests even before our responses
   are right** — great for filling in `notes-protocol.md`.
2. **Hosts / DNS override:** point the Netmarble domains at your PC's IP (Android needs root or
   an emulator for `/system/etc/hosts`, or use a local DNS like `dnsmasq`/AdGuard).

### ⚠️ Two walls to expect

- **TLS pinning / HTTPS:** the client talks HTTPS and may reject our certificate. You'll likely
  need a user/system CA (proxy CA) installed, and possibly to defeat certificate pinning
  (Frida / patched build). If requests never reach us over HTTPS, this is why.
- **NMSS (Netmarble Security):** the `libnms*.so` anti-tamper layer may detect a modified
  environment. If the client bails early, suspect this.

## What to look for in the logs

When the client hits us, the console prints method + path + headers + body for each request.
Copy those into `notes-protocol.md`. We especially want:

- The **exact GMC2 path** and query params the client uses (so we stop guessing the URL).
- The **response fields the client complains about missing** (watch its own logcat too).
- Whether/when it moves on to `<gateway>/sessions?gameCode=...&tls=true` (the session server).

## Milestone 1 — definition of done

✅ = the client boots, sends its config request to **our** server, accepts the response, and
proceeds to request the **session/login** server. That's the checkpoint. No gameplay yet — it
proves we're inside the client's flow and gives us the real request shapes to build the next
piece (the protobuf session server).

## Roadmap from here

1. **GMC2 (this)** — config gate. ← we are here
2. **Session server** — protobuf over `/sessions` (SignIn / Ping / SessionProperty).
3. **Game server** — UE4 NetDriver + the ~53 services. The mountain.
