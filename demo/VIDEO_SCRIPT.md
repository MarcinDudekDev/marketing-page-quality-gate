# 90-Second Demo Video — Script & Shot List

**Format:** screen recording (Loom-style). Two assets to screen-capture:
`demo/demo.html` (the 52s asciinema, autoplay) and `report/scorecard.html`.
**Voiceover:** record over the visuals — Marcin to narrate (headless build can't voice it).
Target run time **~90s**. Read at a calm, confident pace.

---

### 0:00–0:12 — The problem  (visual: title card / demo.html opening frame)
> "Our media-buying team ships fifty AI-generated landing pages a week. Here's the question
> nobody can answer fast enough: which of them is quietly leaking ad spend? A missing pixel,
> a buried CTA, a dead link in the hero — you don't see it, but you pay for it on every click."

### 0:12–0:30 — Grade a leaky page  (visual: demo.html — `score leaky_funnel` → F)
> "So we built a gate. Hand it any page — a URL, or the raw HTML before it's even deployed — and
> it scores deterministically. Same page, same grade, every time. This one's an F: no viewport,
> no tracking pixel, no call to action, dead links. Eighty-four percent of ad spend at risk."

### 0:30–0:42 — What good looks like  (visual: `score perfect` → A, 0% risk)
> "A clean page scores an A — responsive, tracked, one clear CTA, fast, every link alive. Zero
> spend at risk. The difference between these two pages is real money."

### 0:42–1:02 — The actual job: gate the spend  (visual: `gate gate_spend` → BLOCK)
> "But a grade is just a number. This is the job: feed it a real Ads Manager CSV export, and it
> blocks spend on anything below a C. Here it stops a twelve-thousand-dollar-a-month campaign from
> pointing at a broken funnel — ten thousand dollars that would've burned. A missing pixel is the
> biggest leak of all: no pixel means no measurement, no retargeting — the whole budget runs blind."

### 1:02–1:18 — Real pages, real grades  (visual: report/scorecard.html)
> "And it's not a toy. We graded seven real DTC landing pages as they ship today — Dr. Squatch,
> HelloFresh, Bombas, Ruggable. Not one scored an A. Even the big brands ship leaky funnels. This
> is exactly the page type our buyers run — and exactly what the gate catches before launch."

### 1:18–1:30 — Close  (visual: demo.html — 8-tool list, then `pytest 54/54`)
> "Eight tools, callable by any AI agent in plain language, all gated by a deterministic oracle —
> fifty-four tests, green. Claude wrote the oracle; Grok built to pass it. AI velocity never ships
> a leaky funnel."

---

**On-screen captions to add (optional):** the F badge, the `$10,711 at risk`, the `BLOCK` verdict,
and `54/54 passed` — these are the four moments that sell it.
