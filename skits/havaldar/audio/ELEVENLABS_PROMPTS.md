# हवलदार का भौकाल — ElevenLabs prompts

Generate each item below in ElevenLabs, download the MP3, and **rename it to the exact file name given**.
Send them back (or drop them in `skits/havaldar/audio/vo/`, `audio/sfx/`, `audio/music/`).
The animation, lip-sync and final mix pick them up automatically by file name.

Settings for every voice line: **Text to Speech → model "Eleven v3"** (the expressive one; it understands
the `[tags]`). Make 2–3 takes and keep the funniest. Keep the `[tags]` exactly as written — they control the acting.

---

## 1. Voices

| Character | ElevenLabs voice | Voice ID |
|---|---|---|
| Havaldar Pandey | **Chem – Deep, Expressive & Cinematic** (Hindi/Bhojpuri) | `g66sJwhqbl8rk5CtPVKH` |
| Chhotu | **Pintu – Playful Comedic Character** (Hindi) | `oT6YGCPblY04TqTskA2d` |
| Baba | Design it: **Voices → Voice Design**, paste the description below, language **Hindi**, preview text = Baba's two lines. Save the one you like as "Baba". | — |

**Baba voice description:**
> A thin elderly North Indian village man around 75, amused and teasing, cheeks bulging with paan so his speech is thick, wet and slightly slurred. Slow lazy drawl, dry wit, rustic Awadhi Hindi accent, wheezy chuckle.

---

## 2. Dialogue (11 lines)

Already done ✅: `c1_bhaukal_nikalte.mp3`, `h5_sab_hai_na.mp3` (you can redo them if you want a better take).

| # | File name | Voice | Text to paste |
|---|---|---|---|
| H1 | `h1_naam_pandey.mp3` | Chem | `[deep voice] [dramatically] नाम है पांडे... [pause] हवलदार पांडे। पूरे गाँव मा... भौकाल है हमार!` |
| C1 ✅ | `c1_bhaukal_nikalte.mp3` | Pintu | `[childlike voice] [whispers] [mischievously] भौकाल? अभी निकालते हैं।` |
| H2 | `h2_kaun_hai_be.mp3` | Chem | `[tired] [suspicious] कौन है बे?` |
| H3 | `h3_hawa_hai.mp3` | Chem | `[snorts] हुंह... [smug] हवा है। हवा भी हमसे डरत है।` |
| C2 | `c2_jai_bajrangbali.mp3` | Pintu | `[childlike voice] [whispers] जय बजरंगबली...` |
| H4 | `h4_baap_re.mp3` | Chem | `[shouting] [panicked] अरे बाप रे! बंदूक चल गई! पीछे से चल गई! [crying] हाय दैया, हमार पिछवाड़ा उड़ गवा!` |
| H5 ✅ | `h5_sab_hai_na.mp3` | Chem | `[nervous] [breathless] है... है ना? सब है ना?! [shouting] अरे कोई गिनो रे!` |
| C3 | `c3_bhaukal_fuss.mp3` | Pintu | `[childlike voice] [giggles] हे हे हे! [excited] भौकाल फुस्स!` |
| B1 | `b1_gubbara_phoota.mp3` | Baba | `[slowly] [amused] पिच्च... हवलदार साहब... बंदूक नाहीं चली... गुब्बारा फूटा है।` |
| B2 | `b2_beizzati.mp3` | Baba | `[sarcastic] औ बंदूक पे बैठोगे... तो गोली नाहीं... बेइज़्ज़ती निकलती है। [chuckles] हें हें हें...` |
| H6 | `h6_chhotua.mp3` | Chem | `[angry] [shouting] छोटुआआआ...!!!` |

---

## 3. Sound effects (Sound Effects tool)

Set the duration shown; "Prompt influence" around 0.5.

| File name | Duration | Prompt |
|---|---|---|
| `thunder_crash.mp3` | 2 s | `Dramatic thunder crash with a deep cinematic boom, Bollywood hero entry` |
| `belly_pat_dhab.mp3` | 1.5 s | `A single heavy slap on a big fat belly, cartoon 'DHAB' thump with a short echo` |
| `record_scratch.mp3` | 1 s | `Vinyl record scratch that stops the music abruptly, comedic` |
| `balloon_squeak.mp3` | 1 s | `Rubber balloon squeaking loudly when squeezed, 'kreee'` |
| `crickets.mp3` | 2 s | `Crickets chirping in an awkward comedic silence` |
| `drumroll.mp3` | 3 s | `Snare drum roll building tension, comedic suspense` |
| `dhaam_pop.mp3` | 2 s | `Huge balloon pop combined with a cannon boom, cartoon explosion` |
| `boing.mp3` | 1 s | `Cartoon spring boiiinng as someone shoots up into the air` |
| `dhapp_land.mp3` | 1.5 s | `Heavy fat man falling and landing on his bottom on dusty ground, cartoon thud` |
| `frantic_pat.mp3` | 4 s | `Rapid frantic patting on cotton trousers, thap thap thap thap` |
| `whoosh_away.mp3` | 1 s | `Fast cartoon whoosh of a kid zooming away` |
| `paan_chew.mp3` | 4 s | `Old man chewing betel leaf paan with his mouth full, wet chap chap chewing` |
| `sad_trombone.mp3` | 3 s | `Sad trombone wah wah wah waaah, comedic fail` |

## 4. Music (Music tool, instrumental)

Original music only (no real Bollywood songs, so the Short doesn't get muted or claimed).

| File name | Length | Prompt |
|---|---|---|
| `hero_theme.mp3` | 6 s | `Over-the-top 1990s Bollywood action hero entry fanfare, heavy dhol, blaring trumpet "taaa-daaa", thunder, slow-motion swagger, instrumental` |
| `sneaky_strings.mp3` | 8 s | `Comedic sneaky tiptoe music, plucked pizzicato strings "tin... tin... tin-tin-tin" with a bassoon "bom" on each step, cartoon, instrumental` |
| `sneaky_strings_fast.mp3` | 4 s | `The same comedic sneaky pizzicato and bassoon tiptoe music but faster and more excited, instrumental` |
| `shehnai_lazy.mp3` | 5 s | `A single lazy, slightly off-key shehnai phrase, comedic Indian village feel, instrumental` |
| `hero_kazoo.mp3` | 4 s | `A Bollywood hero entry fanfare melody played badly on a kazoo, silly and deflated, instrumental` |
| `village_ambience.mp3` | 30 s | `Hot quiet afternoon in a North Indian village, distant birds, a faint breeze, far-off cow moo, no music` |

---

## Where each sound plays (for reference)

| Time | Sound |
|---|---|
| 0.0 | hero_theme + thunder_crash, village_ambience (low, whole Short) |
| 0.35 | H1 |
| 4.45 | belly_pat_dhab |
| 5.15 | record_scratch (hero music cuts) |
| 5.7 | C1 |
| 8.2 | sneaky_strings |
| 10.65 | balloon_squeak, music stops dead |
| 10.95 | H2 |
| 11.9 | crickets (1.5 s) |
| 13.5 | H3 |
| 14.6 | sneaky_strings_fast |
| 15.6 | drumroll |
| 16.9 | C2 |
| 18.4 | dhaam_pop, boing |
| 18.75 | H4 |
| 19.5 | dhapp_land |
| 19.9 | frantic_pat |
| 24.1 | H5 |
| 25.0 | C3 + whoosh_away |
| 28.9 | shehnai_lazy, paan_chew |
| 29.1 | B1 |
| 31.7 | B2 |
| 34.5 | sad_trombone |
| 35.0 | H6 |
| 35.6 | hero_kazoo |

Timings get adjusted to the real length of each MP3 when they arrive.
