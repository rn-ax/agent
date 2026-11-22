---
name: standard-diagram
description: Use whenever the user wants a diagram drawn from text, above all a breadboard wiring diagram for a DIY circuit, and also a circuit schematic, flowchart, genogram, timeline, state or sequence diagram, org chart, floor plan or any other standard diagram type. The diagram is written as a Schematex DSL file that stays in the project, and `render-diagram` turns it into an SVG and a standalone HTML page in /tmp for the user to open. This skill holds the Schematex DSL conventions, the breadboard grammar and its gaps, and the workflow, so read it before writing a diagram.
---

# Standard diagrams with Schematex

[Schematex](https://schematex.js.org) turns a short text DSL into an SVG for 52 standard diagram types (breadboard, circuit schematic, flowchart, genogram, timing, state, sequence, org chart, floor plan and more). The first keyword of the file picks the type, and each type's grammar is on `https://schematex.js.org/docs/<type>`. A diagram is the DSL file, which belongs in the project it illustrates (an experiment's `docs/`, for example) and is versioned there. The rendered files are rebuilt from it on demand and are not committed.

## Rendering

`render-diagram <dsl-file> [--out-dir DIR] [--png]` (this skill's directory) parses the file and writes `<name>.svg` and `<name>.html` into a new directory under `/tmp/standard-diagram/`, or into `--out-dir`. Its JSON context carries `url`, a `file://` link to the page, and `diagnostics`, the parser's line-numbered messages; exit 1 means the DSL is invalid and nothing is written. The first run installs the pinned `schematex` package into `~/.cache/rn-agent/schematex/<version>` with install scripts disabled, and needs `node` and `npm`. `--png` adds a PNG for looking at the drawing (needs `inkscape`).

Workflow:
1. Write or edit the DSL file in the project.
2. Run `render-diagram <file> --png`, open the PNG with the Read tool and fix overlaps, collisions and wrong holes in the DSL. Render again after each change.
3. Give the user the page as a markdown link built from the context's `url`.
4. For a build the user will follow, write a short markdown note beside the DSL (build order, what each part does, which hole each leg goes in, and a table of which holes share a strip), because Schematex draws the parts but states none of this.

The page can also be published as an Artifact: it starts with `<title>` and has no `<html>` or `<body>` tags.

Schematex is AGPL-3.0. The skill installs it as a tool and does not copy it into any repository.

## Breadboard diagrams

Header, then optional `board:` and `title:` lines, a `parts` block and a `wires` block. Comments start with `//`. Every part is `id: kind [args] @placement` and every wire is `<endpoint> --color-- <endpoint>`.

**Coordinates.** `@<col><row>` is a hole: columns count from 1 (30 on a half board, running left to right), rows are `a`-`e` (top half) and `f`-`j` (bottom half). The five holes of one column and half are connected, so `@5a`-`@5e` share a strip, and the centre gap separates the halves. `@+t<col>` and `@-t<col>` are the top plus and minus rails, `@+b<col>` and `@-b<col>` the bottom ones. `@<a>..<b>` is a span from one hole to another, and `@beside-left`, `@beside-right`, `@above` and `@below` place a microcontroller off the board. `board: half` (default, 30 columns, continuous rails), `board: full` (63 columns, rails break at the middle) and `board: mini` (17 columns, no rails).

**Parts.**

| Kind | Form |
|---|---|
| `resistor` | `r1: resistor 220 @5e..9e` (ohms, `k` and `M` allowed, colour bands drawn automatically) |
| `led` | `d1: led red @10e..10f` (red, green, blue, yellow, white, orange) |
| `cap-elec`, `cap-ceramic`, `diode`, `button` | `c1: cap-elec @4e..4f` |
| `potentiometer` (`pot`) | placed like the others |
| `dip`, `header` | `ic: dip pins=8 @4e`, `h1: header pins=4 @20a` |
| `mcu` | `uno: mcu uno @beside-left`; subtypes `uno`, `nano`, `esp32`, `esp32-c3`, `esp32-s3`, `pico` |
| `sensor` | `hcsr04`, `dht11`, `dht22`, `vl53l0x` |
| `display` | `oled-ssd1306` (`oled`), `lcd-1602-i2c`, `tm1637` |
| `module` | `rotary-ky040`, `l298n`, `relay-1ch`, `rtc-ds3231` |
| `actuator` | `servo-sg90` |

Wire endpoints are `<partId>:<pin>` (for example `esp:GND`, `esp:GPIO21`, `uno:5V`) or a coordinate. The `esp32` drawing labels its 5 V pin `VIN`. A wire may add `via @<hole>` to bend its arc.

**Idioms.** Take power from the rails: a wire from the board's supply pin to a `@+t` hole and one from GND to a `@-b` or `@-t` hole, then short jumpers from a rail hole to the strip that needs it. An LED that crosses the centre gap (`@10e..10f`) is the standard look; an LED or resistor spanning columns along one row works but needs room, so leave a few columns between parts. Parts placed in adjacent columns overlap their labels and bodies.

**Gaps.** There is no transistor, no infrared LED and no way to define a part, so a transistor is a 3-pin `header` (its id is the label) and an IR LED is drawn as a white `led`; the note beside the DSL says so. The drawing does not show which LED leg is the anode, and neither the docs nor the parser say which end of a span it is, so the note states polarity. Schematex checks syntax and coordinates only: it does not detect shorts, floating pins or wrong values, so the strip table in the note is derived by reading the DSL.
