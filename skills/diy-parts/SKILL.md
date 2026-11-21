---
name: diy-parts
description: Use whenever a DIY or electronics project needs to know what parts the user already has, whenever suggesting components, microcontrollers or tools for a build, and whenever the user says what they bought or have for a project, or asks to record, look up or count DIY parts. This is the knowledge base for the user's DIY parts inventory, a Homebox collection kept apart from the home inventory, so read it before suggesting parts to buy or adding a part.
---

# DIY parts inventory

What the user owns for hands-on projects (rn-ax/diy experiments): microcontrollers and dev boards, sensors, LEDs, transistors, resistors, connectors, tools. Before suggesting a part for a build, look here, and prefer what the user already has.

**Related systems**: the `homebox` skill (the API, record fields and attachments, and the separate household inventory); `rn-diy`'s `AGENTS.md` (the experiments these parts serve).

## Separation

The DIY inventory is a second Homebox user with its own collection, "DIY parts", on the same Homebox app as the household inventory. A call reaches the collection of the inventory it names, so every call is `hb-api --inventory diy <method> <path>` (the `homebox` skill describes the wrapper). A part belongs in exactly one inventory: the household inventory excludes bare components, batteries and cables, and the DIY inventory holds them. The two never share tags, locations or items, and no script reads one on behalf of the other.

Credentials: the DIY section of the "Homebox" item in the "Agent" 1Password vault holds the DIY user's login `password` and its `api token`.

## What is recorded

An item in the inventory means the user has the part, so no quantities are kept. A kit is recorded as the individual parts in it, each its own item, because one value can run out while the rest of the kit remains. When a part runs out the item is archived (`archived: true`), which hides it from default searches and keeps its record; a part that is bought again is un-archived. The inventory has no locations and no rooms.

## Categories

Categories are nested tags, and each item carries exactly one leaf tag. Filtering by a top-level tag returns the items under all of its leaves (`GET /entities?tags=<tag id>`).

| Category | Leaf tags |
|---|---|
| Semiconductors | Transistors, Diodes, MOSFETs, Voltage Regulators |
| Passives | Resistors, Electrolytic Capacitors, Ceramic Capacitors, Potentiometers |
| Optoelectronics | LEDs, IR Emitters, IR Receivers |
| Microcontrollers | ESP32 Boards |
| Power | Buck Converters, USB-C Power Delivery, Battery Holders |
| Connectors | DC Jacks and Plugs, Wire Connectors, USB-C Parts, Battery Snaps |
| Switches | Tactile Switches, Limit Switches, Touch Sensors |
| Modules | Level Shifters, Displays, Sensor Kits |
| Motors | Stepper Motors, Servos |
| Lighting | Lamps |
| Household Tools | Soldering, Bench Equipment, 3D Printing, Hand and Power Tools |

A part that fits no leaf gets a new leaf under the closest category, or a new category when none fits. Status tags are `Ordered` and `Needs Info`.

## Recording a part

Follow the `homebox` skill's two-call create (`POST /entities`, then `PUT /entities/{id}` with the full body), with these conventions:

- **Names** state the part and its distinguishing value: `2N2222A transistor`, `Resistor 4.7 kΩ 1/4 W 1%`, `Electrolytic capacitor 100 µF 16 V`.
- **Custom fields** carry specs with their units: `Value`, `Voltage`, `Package`, `Source Kit` (the kit or bag the part came in). Check `GET /entities/fields` before inventing a name. The 500-character field limit applies.
- **An ordered part** is created at once with the `Ordered` tag and an `Expected Delivery` field, and both are removed when it arrives.
- **An unconfirmed fact** (a value read from a photo that may be wrong, a missing detail) is recorded with the `Needs Info` tag and a `Missing Info` field saying what to check.
- **Datasheets** are attached as `attachment`, or linked in a `Datasheet` field when the PDF is large or unstable.

## Household tools

The tools the user uses for DIY work (soldering iron, bench power supply, multimeter, 3D printer, drill, glue gun) are recorded in the household inventory. The DIY inventory holds a link-only stub for each under the `Household Tools` category, named like the household item, with a `Household Item` field linking to it, so a DIY search finds the tool. Specs are read from the household inventory with `hb-api --inventory household GET ...` and never copied into the stub. A new tool that matters for DIY work gets a stub the same way. Writes go to the inventory named in the call and never cross over.

## Suggesting parts

Search the collection with `hb-api --inventory diy GET '/entities?q=<term>'` or by category tag, state what is on hand and what a build still needs, and name the exact part to buy for the gap. Never claim the user lacks a part before searching, and check the household tools before suggesting a tool purchase. A photodiode in the inventory is not a demodulating IR receiver, so a build that decodes remote controls needs a TSOP-type receiver.
