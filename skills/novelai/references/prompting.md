# Prompting NovelAI V5 (tested 2026-10)

Generic prompt design, skeletons and phrase banks are in `prompt-patterns.md`. This file holds the tested specifics.

## Style: artists, years, model

- Artist tags: `artist:name`, weighted `1.2::artist:name::`. Strings that worked:
  - Cute / clean modern: `artist:hiten (hitenkei), artist:mignon, artist:kedama milk, year 2024, year 2025`
  - Polished splash art: `1.2::artist:ke-ta::, artist:ask (askzy), artist:ciloranko, 0.8::artist:rella::, year 2024`
- Year tags steer the era: `year 2008` thick lines and saturated colour, `year 2013` soft pink moe, `year 2018` clean gacha portrait, `year 2024/2025` transparent modern colouring. Stacking 2024+2025+2026 just reinforces "modern"; 2026 has little data.
- No artist tags at all also works on V5 if the prompt describes rendering, light and palette in prose (see long-form below).
- **Curated vs Full**: same prompt and seed give a much stronger painterly / oil-paint look on V5 Curated; Full is flatter and more "anime screenshot". Try Curated for atmospheric scenes.
- Negative-artist trick (from admired reference images): put generic-AI-look artists and traits in the negative to push away from the default style: `artist:xinzoruo, artist:milkpanda, artist:kurukurumagical, artist collaboration, one-hour drawing challenge, toon (style), 1990s (style), shiny hair, shiny skin, shiny clothes, thick lips, mob face`.
- Weights: `1.5::tag::` boosts; negative weights work inside the positive prompt, e.g. `-0.8::feet::`.

## Multi-character scenes

2–6 characters interacting in everyday scenes (e.g. Touhou characters living in real cities) are a good test of V5's comprehension. Two methods, both proven:

### A. Per-character slots (robust; best for comedic / action interactions)

- Base `prompt`: artists, count tags (`3girls`, `2girls, 1boy, 1other`), setting, lighting, mood only.
- `chars`: one entry per person: `name, 2–3 identity anchors (hair, signature item), outfit, ONE main action, expression`.
- Interactions: `source#<action>` on the doer, `target#<action>` on the receiver, `mutual#<action>` for both (e.g. `source#pulling by the hand` / `target#pulling by the hand`, `#pointing at another`, `#fanning`, `#giving`).
- **Every extra that matters gets its own slot** (maid handing flyers, vendor, tourists). Otherwise V5 merges the extra's role and outfit into a main character (Suwako became the flyer maid and lost her frog hat).
- Per-character `negative` blocks leakage (`maid, apron` on Suwako; `boat, sitting` on someone who must stand on a bridge).
- Positions: x/y in 0–1. Spread positions spread people out; for a tight huddle keep positions within 0.3–0.7 or omit them.
- Without slots V5 failed by: dropping a character, duplicating one (two Eikis), or swapping roles. With slots all of these were fixed.

### B. Long-form captions in the base prompt (best atmosphere; quiet scenes)

Used by the admired reference images (client "Plana", V5 Curated, 28 steps, CFG 6, quality none, no slots). One English paragraph of art direction, then one `| girl, ...` line per character:

```
3girls, touhou, quiet winter travel illustration, landscape composition, painterly anime illustration,
original outfits, textless, <setting>, <light: "low sun grazing across the snow from the right, long cold blue shadows">,
<layout: "figures grouped in the left half with the empty tracks leading into the right half">,
<palette: "muted slate blue, oatmeal beige and faded crimson">, <texture: "soft dry brush texture, gentle film grain">, <mood: "restrained everyday tenderness">
| girl, hakurei reimu, <hair/outfit>, seated at the left end of a snow-dusted bench, both hands around a paper cup of steaming tea, sleepy
| girl, alice margatroid, <...>, seated beside Reimu, unfolding a paper train timetable
| girl, kirisame marisa, <...>, standing on the right, shading her eyes while looking down the tracks
```

- Placement in words ("lower left", "standing behind Yuyuko on the left").
- Concrete palette words (charcoal brown, pearl gray, faded burgundy), named light, a mood phrase.
- Painter references in prose work: "style of Ivan Kramskoy, nineteenth-century portrait".
- Calm interactions (posing for a photo, waiting, serving tea) render almost perfectly; slapstick does not.

## V5 limits and fixes

| Problem | Fix |
|---|---|
| Character missing / duplicated / roles swapped | Method A slots, extras in own slots, per-char negatives |
| Non-Japanese place drawn as a Japanese festival | Name local architecture, food, objects (e.g. Kashgar: yellow mud-brick, pointed arches, mosque dome, naan, pomegranates) + negative `paper lantern, japanese festival, yukata, torii` |
| Multi-step actions ("stealing", "slamming a winning hand") | One visible pose per character; expect "sneaky" rather than "grabbing" |
| Background crowd counts ("two grandpas" → one) | Don't rely on exact NPC counts; give important NPCs a slot |
| Obscure regional food (mango sticky rice → shaved ice) | Describe what it looks like |
| Long thin props break (Gungnir spear) | Avoid, or keep them short / partly occluded; inpaint |
| Garbled signage | Normal; crop, cover, or ignore |

## Quality / negative defaults

Quality `standard` appends `very aesthetic, masterpiece, no text`; UC `heavy` prepends the V5 heavy preset. Add scene-specific negatives on top (`bad hands, extra fingers, fused fingers`, culture leaks, `oversaturated` for muted looks). Never `nsfw`.
