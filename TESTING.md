# Testing guide — for testers

Thanks for helping test the MFR revival research! This guide explains **what to test right
now, how to set it up, and what data to send back**. Please read the whole thing once before
starting — especially the "What to expect" and "Legal / safety" sections.

## What to expect (read this first)

We are **not at a playable stage.** So far we have:
- a **fake config server** (`server/fake_gmc2.py`), and
- a reconstructed **login protocol** (`proto/session.proto`).

There is **no running game server yet**, so you will **not** be able to log in or play. The
goal of testing right now is to **observe what the real client asks for** so we can make our
fake servers match. Capturing "the client tried to reach host X with this request" *is* a
successful test.

## Legal / safety

- Use **your own legally obtained copy** of the game. Do **not** upload or share the APK, the
  OBB, or any game files here or anywhere.
- Captures can contain **personal data** (device IDs, tokens, your IP). **Scrub anything
  personal** before sharing a log — replace tokens/IDs with `XXXX`.

## What you need

| Level | Setup | What it proves |
|------|-------|----------------|
| 0 | Just your phone + the APK | The client installs and launches |
| 1 | **Android emulator on a PC** + a capture proxy | What hosts/requests the client makes |
| 2 | Same as L1 + pinning/anti-tamper bypass | We can redirect it to our fake server |

**Important:** a normal (non-rooted) phone can only really do **Level 0**. From Android 7+,
apps don't trust user-installed certificates, so HTTPS interception needs a **rooted device or
an emulator**. For Levels 1–2, please use an emulator on a PC.

Recommended tools:
- **Emulator:** Android Studio AVD (use a *non–Play Store* system image so you can get root/
  writable system), or a rooted emulator like **Genymotion** / **LDPlayer**.
- **Capture:** **HTTP Toolkit** (easiest — one-click ADB interception, and built-in certificate
  + pinning handling for rooted targets) or **mitmproxy** + **Frida** (more manual).

---

## Level 0 — Does it launch? (phone is fine)

1. Install the APK on your device.
2. Open the game and let it sit at the connection/loading screen.
3. **Report:** does it install? does it open? does it crash immediately (possible anti-tamper),
   or does it hang/error trying to connect? A screenshot of the error is perfect.

## Level 1 — Capture what it asks for (emulator on PC)

1. Create/boot an Android emulator on your PC.
2. Install **HTTP Toolkit** on the PC. Start it → choose **Android device via ADB** → it sets
   up interception and the certificate automatically.
3. Install and launch the game inside the emulator.
4. Watch HTTP Toolkit. **Report** the list of hosts/URLs it contacts and the order, e.g.:
   - `GET https://apis.netmarble.com/....` → what path? what query params?
   - `POST https://.../sessions?gameCode=...&tls=true` → did it try this?
5. Save the session (HTTP Toolkit → export). **Scrub tokens/IDs**, then attach it to a GitHub
   issue.

If HTTPS shows up as encrypted/unreadable, note that too — it tells us pinning is active.

## Level 2 — Redirect to the fake GMC2 (advanced)

Only after Level 1 works:

1. On the PC, run the fake server (see `server/README.md`):
   ```
   python fake_gmc2.py --port 8080 --gateway http://<PC_LAN_IP>:9000
   ```
2. In your proxy, **redirect** the Netmarble config host to `http://<PC_LAN_IP>:8080`.
3. Launch the game. Watch **both** the proxy and the `fake_gmc2.py` console (it logs every
   request it receives).
4. **Report:** did the client accept our config? Did it move on to request the session server,
   or did it reject/complain? Copy the `fake_gmc2.py` console output and any in-game error.

Expect walls here: **TLS pinning** (client rejects our cert) and **NMSS** (Netmarble's
anti-tamper, the `libnms*.so` libraries) may block a modified environment. If the client dies
instantly, suspect NMSS. Reporting *how* it fails is still useful data.

---

## How to report

Open a GitHub issue with:

1. **Environment:** device/emulator, Android version, rooted? APK version.
2. **Level attempted** (0/1/2) and **what happened** (1–3 sentences).
3. **Attachments:** scrubbed capture/log, screenshots of any errors.
4. Anything that surprised you.

Use this quick template:

```
Level: 1
Env: Genymotion, Android 9, rooted, APK 2.0.3
Result: Client reached apis.netmarble.com then galaxymx.com, then stalled.
HTTPS was interceptable after installing system CA. Log attached (tokens scrubbed).
Notes: it never tried /sessions — died at config step.
```

Every report, even a failed one, moves this forward. Thank you! 🙏
