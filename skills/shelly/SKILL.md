---
name: shelly
description: Use whenever a task involves Shelly devices in the user's home — the Shelly 2PM Gen4 relay, any other Shelly (Gen3/Gen4 relays, plugs, sensors), pairing one to Zigbee or Wi-Fi, switching its profile or firmware, its wall-switch inputs, its Home Assistant entities, or anything about "shelly" explicitly. This is the accumulating knowledge base for how this user's Shelly devices are set up and what was learned getting them working, so read it before pairing, resetting or reconfiguring one, and add to it whenever something new is learned.
---

# Shelly

Everything learned about the user's Shelly devices, kept so the next device or the next reset starts from what already works. Fill in each section as it is confirmed on a real device; per-device facts go in the device sections at the end, general behaviour in the sections before them.

**Related systems**: `home-assistant` (ZHA is where the Zigbee devices live; its `SKILL.md` has the ZHA diagnostics calls), `homebox` (each device's specs, serial, firmware and photos), `home-network` (the IoT Wi-Fi network and how to find a device in SRM), `home` (topology).

## How the Gen4 devices behave

- **One radio, several protocols.** Gen4 devices speak Wi-Fi, Bluetooth, Zigbee and Matter from a single multiprotocol chip. Matter is the factory default; Zigbee is a separate firmware build (its `app` ends in `ZB`, for example `S2PMG4ZB`) that the device switches to. Matter and Zigbee are exclusive; Wi-Fi can stay configured next to Zigbee. Bluetooth is turned off to reduce contention on the shared radio.
- **Control button.** On the 2PM Gen4 it is a round recess on the back, bottom right. Hold 5 s turns on the access point and Bluetooth (web page at `192.168.33.1`); hold 10 s is a factory reset; 5 presses switch the Matter and Zigbee firmware; 3 presses start Zigbee inclusion. The LED has no distinct Zigbee pattern, so its state shows in the web page, in ZHA or in the device status.
- **Factory reset returns the Matter default and the `cover` profile.** A relay that switches lights needs the `switch` profile (`/rpc/Shelly.SetProfile?name="switch"`; the device restarts). The profile decides the Zigbee entities.
- **Enabling Zigbee in the web page turns the device's access point off.** The page stays reachable over Wi-Fi at the address SRM assigned, as long as Wi-Fi is configured.
- **The Zigbee page status "joined" means the device holds a network** and never searches for a new one. Clear config resets it; then Start pairing joins with ZHA's join window open.
- **Firmware: update before pairing.** Updates over Wi-Fi (`available_updates` in the status, or the web page). Version 1.7.99 joined ZHA but its configure step failed with radio errors; 2.0.1 configured in about 30 seconds and added a Zigbee OTA cluster, so ZHA offers an update entity. The Zigbee address changed between those versions.
- **Device password.** Once one is set, only `Shelly.GetDeviceInfo` answers without credentials (digest authentication for the rest); scripted reads of settings need the password from the password manager.
- **"Enable Advanced Security"** (stricter certificate checks, HTTPS) cannot be undone without a factory reset and depends on a correct device clock; it stays off until there is a reason.
- **Debug logs over UDP.** The device can send its log to an `address:port` (Sys config `debug.udp.addr`). A short-lived `python3` UDP listener on the Home Assistant Pi captures it when the device is on the IoT Wi-Fi network. Clear the destination afterwards.

## Pairing a relay to ZHA

1. Factory reset (hold 10 s) and wait for the steady blink.
2. Connect to its access point, open `192.168.33.1`, set the `switch` profile if it controls loads.
3. Join Wi-Fi (the IoT network) and update the firmware to the latest stable.
4. In the Zigbee page: enable Zigbee, Clear config, then Start pairing while ZHA's join window is open (`zha/devices/permit`, up to about 250 s; an open window with the device inside, not far from a router, joins in seconds).
5. Watch the configure step in the core log; a healthy join shows `Bound cluster …: Status.SUCCESS` for every cluster and `zha_device_configured`.
6. Remove a stale ZHA entry under an old Zigbee address from the ZHA device page; the generic device-registry removal call is refused for ZHA.

## Entities in Home Assistant (switch profile)

Per channel: a switch plus power, apparent power, current, voltage, frequency, power factor and energy delivered and received (On/Off, Metering and ElectricalMeasurement clusters on endpoints 1 and 2). The device also exposes an identify button, a Zigbee OTA update entity and, from a window-covering endpoint, an "opening" binary sensor that is unused in switch profile. Naming follows the load: switches `switch.<area>_<load>`, sensors `sensor.<area>_<load>_<thing>` with Swedish suffixes (`effekt`, `skenbar_effekt`, `strom`, `spanning`, `frekvens`, `effektfaktor`, `energi`, `energi_mottagen`); the device-level entities keep the device prefix. Channel 2 voltage and frequency duplicate channel 1.

## Wall-switch inputs

- **Detached.** Per channel, output type Detached (and input mode Switch for a rocker, Button for a push-button) makes the wall switch report events without moving the relay. Auto ON on a channel that must stay powered turns its relay back on after a short delay, and the power-on action fixes its state after a power cut.
- **What a flip sends.** Each input is a Zigbee endpoint (3 for input 0, 4 for input 1) whose OnOff output cluster emits `on`/`off` plus an `attribute_updated` for `on_off` carrying the rocker's position. Scene recalls and endpoint 5 window-covering commands arrive alongside and carry nothing extra. They reach HA as `zha_event` events (`device_ieee`, `endpoint_id`, `cluster_id`, `command`, `args`).
- **No ZHA entity exists for the inputs.** A trigger-based template binary sensor per rocker on `zha_event` (endpoint, cluster 6, command `attribute_updated`, state from `args.attribute_value`) gives each rocker an entity. It reads unknown until its rocker has been flipped once.
- A push-button input would send presses without a stored position; options for that were discussed but not built.

## Devices

### Shelly 2PM Gen4 — office wall box (`Kontor · Väggbrytare`)

Homebox record `000-243` holds the specs, serial, firmware and photos. Wired in the office wall box; paired through ZHA.

- **Loads.** Channel 1 (`switch.kontor_takflakt`) is the ceiling fan, which has its own remote and must never be off; channel 2 (`switch.kontor_fonsterlampa`) is the window lamp.
- **Device settings.** Fan output: Detached, power-on = on, Auto ON 10 s, Auto OFF disabled. Lamp output: Detached, power-on = restore, no timers. Input mode Switch on both. Bluetooth off, Wi-Fi on the IoT network, Advanced Security off, firmware 2.0.1.
- **Rockers.** Left rocker is input 0, endpoint 3 (the fan's input), right rocker is input 1, endpoint 4 (the lamp's input). `binary_sensor.kontor_vaggbrytare_vanster` and `_hoger` in `templates.yaml` follow them. No automation uses them yet; the left rocker and the lamp are deliberately left alone for now.
- **Zigbee address** `d8:85:ac:ff:fe:f5:93:29` on firmware 2.0.1 (it was `…:28` on 1.7.99).

## Open items

- Decide what the rockers do, and build the automations on the two rocker entities.
- Check after the next Home Assistant restart that the rocker entities keep their last position instead of reading unknown.
- Decide whether the unused "opening" sensor and the duplicate voltage and frequency sensors of channel 2 are disabled.
