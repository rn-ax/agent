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

## Recording a part

Follow the `homebox` skill's two-call create (`POST /entities`, then `PUT /entities/{id}` with the full body), with these conventions for DIY parts:

- **One item per part type.** Boards and modules are one item each (`ESP32-C3 SuperMini`). Bulk parts are one item per value or type with the count in `quantity` (`Resistor 100 Ω 1/4 W`, `LED 5 mm IR 940 nm`).
- **Specs in custom fields**, with units, named consistently across items (check `GET /entities/fields` first): `Voltage`, `Interface`, `Package`, `Pinout`, `Max Current`, `Datasheet` (markdown link). The 500-character field limit applies.
- **Locations** are where the part is stored (drawer, box), nested as in the household inventory.
- **Tags** stay a small reused set, such as `MCU`, `Sensor`, `IR`, `Passive`, `Tool`, `Low Stock`, and `Ordered` for parts bought and not yet delivered.
- **Datasheets** are attached as `attachment` (pinouts and ratings); a link in `Datasheet` is enough when the PDF is large or unstable.
- **Quantity follows use.** When a project uses parts up, the count is updated in the same session.

## Suggesting parts

Search the collection with `hb-api --inventory diy GET '/entities?q=<term>'` and by tag, state what is on hand and what a build still needs, and name the exact part and quantity to buy for the gap. Never claim the user lacks a part before searching.
