# Level 2 — Redirecting the client to our server

**Goal:** make the game's dead config host resolve to a PC running `server/fake_gmc2.py`, so
the client finally sends its request to *us*. The moment it does, `fake_gmc2.py`'s log prints
the **exact URL path** it wants — which is the piece we can't get any other way (the real host
was deleted from DNS: it returns **NXDOMAIN**, so nothing ever leaves the device).

## The target host

```
projects2.gcdn.netmarble.com   <- config file download (prime target)
```

Also worth redirecting once the above works:
```
nmss.gcdn.netmarble.com        (NMSS security, HTTP :80)
apis.netmarble.com  apis.galaxymx.com   (platform APIs, for later)
```

## Before you start

1. On the PC, find your **LAN IP** (`ipconfig` on Windows → e.g. `192.168.1.50`).
2. Run the fake server on **port 80** (the gcdn hosts were seen using HTTP):
   ```
   # Windows: run the terminal as Administrator (port 80 is privileged)
   python fake_gmc2.py --port 80 --gateway http://<PC_LAN_IP>:9000
   ```
3. Make sure the phone/emulator and PC are on the **same network**, and the PC firewall allows
   inbound on port 80.

## Method A — Rooted emulator (recommended, easiest to control)

Using **LDPlayer**, **Android Studio AVD (Google APIs image)**, or any rooted emulator:

1. Enable ADB and connect: `adb devices` should list it.
2. Map the host to your PC in the emulator's hosts file:
   ```
   adb root
   adb remount
   adb shell "echo '<PC_LAN_IP> projects2.gcdn.netmarble.com' >> /system/etc/hosts"
   ```
   (Android Studio AVD: if `remount` fails, boot with `-writable-system`.)
3. Launch the game. Watch the `fake_gmc2.py` console.

## Method B — Rooted physical phone

Same idea, editing `/system/etc/hosts` (via a root file manager or `adb shell` with `su`):
```
<PC_LAN_IP> projects2.gcdn.netmarble.com
```
Then launch the game on the same Wi-Fi as the PC.

## Method C — No root (harder)

Use a custom-DNS / hosts-mapping app that works over Android's VPN slot (e.g. an app that lets
you add a manual A-record `projects2.gcdn.netmarble.com -> <PC_LAN_IP>`). Set it up, then launch
the game. This avoids editing system files but is fiddlier and varies by app.

## What success looks like

When the redirect works, `fake_gmc2.py` prints something like:

```
===== 18:20:01  GET /path/to/whatever/config... =====
  Host: projects2.gcdn.netmarble.com
  ...
```

**That request line is the prize.** Copy it and report it back — it tells us the exact config
path and whether the client accepts our response or asks for something specific.

## Expected walls (be ready)

- **HTTPS instead of HTTP:** if the client requests over `https://` (port 443), it won't trust
  our server without a CA installed, and may pin the cert. If you see the connection reach us on
  :80 → great. If it insists on :443 and fails, that's the next problem to solve (CA install /
  pinning bypass) — tell us and we'll tackle it.
- **NMSS anti-tamper:** `nmss.gcdn.netmarble.com` is Netmarble's security layer. If the game
  detects the redirect/modified environment and bails, note exactly when it dies.

## Report back

- The **request line(s)** from the `fake_gmc2.py` console (path + method + host).
- Whether it came over HTTP (:80) or tried HTTPS (:443).
- What the game showed after (same error? new error? moved forward?).

Even "it still failed but now it hit our server on port X asking for Y" is a big step — that's
the first time the client talks to us instead of Netmarble.
