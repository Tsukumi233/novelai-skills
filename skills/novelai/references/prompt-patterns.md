# Prompt patterns (distilled from a set of admired reference images, 2026-10)

Source: 10 well-made NovelAI images (read with `nai.py meta`).

- **6 "Plana" images** (V5 Curated, CFG 6, no presets, long custom negative). Recipe: `--style painterly`.
- **4 NovelAI-web images** (V5 at CFG 5.6, V4.5 at CFG 5.5, standard presets). Recipe: `--style graphic`.

The two recipes are opposite looks, painted atmosphere vs flat graphic poster, but they share most of the principles below. Those principles carry over to any style, to char-slot prompts, and to manga panels.

## Principles

1. **Write a director's brief, not a tag pile.** Order the prompt from *what* to *how*:
   - count, franchise
   - identity
   - medium label
   - composition / camera
   - action (with hands)
   - expression
   - setting
   - light
   - palette
   - texture
   - mood
2. **Account for every hand.** Every figure in every reference says what both hands do:
   - "both hands around a teacup"
   - "one hand pressing her windblown scarf against her chest, the other loosely holding the bag strap"
   - "one hand on the step rail"

   Unassigned hands are where V5 invents bad gestures and extra fingers.
3. **Place figures in words and design the empty space.** Name where the figure is, what fills the rest, and what leads the eye:
   - "figure in the lower right, broad near-black ocean filling the left side"
   - "figure placed near the left edge, broad crossing stripes leading into the street on the right"
4. **Palette: three named muted colours plus one restrained accent.** Use concrete pigment-like names, then say how the character's canon colours are muted to fit the palette:
   - "charcoal brown, pearl gray and faded burgundy"
   - "faded cream sky, dark petrol-green shadows and restrained rust-red accents"
   - "restricted pale jade, bone-white and ink-black palette"
   - Muting canon colours: "pink fabric subdued into dusty gray".
5. **Light: source, quality, direction, and where it lands.**
   - "weak moonlight filtered through thick clouds, tiny silver-gray traces on distant wave crests, faint cool highlights on her hair and frilled collar"
   - "narrow cold sidelight"
   - "soft overcast light shaping the faces"
6. **Texture words decide the rendering** more than artist tags do:
   - "dry brush shadows"
   - "subtle oil glazes"
   - "loosely brushed buildings, softened print colors"
   - "coarse film grain throughout, granular black areas, soft dye bleeding, weathered emulsion texture"
7. **End on a mood noun phrase.**
   - "heavy spacious silence"
   - "quiet ritual of release"
   - "understated everyday melancholy"
   - "historical intimacy"
   - "restrained intimidating atmosphere"
8. **Micro-narrative actions make 生活气息.**
   - Freeze a moment inside an ongoing activity: "pausing while arranging the cups", "adjusting the clasp of a worn leather medicine case".
   - Use similes for attitude: "holding up a strawberry like a tiny trophy".
   - Give each person one prop that belongs to the same scene, e.g. strawberry, cookie, teacup, tea tray, sandwich, pastries at one picnic.
9. **Costume changes keep one recognisable anchor.**
   - "long dark hair, small recognizable red hair bow, oatmeal trench coat..." changes Reimu's outfit; the bow keeps her identifiable.
   - `original outfit` means the canon outfit. Add "recognizable" to the item that must survive, e.g. "recognizable red and blue dress and nurse cap".
10. **Guard phrases pre-empt known failures.** Put them in the positive:
    - `clear spacing between faces` (groups merging)
    - `normal anatomy and natural relative scale` (chibi or giant scaling between figures)
    - `normal human face` (on a stern or shadowed face)
    - `clear layered silhouettes` (overlapping figures)
    - `textless` / `no text`
11. **Groups need a geometry that gives every face its own place.**
    - Six girls: "high-angle overhead view, sitting in a loose oval on a picnic blanket, all looking upward toward the camera with different happy expressions". Rendered all six correctly with no slots.
    - Assign places as a word grid: lower / middle / upper × left / right.
12. **Relate people by name**: "standing behind Yuyuko on the left", "seated beside Reimu". This is clearer than coordinates for depth (behind / beside / deeper inside).
13. **Hybrid: tags for attributes, prose for relations** (graphic school).
    - Grouped tag lines fix discrete facts: camera, pose, expression, props, background, lighting.
    - Then one prose paragraph states the spatial layout and the effects: "Character 1 is positioned dynamically on the right half…", "The background is sharply divided into a solid vibrant red lower section and a pitch-black upper void…".
    - Key facts are said twice, once as a tag and once in prose.
14. **Weights for local control**:
    - `-0.8::feet::` suppresses feet in crouching poses (it is part of the V4.5 quality string).
    - `2::splattered colors::`
    - `1.4::close shot::`
    - `1.5::bare feet::`
15. **Lower CFG for long prompts.** Every reference used 5.5–6, below the web default of 7. Long descriptive prompts already constrain enough; 7 tends to overcook.
16. **The generic negative is only a baseline.** The painterly negative contains `film grain`, but a positive asking for "coarse film grain throughout" still got grain. Ask for the texture you want in the positive; don't edit the shared negative per image.

## Skeletons

Fill the `<>` slots. Keep the order.

### P1. Painterly solo / quiet scene (`--style painterly`)

```
1girl, solo, <name>, <franchise>, <original outfit | new outfit>, <hair, eyes, 1 recognizable anchor>,
painterly anime illustration, <portrait|landscape> composition,
<pose with both hands>, <gaze / expression>,
<setting with 2-3 concrete objects>, <figure placement> , <what fills the rest / leading lines>,
<light: source + quality + direction + where it lands>, <how canon colours are muted>,
<palette: 3 named colours + restrained accent>, <texture/medium>, <mood noun phrase>
```

### P2. Painterly ensemble (`--style painterly`, no slots)

```
<N>girls, <franchise>, <scene genre> illustration, <composition>, <group geometry>, clear spacing between faces,
<setting objects>, <light>, <palette>, painterly anime illustration, <texture>, <mood>, textless
| girl, <name>, <hair>, <outfit>, <placement in words or relative to a named girl>, <action with both hands + one prop>, <expression>
| girl, ...
```

### P3. Fine-art homage (`--style painterly`)

```
<N>girls, <franchise>, <names>, style of <painter>, <their genre in a phrase, e.g. "psychologically detailed nineteenth-century portrait and genre painting">,
<Name> <placement>, <hair>, <outfit>, <hands>, <gaze>;
<Name> <placement relative to the first>, ...;
<background>, <light>, <palette>, <technique words: precise facial modeling, restrained gestures, subtle oil glazes>, <mood>
```

### G1. Graphic poster (`--style graphic`)

```
1girl, solo, <name (franchise)>,
<shot>, <angle>, <dynamic angle / dutch angle / foreshortening>,
<pose tags>, <hand tags>,
<expression tags>,
<props>,
<simple|split|two-tone background>, <solid colour fields>, <effects: petals, flames, splatter, slash>,
rim lighting, sharp shadows, high contrast, <spot color | flat color | clean lineart>,
<prose: where the character is in the frame and what they do; how the background is divided; where the light comes from>,
<outfit tags last>
```

## Phrase banks

- **Composition:**
  - `vertical composition, high-angle overhead view`
  - `figure in the lower right`
  - `figure placed near the left edge`
  - `viewed through a cafe window with faint interior reflections`
  - `compressed spatial depth`
  - `approximately half of the rear figure lost in solid black`
  - `spacious empty background`
  - `distant pedestrians reduced to soft silhouettes`
- **Light:**
  - `low sun grazing across the snow from the right, long cold blue shadows`
  - `narrow cold sidelight`
  - `weak moonlight filtered through thick clouds`
  - `soft overcast light shaping the faces`
  - `overcast autumn afternoon`
  - `very restrained luminous accents`
  - `volumetric lighting glowing from <source>`
  - `dynamic rim lighting`
- **Palette:**
  - `warm cream and muted leaf-green atmosphere`
  - `muted slate blue, oatmeal beige and faded crimson`
  - `black moss green, gray yellow and muted blue`
  - `charcoal brown, pearl gray and faded burgundy`
  - `restricted pale jade, bone-white and ink-black palette`
  - `solid red background` + `deep black background` (graphic)
- **Texture:**
  - `soft dry brush texture, gentle film grain`
  - `dry brush shadows`
  - `subtle oil glazes`
  - `loosely brushed buildings`
  - `softened print colors`
  - `visible organic film grain`
  - `soft dye bleeding, weathered emulsion texture`
  - `surreal flat illustration`
  - `clean lineart, flat color, pop art`
- **Weather / motion:**
  - `coat hem and hair pulled sideways by a passing gust`
  - `dense sea fog obscuring the cliff edge and horizon`
  - `dark rock shapes dissolving into mist`
  - `fluttering cape`
  - `falling red petals`
- **Mood:**
  - `restrained everyday tenderness`
  - `understated everyday melancholy`
  - `heavy spacious silence`
  - `quiet ritual of release`
  - `historical intimacy`
  - `joyful family picnic`
  - `restrained intimidating atmosphere`
- **Guards:**
  - `clear spacing between faces`
  - `normal anatomy and natural relative scale`
  - `normal human face`
  - `clear layered silhouettes`
  - `lively natural poses`
  - `textless`

## Choosing

| Want | Use |
|---|---|
| Atmosphere, quiet everyday moments, travel, 1–6 calm figures | P1 / P2, `--style painterly` |
| Character showcase, action, poster, bold colour | G1, `--style graphic` |
| Classical painting look | P3 |
| Slapstick or exact who-does-what-to-whom, NPC extras | Char slots with `source#` / `target#` (prompting.md, Method A). Principles 2–10 still apply inside each slot. |

## Tested tips

Composition and medium
- A "spread across the lower two thirds" layout gives a flat frontal line-up. For depth, give explicit layers (`in the foreground`, `deeper inside`, `behind <Name>`) or a camera (`high-angle view`, `viewed from the doorway`).
- Weak texture words on Curated drift to retro cel anime ("soft gouache texture" did). Use strong medium words: `subtle oil glazes`, `dry brush`, `loosely brushed`.
- Fine-art homage: Curated + `1.4::style of Alphonse Mucha::` gave a real art-nouveau arch and side panels; Full gave a generic moe girl.
- Thin props (spears, beams of light) stay weak; keep them short or occluded.
- Name the concrete shape of fantastic things: "golem made of bridge arches" became an aqueduct, "colossal humanoid stone golem ... glowing eyes, one gigantic arm reaching" read as a monster.
- Atmosphere beats literalness: show a monster only partly (one huge pale eye in fog, a silhouette, `barely distinguishable`), keep the figure close with half the face in shadow, a muted 3-colour palette, `very restrained luminous accents`, `visible organic film grain`.
- Scale failure (a tiny person next to a giant-looking girl): `cowboy shot` + `normal anatomy and natural relative scale` + negative `1boy, multiple people, giant, size difference`.

Game / visual-novel characters
- Their character tag often pulls in the game's flat official CG face, especially under `--style painterly`. Either use V5 Full, CFG 6 with an artist string for the face, or weight the tag down (`0.8::name::`) and add `slender teenage girl, delicate refined facial features, natural head-to-body proportions` + negative `visual novel, game cg, official art, eroge, chibi, child, round face, oversized eyes`.
- A character tag may default to another canon look (alternate hair colour, outfit). State the wanted look and negate the wrong one (`long straight brown hair` + negative `red hair, orange hair`).
- Canon details the tag does not produce (sock trims, a single bow vs two ribbons) must be written out in every slot, every time, or they drift. Write accessories singular and structural ("a single large red ribbon bow tied at the back of her head, the two loops peeking out on both sides") + negative the wrong variant (`two ribbons, two bows`).
- Personality comes from the actions and expressions you write. Check the canon personality before writing; a cool/deadpan character gets `cool unimpressed`, not `heavy blush` (put `heavy blush, flushed face` in the negative).

Clothes
- Never put the garment you want in the negative (a leftover `thighhighs` in the negative made sock length a coin flip). Use the real Danbooru tag (`thighhighs`, not "over the knee socks").
- Hand-driven cloth interaction ("one hand lifting the hem") beats passive cloth descriptions ("skirt flipped up"), which V5 often ignores.
- Sleeves/hems: "flutter sleeves" alone became spaghetti straps; `short flutter sleeves covering the shoulders`, `knee-length`, `bows sewn along the scalloped hem edge` + negative `sleeveless, spaghetti straps, short dress, chain` fixed it.
- Layered sheer dress (2/2 on Curated): describe each layer separately (opaque inner slip ending at mid-thigh, long sheer chiffon outer dress, inner hemline visible through it) and backlight it.

Hands and interactions
- "A standing behind seated B, doing B's hair": `cowboy shot`, "both hands visible at the back of B's head, each hand pinching one end of the ribbon", give B's hands a relaxed pose, negative `extra arms, missing arms, clenched hands, fist`.
- Camera: `holding an old rangefinder film camera at chest height with both hands, right index finger on the shutter button, left hand cupping the lens from below` was clean in 3/3.
- `source#/target#` touching actions can add a stray hand; inpaint it with negative `hand on head, headpat, extra hands`.
- Calm interactions (sparklers, pulling by the hand, tying a ribbon, drying hair with a towel) land reliably; slapstick does not.

Art-photo portraits ("氛围感")
- 5/5 recipe: V5 Full, CFG 6, `uc: light`, artist string, `anime portrait in the style of film photography`, `85mm lens, shallow depth of field, soft bokeh`, `subtle film grain`, one named light setup, negative `realistic, photorealistic, 3d`.
- Strongest setups: shot through a rain-streaked window (raindrops in sharp focus, face soft behind the glass), blue hour with warm rim light, overexposed high-key backlight, firefly long-exposure trails.

Tool gotchas
- A `model` in a file's `defaults` beats a job's `style` preset model; set `model` explicitly in the job when mixing styles.
- Removing clutter by inpainting: include overlapping objects in the mask (they get redrawn cleanly) and put the removed objects in the negative.
