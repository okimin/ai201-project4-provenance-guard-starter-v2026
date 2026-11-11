# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. **Client → `POST /submit`**: the body is JSON with `text` and `creator_id`.
2. **Validation in `app.py`**: empty, missing or oversized text is rejected with a 400. Valid text continues.
3. **`detector.model_signal`**: GPT-2 measures perplexity, which becomes `model_score` (0–1, higher means more AI-like).
4. **`stylometry.style_signal`**: measures sentence-length spread, type-token ratio and punctuation density, which become `style_score` (0–1, same direction).
5. **`scoring.combine_signals`**: a weighted average of the two scores gives one `confidence` number.
6. **`scoring.score_to_label`**: turns that score into a guess and a label written for the reader (human, unsure or AI).
7. **`audit.log_decision`**: assigns a `content_id` and logs both signal scores, the combined score, the label and the status. The response goes back to the reader. If they dispute it, `/appeal` with that `content_id` moves the item to `under_review`.

### Tracing a false positive

- **Who:** a student writing in their second language submits an essay they wrote themselves. They use short, safe sentences and familiar words.
- **Score:** low perplexity (about 22) gives a `model_score` of about 0.76. Even sentences and repeated vocabulary give a `style_score` of about 0.60. Combined, that's about **0.68**.
- **What they're told:** under the default 0.65 cutoff, **"high-confidence AI."** Both signals fail in the same direction for this writer, so averaging them doesn't help.
- **What they can do:** `POST /appeal` with their `content_id` and their reasoning. The item moves to `under_review` for a human to check. Nothing is re-scored automatically.
- **What this means for the thresholds:**
  - The AI cutoff has to sit above where plain human writing lands, probably around 0.75–0.80. I'll confirm the exact number with the calibration inputs in Milestone 4.
  - The "unsure" band should be wide.
  - The AI label should say "patterns common in AI text," not "you used AI."
  - Every response should show the `content_id` and explain how to appeal.

### Endpoint contracts

**`POST /submit`**

- **In:** `text` (string, required, non-empty, with a size limit) and `creator_id` (string, optional, defaults to `"unknown"`).
- **Out (200):**
  - `content_id`: string
  - `guess`: `"human"`, `"unsure"` or `"ai"`
  - `confidence`: float 0–1, the combined score
  - `label`: string, the exact text the reader sees
  - `model_score`: float 0–1
  - `style_score`: float 0–1
- **Errors:** 400 `{error, message}` for bad input, and 429 when the rate limit is hit.

**`POST /appeal`**

- **In:** `content_id` (string, required, must already exist in the log) and `reasoning` (string, required, non-empty).
- **Out (200):** `content_id`, `status: "under_review"`, and `message`, a plain-language confirmation.
- **Errors:** 400 for a missing field, and 404 for an unknown `content_id`.


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable each next word is to GPT-2 (perplexity), mapped to a 0–1 score where low perplexity means a high AI score.

**Why that might differ between human and AI writing:** A model writes by picking likely next words, so its output is easy for a model to predict. People make odder, more specific word choices.

**What it can't see:** Who wrote the text. It rewards plain, common words, so ESL writers, young writers and deliberately plain writers score as AI. Ornate AI prose full of rare words scores as human.

### Signal two — the style signal

**What it measures:** The shape of the text: how much sentence length varies, how much vocabulary repeats (type-token ratio), and how dense and varied the punctuation is.

**Why that might differ between human and AI writing:** Generated prose tends toward even, mid-length sentences and a narrower vocabulary. Human writing is lumpier, with a three-word sentence next to a forty-word one.

**What it can't see:** What the text means. Typos, chopped-up sentences or a pasted quotation change the shape without changing who wrote it. Type-token ratio also falls as text gets longer, so length alone can look like a signal.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Average the two signals with equal weight. If they disagree by a lot, the combined score is capped just below the AI band. A split can come out "unsure" or "human" but never "high-confidence AI", because an accusation needs both signals to point the same way.

**The numbers:**

- `WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5`
- `DISAGREEMENT_GAP = 0.35`: if `|model_score − style_score| ≥ 0.35`, the signals count as split.
- `DISAGREEMENT_CAP = 0.60`: a split's combined score can't go above 0.60. That's below the AI cutoff now (0.65) and below the one I plan to set (0.75–0.80).
- All of these live in `config.py`.

**How the style signal is built** (`stylometry.py::style_signal`): each measure is placed on a 0–1 "AI-ness" scale between two anchors I took from the calibration inputs. The three are then combined 0.4 / 0.4 / 0.2.

| Measure | Scores 0.0 (human) at | Scores 1.0 (AI) at | Weight |
|---|---|---|---|
| Sentence-length spread (stdev ÷ mean) | 0.90 | 0.30 | 0.4 |
| Punctuation density (`, ; : ! ? ( ) " —` per word, full stops excluded) | 0.12 (and, since unit 8, 0.00) | 0.02, peaking at 0.8 at 0.04 (unit 8: turns around below `PUNCT_AI_FLOOR`; see The Improvement) | 0.4 |
| Type-token ratio (moving average over 50 words, so length doesn't skew it) | 0.75 | **0.95** | 0.2 |

Type-token ratio runs **the opposite way** from the usual hint. In every calibration input, AI text had the *most* varied vocabulary (0.91–0.93) and plain human writing the least (0.76). Plain writers are the people this system wrongly accuses, so scoring varied vocabulary as AI-like also protects them. It gets the lowest weight because it rests on only five texts. Text under 30 words or 3 sentences gets a style score of 0.5, meaning no opinion.

**Calibration inputs:**

| Input | model | style | combined | Which signal is off? |
|---|---|---|---|---|
| Clearly AI (`samples/clearly_ai.json`) | 0.754 | 0.795 | **0.775** | Neither. They agree. |
| Clearly human (`samples/clearly_human.json`) | 0.445 | 0.070 | **0.257** | Model: it reads it as close to a coin flip. |
| Plain human (short sentences, simple words) | 0.853 | 0.811 | **0.832** | **Both.** It scores higher than the clearly-AI text. |
| Lightly edited AI (contractions, a dash, "honestly") | 0.606 | 0.526 | **0.566** | Both drift toward human. A light edit moves it into unsure. |
| Borderline (`samples/borderline.json`) | 0.349 | 0.498 | **0.424** | Model reads it as *more* human than the clearly-human sample. |

The plain-human result is the false positive traced in Milestone 1. Short, even sentences and no commas look AI-like to style, and common words look AI-like to the model. Both signals fail in the same direction, so no combining rule can rescue it. The only protection is where the AI cutoff sits (Milestone 5), the appeal path, and wording the AI label as "patterns common in AI text."

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

The clearly-human sample: `model_score` 0.445, `style_score` 0.070, a gap of 0.37. The model finds the wording fairly predictable ("I didn't sleep", "the long way round to work"). Style sees sentence lengths ranging from 2 to over 40 words, plus dashes, colons and quotes, all strongly human. The gap is over 0.35, so the cap applies. The average is already 0.257, under the cap, so the result stays 0.257 and the piece is labelled human.

The cap matters for the mirror case, a split that averages *high*. Model 0.95 with style 0.40 averages 0.675, which is "high-confidence AI" under the default 0.65 cutoff. My rule holds it at 0.60, which is unsure. One signal alone can't accuse someone.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text. |
| unsure | 0.35 – 0.75 | We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI. |
| high-confidence AI | 0.75 – 1.00 | This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result. |

The ranges come from `scoring.label_ranges()`, which reads them from `config.py`. A score of exactly 0.35 counts as human, and exactly 0.75 counts as AI. There are no gaps, and all three labels came up from the samples:

| Input | combined | Label it got |
|---|---|---|
| `samples/clearly_human.json` | 0.257 | high-confidence human |
| `samples/borderline.json` | 0.424 | unsure |
| `samples/clearly_ai.json` | 0.775 | high-confidence AI |

I raised the AI cutoff from the default 0.65 to **0.75**. The Milestone 1 trace put plain human writing at about 0.68, which 0.65 would accuse. 0.75 still lets clearly-AI text (0.775) reach the AI label. It doesn't save the plain-human calibration input (0.832), and that miss is logged above.

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

The person reading it may well have written every word, so the label has to be honest that we don't know without sounding like a soft accusation. It opens with "We can't tell either way" so the first thing they read is uncertainty, not suspicion. It names patterns of *both* kinds, so it doesn't sound like "probably AI, but we're being polite." "Plenty of people simply write this way" tells the writer their style is normal. It ends by saying outright that we're not claiming AI, because without that line a worried reader will assume we are. It avoids numbers and words like "confidence" or "score," which mean nothing to someone who has never heard of a threshold.

The AI label has the same care built in. It says "patterns," not "you used AI," says plainly that it isn't proof, and tells the reader how to appeal.


---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d @samples/clearly_ai.json
```

```json
{
  "confidence": 0.775,
  "content_id": "c_fd373e84c4f8",
  "guess": "ai",
  "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
  "model_score": 0.7544,
  "style_score": 0.7955
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "c_fd373e84c4f8", "reasoning": "I wrote this myself for a workplace newsletter. I write in a plain, structured way because that is how I was taught to write reports."}'
```

```json
{
  "content_id": "c_fd373e84c4f8",
  "message": "Thanks. Your appeal is recorded and a person will review this result. Keep your reference number in case you need to follow up.",
  "status": "under_review"
}
```

An unknown id gets a 404, and a missing `reasoning` gets a 400:

```json
{"error": "not_found", "message": "We couldn't find a result with reference c_doesnotexist. Check it matches the one shown with your result."}
{"error": "bad_request", "message": "Tell us in \"reasoning\" why you think the result is wrong."}
```

**What the log shows afterwards**

Every log entry for `c_fd373e84c4f8` (test rejections filtered out). The appeal entries sit next to the original decision and move the status from `decided` to `under_review`. The decision itself is never rewritten, so the record shows what was decided and what happened after. I appealed this item twice while testing, and both appeals are recorded.

```bash
$ curl -s "http://127.0.0.1:5000/log" \
  | jq '[.entries[] | select(.content_id == "c_fd373e84c4f8" and .event != "rejected")]'
```

```json
[
  {
    "timestamp": "2026-11-09T03:44:25+00:00",
    "content_id": "c_fd373e84c4f8",
    "creator_id": "demo_instructor",
    "guess": "ai",
    "model_score": 0.7544,
    "style_score": 0.7955,
    "combined_score": 0.775,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-09T03:44:30+00:00",
    "content_id": "c_fd373e84c4f8",
    "creator_id": "demo_instructor",
    "event": "appeal",
    "status": "under_review",
    "reasoning": "I wrote this myself for a workplace newsletter. I write in a plain, structured way because that is how I was taught to write reports."
  },
  {
    "timestamp": "2026-11-09T03:44:45+00:00",
    "content_id": "c_fd373e84c4f8",
    "creator_id": "demo_instructor",
    "event": "appeal",
    "status": "under_review",
    "reasoning": "I wrote this myself for a workplace newsletter. I write in a plain, structured way because that is how I was taught to write reports."
  }
]
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* Help with building on the stylometry.py
- *What came back:* Implemention of the stylometry functions with a description of what it has done.
- *What I changed:*

**Moment 2**

- *What I asked for:* Help with understand the repo so I can help with building the criteria.
- *What came back:* Give a description of the important files as well as example criterias. 
- *What I changed:* Had to make it give unrelated criterias.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 60 per day

**Why those numbers and not others:**
A real writer submits a draft, fixes something, and resubmits, maybe a few times in an hour. Five a minute leaves room for quick resubmits, and 60 a day covers a heavy day of revising. A script sending 1,000 variations to map my thresholds would finish in minutes with no limit. At 60 a day it needs about 17 days per creator_id, and every refused attempt is written to the audit log as `rate_limited`, so the probing is visible.

**What a caller counts as:** per `creator_id`, falling back to the caller's address when there isn't one. This is fair to a household or classroom sharing one IP. The weakness is that a script can make up a new `creator_id` for every request and get a fresh allowance each time. The per-day cap doesn't help with that, because it is also counted per creator_id.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

Full run output: [`results/attack_run_2026-11-11_0000.md`](results/attack_run_2026-11-11_0000.md). 56 attacks, rate limiting on (5/minute, 60/day), AI cutoff 0.75, human cutoff 0.35.

**How I marked them.** Each row's `targets` column says what the attack was going for. It **BROKE** if it got there:

- **evasion:** AI-written text escaped the AI label. Getting "unsure" counts as broken, because the attacker's text goes out without a flag.
- **false_positive:** genuine human writing got the "high-confidence AI" label.
- **prompt_injection:** the instruction changed the result, the label text or the log.
- **malformed:** the service crashed (5xx) or gave a confident verdict on input that isn't writing. A clean 4xx, or a non-committal "unsure", counts as held.
- **flood_same_creator:** submissions past the limit got through. The first five are inside the allowance and are supposed to be 200.

| ID | Family | Targeting | Status | Guess | Score | model / style | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.546 | 0.164 / 0.928 | **BROKE** |
| EV02 | evasion | signal two: broken-up sentences | 200 | unsure | 0.560 | 0.594 / 0.526 | **BROKE** |
| EV03 | evasion | signal two: pasted quotation | 200 | unsure | 0.691 | 0.666 / 0.715 | **BROKE** |
| EV04 | evasion | signal one: unusual words | 200 | ai | 0.771 | 0.611 / 0.931 | HELD |
| EV05 | evasion | both: heavy human editing pass | 200 | unsure | 0.408 | 0.321 / 0.495 | **BROKE** |
| EV06 | evasion | signal two: one very long + one very short sentence | 200 | unsure | 0.511 | 0.573 / 0.448 | **BROKE** |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.543 | 0.586 / 0.500 | **BROKE** |
| EV08 | evasion | signal one: below the token window | 200 | unsure | 0.373 | 0.245 / 0.500 | **BROKE** |
| EV09 | evasion | both: human opening bolted onto AI text | 200 | unsure | 0.738 | 0.704 / 0.772 | **BROKE** |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.858 | 0.979 / 0.737 | HELD |
| FP01 | false_positive | plain, clear human writing | 200 | unsure | 0.684 | 0.618 / 0.751 | HELD |
| FP02 | false_positive | formal register | 200 | ai | 0.779 | 0.739 / 0.820 | **BROKE** |
| FP03 | false_positive | non-native English speaker writing carefully | 200 | ai | 0.828 | 0.805 / 0.851 | **BROKE** |
| FP04 | false_positive | student essay written to a rubric | 200 | ai | 0.830 | 0.833 / 0.827 | **BROKE** |
| FP05 | false_positive | technical documentation | 200 | ai | 0.783 | 0.801 / 0.766 | **BROKE** |
| FP06 | false_positive | person imitating a formal template | 200 | ai | 0.771 | 0.881 / 0.660 | **BROKE** |
| FP07 | false_positive | deliberate repeated phrase | 200 | unsure | 0.600 | 0.882 / 0.457 | HELD |
| FP08 | false_positive | very short genuine submission | 200 | unsure | 0.411 | 0.322 / 0.500 | HELD |
| PI01 | prompt_injection | "ignore the check" | 200 | unsure | 0.602 | 0.463 / 0.742 | HELD |
| PI02 | prompt_injection | fake system message | 200 | unsure | 0.436 | 0.204 / 0.668 | HELD |
| PI03 | prompt_injection | instruction in the writer's voice | 200 | unsure | 0.701 | 0.594 / 0.807 | HELD |
| PI04 | prompt_injection | make the label text hostile | 200 | unsure | 0.556 | 0.500 / 0.612 | HELD |
| PI05 | prompt_injection | inject into the audit log | 200 | unsure | 0.570 | 0.640 / 0.500 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.662 | 0.558 / 0.766 | HELD |
| MF01 | malformed | only whitespace | 400 | — | — | — | HELD |
| MF02 | malformed | single character | **500** | — | — | — | **BROKE** |
| MF03 | malformed | control characters | 200 | human | 0.250 | 0.000 / 0.500 | **BROKE** |
| MF04 | malformed | only punctuation | 200 | human | 0.256 | 0.011 / 0.500 | **BROKE** |
| MF05 | malformed | very long single word | 200 | unsure | 0.600 | 0.998 / 0.500 | HELD |
| MF06 | malformed | emoji only | 200 | unsure | 0.600 | 0.997 / 0.500 | HELD |
| MF07 | malformed | right-to-left script | 200 | unsure | 0.600 | 0.906 / 0.500 | HELD |
| MF08 | malformed | 60,000 characters | 400 | — | — | — | HELD |
| RQ01 | malformed | no text field | 400 | — | — | — | HELD |
| RQ02 | malformed | no creator_id | 200 | unsure | 0.370 | 0.240 / 0.500 | HELD |
| RQ03 | malformed | text is a number | 400 | — | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | — | — | — | HELD |
| RQ05 | malformed | text is null | 400 | — | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 200 | human | 0.275 | 0.049 / 0.500 | HELD |
| RQ07 | malformed | body is a JSON array | 400 | — | — | — | HELD |
| RQ08 | malformed | unparseable JSON | 400 | — | — | — | HELD |
| RQ09 | malformed | empty body | 400 | — | — | — | HELD |
| RQ10 | malformed | form-encoded body | 429 | — | — | — | HELD* |
| RQ11 | malformed | JSON sent as text/plain | 429 | — | — | — | HELD* |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | — | HELD |
| FL01_01–05 | flood_same_creator | 20 rapid submissions, one creator | 200 ×5 | human | 0.264 | 0.029 / 0.500 | HELD |
| FL01_06–12 | flood_same_creator | 20 rapid submissions, one creator | 429 ×7 | — | — | — | HELD |

\*RQ10 and RQ11 never reached the route. RQ02, RQ06, RQ07, RQ08 and RQ09 have no usable `creator_id`, so they were all counted against my own address and used up its five-per-minute allowance. RQ10 and RQ11 were refused before the route could parse them. Nothing crashed, so I've marked them held, but this run didn't test how `/submit` handles a form-encoded or `text/plain` body. It also shows that **requests rejected with 400 still use up the allowance**.

**Counts**

| Family | Attacks | Held | Broke |
|---|---|---|---|
| evasion | 10 | 2 | **8** |
| false_positive | 8 | 3 | **5** |
| prompt_injection | 6 | 6 | 0 |
| malformed | 20 | 17 | **3** |
| flood_same_creator | 12 | 12 | 0 |
| **Total** | **56** | **40** | **16** |

**What the breaks have in common**

- **Evasion (8 of 10).** The AI cutoff sits at 0.75 and the clearly-AI calibration text only scored 0.775. Almost any edit is enough to push AI text into "unsure". EV09 missed the AI label by 0.012. Nothing got all the way to "human", though. The lowest evasion score was EV05 at 0.408.
- **EV01 didn't work the way it was meant to.** It was aimed at signal two, but the typos made style score it *more* AI-like (0.928). What actually moved was signal one: GPT-2 finds misspellings unpredictable, so the model score fell to 0.164. The signals then split, and averaging them gave "unsure".
- **False positives (5 of 8).** All five have both signals above 0.65 and agreeing: formal, rubric, ESL, technical and template writing. My disagreement cap only steps in when the signals split, so it did nothing for these. The gap in FP06 was 0.22, under the 0.35 split threshold. The cap did save FP07: model 0.882 and style 0.457 averaged 0.67, and the cap held it to 0.600.
- **The cap only works in one direction.** One signal can't *accuse* on its own, but it can *clear* on its own. MF03 and MF04 got a model score near 0 because GPT-2 can't predict junk. Style returns its 0.5 "no opinion" for very short text, so the average lands at 0.25, which is "high-confidence human". That's a confident verdict on text that isn't writing. EV08 (0.373) is the same mechanism stopping just short of the human label.
- **MF02 (500).** `detector.perplexity` raises `ValueError("Text is too short to score…")` for a single token, and `app.py::submit` doesn't catch it. The 500 also left **no entry in the audit log**, so the crash is visible only in this run's output, not in my own records.
- **Prompt injection held all six** because there's no language model reading instructions. The text is only ever scored. Labels are fixed strings from `config.py`, and the log is written with `json.dumps` and never stores the submitted text, so PI04 and PI05 had nothing to grab onto. The injected wording does move the scores, though. PI02's "SYSTEM:" header pushed the model score down to 0.204, so injection works as an evasion trick even though it fails as an instruction.

**Audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

Twelve entries pulled from `logs/audit.jsonl` for this run (05:00:34–05:00:36 UTC). In order:

1. FP03, the worst outcome
2. FP04, a rubric essay accused
3. FP06, a split that stayed under the gap threshold
4. EV09, 0.012 under the AI cutoff
5. EV01, typos hitting the wrong signal
6. EV08, short text drifting toward human
7. FP07, where the cap worked
8. MF03, control characters labelled human
9. MF05, junk saved only by the cap
10. RQ10, a creator-less request refused by the limiter
11. FL01_06, the first rate-limited flood row
12. MF08, an oversized text rejected

```json
[
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_2330b368c835",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "model_score": 0.8051,
    "style_score": 0.8506,
    "combined_score": 0.8278,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_7759b61279a7",
    "creator_id": "attacker_FP04",
    "guess": "ai",
    "model_score": 0.8329,
    "style_score": 0.8266,
    "combined_score": 0.8297,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_4176327d234f",
    "creator_id": "attacker_FP06",
    "guess": "ai",
    "model_score": 0.8814,
    "style_score": 0.6599,
    "combined_score": 0.7707,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_7197dff135c8",
    "creator_id": "attacker_EV09",
    "guess": "unsure",
    "model_score": 0.7042,
    "style_score": 0.7722,
    "combined_score": 0.7382,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:34+00:00",
    "content_id": "c_8a86d99cb1f4",
    "creator_id": "attacker_EV01",
    "guess": "unsure",
    "model_score": 0.1635,
    "style_score": 0.9282,
    "combined_score": 0.5459,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_649f70685ce2",
    "creator_id": "attacker_EV08",
    "guess": "unsure",
    "model_score": 0.2452,
    "style_score": 0.5,
    "combined_score": 0.3726,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_4170b4772215",
    "creator_id": "attacker_FP07",
    "guess": "unsure",
    "model_score": 0.8816,
    "style_score": 0.4571,
    "combined_score": 0.6,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:35+00:00",
    "content_id": "c_c321193c9a26",
    "creator_id": "attacker_MF03",
    "guess": "human",
    "model_score": 0.0,
    "style_score": 0.5,
    "combined_score": 0.25,
    "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:36+00:00",
    "content_id": "c_5b4b7de57f07",
    "creator_id": "attacker_MF05",
    "guess": "unsure",
    "model_score": 0.9976,
    "style_score": 0.5,
    "combined_score": 0.6,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T05:00:36+00:00",
    "content_id": null,
    "creator_id": "unknown",
    "guess": null,
    "model_score": null,
    "style_score": null,
    "combined_score": null,
    "label": null,
    "status": "rejected",
    "event": "rejected",
    "reason": "rate_limited",
    "limit": "5 per 1 minute"
  },
  {
    "timestamp": "2026-11-11T05:00:36+00:00",
    "content_id": null,
    "creator_id": "attacker_flood",
    "guess": null,
    "model_score": null,
    "style_score": null,
    "combined_score": null,
    "label": null,
    "status": "rejected",
    "event": "rejected",
    "reason": "rate_limited",
    "limit": "5 per 1 minute"
  },
  {
    "timestamp": "2026-11-11T05:00:36+00:00",
    "content_id": null,
    "creator_id": "attacker_MF08",
    "guess": null,
    "model_score": null,
    "style_score": null,
    "combined_score": null,
    "label": null,
    "status": "rejected",
    "event": "rejected",
    "reason": "text_too_long",
    "length": 57640
  }
]
```

One more thing about the log: **MF02's 500 has no entry here.** The crash happens before `audit.log_decision` or `log_rejection` runs, so the log has no record of the request at all.

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**FP03: a non-native English speaker writing carefully about their first month in a new country got "high-confidence AI" at 0.828.** It's the exact writer I traced in Milestone 1, and the system still accused them after every safeguard I built for that case.

- **Both signals were confident and agreed** (model 0.805, style 0.851). The disagreement cap had nothing to catch.
- **0.828 is well clear of the 0.75 cutoff** I raised specifically to protect plain writers.
- **The label is wrong for the reason they can least change.** They write in short, safe sentences with familiar words *because* English is their second language. What the system read as machine-like was the care they took. Telling them "this has strong patterns common in AI-generated text" amounts to telling them their English sounds fake.

The appeal path exists, but they have to know to use it, feel confident enough to argue in a second language, and wait for a person. FP04, the rubric essay, scored slightly higher (0.830). FP03 is worse because the writer has fewer ways to defend themselves and the accusation lands on who they are, not on a choice they made.


---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

`python run_eval.py --label before`, three trials, nothing changed in between. Full output: [`results/run_2026-11-11_0020_before.md`](results/run_2026-11-11_0020_before.md). Thresholds are the same as the attack run: human below 0.35, AI at 0.75 and above.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own writing labelled high-confidence AI | ≤ 1 of 10 | 0/10 | 0/10 | 0/10 | MET |
| 2. Clearly-AI average minus clearly-human average | ≥ 0.30 | 0.403 | 0.403 | 0.403 | MET |
| 3. Appeals on real ids → 200, `under_review`, logged; unknown id → 404 | 10 of 10, 2 of 2 | 10/10, 2/2 | 10/10, 2/2 | 10/10, 2/2 | MET |
| 4. All three labels reached, and ≤ 1 of 3 clearly-human inputs in "unsure" | 3 of 3 labels, ≤ 1 of 3 | 3/3, **2 of 3** | 3/3, **2 of 3** | 3/3, **2 of 3** | MISSED |
| 5. Missing, empty, null and 100,000-char text → 400 with `{error, message}`, logged as rejected | 4 of 4 | 4/4 | 4/4 | 4/4 | MET |

**How each criterion was tested**

- **1.** Ten pieces I wrote myself, saved word for word in `samples/own_writing.json`: two cover letters, two history essays, a recommendation letter, two bios, two sets of event instructions and a Facebook post.
- **2 and 4.** Nine calibration inputs:
  - **Clearly AI:** `samples/clearly_ai.json` plus two paragraphs generated by Claude.
  - **Borderline:** `samples/borderline.json`, `samples/lightly_edited_ai.json` and attack row EV05.
  - **Clearly human:** `samples/clearly_human.json` plus my two most informal pieces, the STEM Hive post and the video brief. I chose those two by register before scoring anything.
  - Criterion 2 uses the AI and human inputs from this set.
- **3.** `run_eval.py` could only call `/submit`, so I extended it (`run_eval.py::run_appeals`). For each of ten texts (attack rows FP01–FP08 plus two samples) it submits the text, appeals the `content_id` that came back, and then reads `/log` to confirm the appeal entry is there. It also appeals two made-up ids, which should return 404.
- **5.** The four bodies are sent exactly as written. For bodies with `check_log`, `run_eval.py::newest_log_entry` reads the newest log line after each request.

**The three trials were identical** to four decimal places. GPT-2 runs in eval mode with no sampling, so the same text always gets the same perplexity. Three trials ruled out run-to-run noise. They don't add any information beyond that.

**What the numbers hide**

- **Criterion 1 passed, but none of my pieces was labelled human.** All ten came back "unsure", with scores from 0.408 to 0.634. Nothing reached 0.75. Nothing went under 0.35 either, including the casual Facebook post (0.494). Every piece I've written gets the label "We can't tell either way."
- **Criterion 4 is the miss.** Both of my own informal pieces landed in "unsure", at 0.494 and 0.434. Only the sample paragraph reached "high-confidence human" (0.257). Style is the signal that separates them. The sample gets a style score of 0.070. My post gets 0.469 and the brief 0.475, so style has no opinion on my writing either way. The model scores are about the same for all three (0.445, 0.518, 0.393). This is where the Diagnoses section should start.

**Real output from trial 1 for each criterion**

Produced by `run_eval.py::main`, which calls `/submit` (`app.py::submit`), and `run_eval.py::run_appeals` for criterion 3. Copied from `results/run_2026-11-11_0020_before.md`.

*Criterion 1: my own writing* (`app.py::submit` → `scoring.py::combine_signals` → `scoring.py::score_to_label`)

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6343,
    "model_score": 0.7231,
    "style_score": 0.5455,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "My name is Daniel Gastonand I am excited to apply for the Infrastructu"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6083,
    "model_score": 0.695,
    "style_score": 0.5216,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "I am writing to express my enthusiastic interest in the Software Engin"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4339,
    "model_score": 0.3925,
    "style_score": 0.4753,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "We have a questionnaire of topics that you can talk about. However we "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5991,
    "model_score": 0.7504,
    "style_score": 0.4479,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Daniel's connection with CECC began when he joined Malborough for Pre-"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4083,
    "model_score": 0.3701,
    "style_score": 0.4465,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Urban spaces have been interpreted and been transformed due to many fa"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4593,
    "model_score": 0.601,
    "style_score": 0.3177,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "In Victoria Siu\u2019s book chapter \u201cExperiencing the Garden of Perfect Bri"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5273,
    "model_score": 0.3611,
    "style_score": 0.6935,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Dear SHPE National Office,\n\tAs a former SHPE CCNY member that graduate"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5226,
    "model_score": 0.5398,
    "style_score": 0.5054,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "There are 20 Questions in total you will have the opportunity to answe"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5912,
    "model_score": 0.3842,
    "style_score": 0.7982,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Daniel is a Haitian American Senior at the City College of New York ma"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4936,
    "model_score": 0.5183,
    "style_score": 0.469,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Hey guys. I have admitted defeat for the gif pause challenge. Your rew"
  }
]
```

*Criterion 2: score spread* (the first three are clearly AI and the last three clearly human, giving averages of 0.7977 and 0.3949, a gap of 0.403)

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.775,
    "model_score": 0.7544,
    "style_score": 0.7955,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "The importance of effective time management cannot be overstated in to"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7787,
    "model_score": 0.6999,
    "style_score": 0.8574,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "Remote work has fundamentally transformed the modern workplace. Organi"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8394,
    "model_score": 0.9073,
    "style_score": 0.7714,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "Regular physical activity offers numerous benefits for both physical a"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2572,
    "model_score": 0.4445,
    "style_score": 0.07,
    "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
    "sent": "I didn't sleep. Not properly, anyway \u2014 I lay there listening to the bo"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4936,
    "model_score": 0.5183,
    "style_score": 0.469,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Hey guys. I have admitted defeat for the gif pause challenge. Your rew"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4339,
    "model_score": 0.3925,
    "style_score": 0.4753,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "We have a questionnaire of topics that you can talk about. However we "
  }
]
```

*Criterion 3: appeal path* (`run_eval.py::run_appeals` → `app.py::appeal` → `audit.py::log_appeal`)

```json
[
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_5ad41d868b2a",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_5ad41d868b2a",
      "creator_id": "eval_appeal path_1",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_457ba3031a5c",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_457ba3031a5c",
      "creator_id": "eval_appeal path_2",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_7f13fe45efaf",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_7f13fe45efaf",
      "creator_id": "eval_appeal path_3",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_769ea7901bef",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_769ea7901bef",
      "creator_id": "eval_appeal path_4",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_62a58fc978a0",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_62a58fc978a0",
      "creator_id": "eval_appeal path_5",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_c7a1c7547d1f",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_c7a1c7547d1f",
      "creator_id": "eval_appeal path_6",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_470c25728d66",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_470c25728d66",
      "creator_id": "eval_appeal path_7",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_a8926192231a",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_a8926192231a",
      "creator_id": "eval_appeal path_8",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_07638759732f",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_07638759732f",
      "creator_id": "eval_appeal path_9",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "real_id",
    "submit_status": 200,
    "content_id": "c_c097250343c2",
    "appeal_status": 200,
    "status_after": "under_review",
    "appeal_logged": true,
    "log_entry": {
      "combined_score": null,
      "content_id": "c_c097250343c2",
      "creator_id": "eval_appeal path_10",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "I wrote this myself and would like a person to review it.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:20+00:00"
    }
  },
  {
    "kind": "unknown_id",
    "content_id": "c_doesnotexist",
    "appeal_status": 404,
    "response": {
      "error": "not_found",
      "message": "We couldn't find a result with reference c_doesnotexist. Check it matches the one shown with your result."
    }
  },
  {
    "kind": "unknown_id",
    "content_id": "c_000000000000",
    "appeal_status": 404,
    "response": {
      "error": "not_found",
      "message": "We couldn't find a result with reference c_000000000000. Check it matches the one shown with your result."
    }
  }
]
```

*Criterion 4: label coverage* (in order: 3 clearly AI, 3 borderline, 3 clearly human)

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.775,
    "model_score": 0.7544,
    "style_score": 0.7955,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "The importance of effective time management cannot be overstated in to"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7787,
    "model_score": 0.6999,
    "style_score": 0.8574,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "Remote work has fundamentally transformed the modern workplace. Organi"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8394,
    "model_score": 0.9073,
    "style_score": 0.7714,
    "label": "This piece has strong patterns that are common in AI-generated text. That isn't proof: clear, plain writing by a person can look like this too. If you wrote it yourself, you can ask a person to review it using the reference number shown with this result.",
    "sent": "Regular physical activity offers numerous benefits for both physical a"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4236,
    "model_score": 0.3489,
    "style_score": 0.4983,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Time management matters more than people admit, especially now that wo"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.659,
    "model_score": 0.5813,
    "style_score": 0.7366,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Time management matters a lot in todays fast-paced work environment. P"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4082,
    "model_score": 0.3212,
    "style_score": 0.4952,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2572,
    "model_score": 0.4445,
    "style_score": 0.07,
    "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
    "sent": "I didn't sleep. Not properly, anyway \u2014 I lay there listening to the bo"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4936,
    "model_score": 0.5183,
    "style_score": 0.469,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "Hey guys. I have admitted defeat for the gif pause challenge. Your rew"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4339,
    "model_score": 0.3925,
    "style_score": 0.4753,
    "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
    "sent": "We have a questionnaire of topics that you can talk about. However we "
  }
]
```

*Criterion 5: bad input* (`app.py::submit` validation → `audit.py::log_rejection`, with the newest log line after each request)

```json
[
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_bad_missing\"}",
    "error": "bad_request",
    "message": "Send JSON with a non-empty \"text\" string.",
    "log_entry": {
      "combined_score": null,
      "content_id": null,
      "creator_id": "eval_bad_missing",
      "event": "rejected",
      "guess": null,
      "label": null,
      "model_score": null,
      "reason": "missing_or_empty_text",
      "status": "rejected",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:23+00:00"
    }
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)",
    "error": "bad_request",
    "message": "Send JSON with a non-empty \"text\" string.",
    "log_entry": {
      "combined_score": null,
      "content_id": null,
      "creator_id": "eval_bad_empty",
      "event": "rejected",
      "guess": null,
      "label": null,
      "model_score": null,
      "reason": "missing_or_empty_text",
      "status": "rejected",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:23+00:00"
    }
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": null, \"creator_id\": \"eval_bad_null\"}",
    "error": "bad_request",
    "message": "Send JSON with a non-empty \"text\" string.",
    "log_entry": {
      "combined_score": null,
      "content_id": null,
      "creator_id": "eval_bad_null",
      "event": "rejected",
      "guess": null,
      "label": null,
      "model_score": null,
      "reason": "missing_or_empty_text",
      "status": "rejected",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:23+00:00"
    }
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "word word word word word word word word word word word word word word ",
    "error": "bad_request",
    "message": "\"text\" is too long (100000 characters). The limit is 20000.",
    "log_entry": {
      "combined_score": null,
      "content_id": null,
      "creator_id": "eval_bad_huge",
      "event": "rejected",
      "guess": null,
      "label": null,
      "length": 100000,
      "model_score": null,
      "reason": "text_too_long",
      "status": "rejected",
      "style_score": null,
      "timestamp": "2026-11-11T05:20:23+00:00"
    }
  }
]
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

There's one miss (criterion 4) and 16 broken attacks. They come down to **five problems**. Most of the failures fall under the first three.

To see the three measures inside signal two, I scored every failing input with `stylometry.py`'s functions directly. The arrow shows each raw value's AI-ness after scaling, where 1.00 means fully AI-like. Weights are spread 0.4, punctuation 0.4 and type-token ratio 0.2.

| Input | spread → AI-ness | punct → AI-ness | TTR → AI-ness | style | model | combined |
|---|---|---|---|---|---|---|
| `clearly_ai.json` (real AI) | 0.413 → 0.81 | 0.043 → 0.77 | 0.915 → 0.82 | 0.796 | 0.754 | 0.775 |
| FP02 formal | 0.240 → 1.00 | 0.013 → **1.00** | 0.770 → 0.10 | 0.820 | 0.739 | 0.779 |
| FP03 ESL | 0.328 → 0.95 | 0.000 → **1.00** | 0.819 → 0.35 | 0.851 | 0.805 | 0.828 |
| FP04 rubric essay | 0.367 → 0.89 | 0.015 → **1.00** | 0.821 → 0.36 | 0.827 | 0.833 | 0.830 |
| FP05 tech docs | 0.277 → 1.00 | 0.029 → **0.91** | 0.626 → 0.00 | 0.766 | 0.801 | 0.783 |
| FP06 template | 0.519 → 0.63 | 0.016 → **1.00** | 0.756 → 0.03 | 0.660 | 0.881 | 0.771 |
| EV02 broken-up sentences | 0.849 → 0.08 | 0.033 → 0.87 | 0.894 → 0.72 | 0.526 | 0.594 | 0.560 |
| EV06 one long + one short | 1.186 → 0.00 | 0.033 → 0.87 | 0.849 → 0.49 | 0.448 | 0.573 | 0.511 |
| EV07 semicolon padding | **1 sentence**, gate fires | | | 0.500 | 0.586 | 0.543 |
| EV08 ten words | **10 words**, gate fires | | | 0.500 | 0.245 | 0.373 |
| My STEM Hive post | 0.674 → 0.38 | 0.058 → 0.62 | 0.821 → 0.35 | 0.469 | 0.518 | 0.494 |
| My video brief | 0.512 → 0.65 | 0.083 → 0.37 | 0.817 → 0.34 | 0.475 | 0.393 | 0.434 |

### Problem 1: signal two's punctuation measure points the wrong way for plain writers (5 false positives)

**FP02, FP03, FP04, FP05 and FP06 broke.**

- **What these inputs share.** Each one is a real person writing formally or carefully: a formal report, an ESL writer, a rubric essay, technical documentation and a letter template. Every one uses fewer commas, dashes and quotes than the actual AI text does. Their punctuation density is 0.000–0.029 per word, against 0.043 for `clearly_ai.json`.
- **Why that flags them.** I anchored "AI" at 0.02, so all five max out the punctuation measure at 0.91–1.00, *more* AI-like than the real AI text (0.77). Spread does the same thing: careful writers keep their sentences even (0.24–0.52), so it scores them 0.63–1.00.
- **Together that's 80% of the style signal** pointing the wrong way. The only measure that protects them is type-token ratio (0.00–0.36). I flipped it for exactly this reason, but it only carries 0.2 of the weight.
- **Signal one fails in the same direction.** Plain, common words are easy for GPT-2 to predict, so the model score is 0.74–0.88.
- **The combining rule can't help.** The cap only acts when the signals split by 0.35 or more. Here they agree, with gaps of 0.01–0.22, so the average passes straight through.
- **The label mapping lets it through.** All five land at 0.771–0.830, just over the 0.75 cutoff.

**The stage is signal two. The mechanism is that its punctuation and spread anchors came from one AI paragraph, and plain human writing sits beyond that anchor on the AI side.** I made the same mistake with type-token ratio in Milestone 4 and fixed it there, but not here. This is one problem, not five.

### Problem 2: signal two's "no opinion" counts as a full vote (EV07, EV08, MF03, MF04)

**EV07, EV08, MF03 and MF04 broke.**

- **When the gate fires.** `style_signal` returns 0.5 when text has fewer than 30 words or fewer than 3 sentences.
- **How it gets triggered.** EV07 chains its whole text together with semicolons. The sentence splitter only breaks on `.`, `!` and `?`, so it sees **1 sentence** and the gate fires. EV08 is only ten words long. MF03 (control characters) and MF04 (punctuation only) have 3 and 0 words.
- **Why it matters.** `scoring.py::combine_signals` averages that 0.5 at full weight. Half the final score is a placeholder, which halves signal one's influence and pulls everything towards the middle.
- **EV07 and EV08:** AI text escaped the AI label just by being short or having no full stops.
- **MF03 and MF04:** junk text got a confident human verdict. Signal one scored them 0.000 and 0.011, and an average of (0 + 0.5) / 2 = 0.25 is "high-confidence human". The disagreement cap only limits scores from above, so one signal on its own can clear a text even though it can't accuse one.

**The stage is the combining rule. The mechanism is that "no opinion" is treated as a 0.5 vote instead of being left out, and the cap only works in one direction.**

### Problem 3: the AI cutoff has almost no headroom above real AI text (EV03, EV05, EV09, plus EV02 and EV06)

**EV03, EV05 and EV09 broke, and EV02 and EV06 broke partly for this reason.**

- **The headroom.** Unedited AI text scores 0.775. I raised the cutoff to 0.75 to protect plain writers, which leaves AI text only 0.025 above it.
- **EV03** (pasted quote) moved both signals slightly: the model fell from 0.754 to 0.666 and style from 0.796 to 0.715. It ended at 0.691.
- **EV09** (human opening) ended at 0.738, 0.012 under the cutoff.
- **EV05** is a heavy human rewrite (0.408). I think the system is honestly right to stop calling it AI.
- **EV02 and EV06** went through spread. Spread is stdev ÷ mean over 6–13 sentences, so a single outlier dominates it. One very long sentence (EV06, spread 1.19) or a few one-word sentences (EV02, 0.85) is enough to zero out that measure, which is 0.4 of the style score.

**The stage is the label mapping, with signal two's spread measure doing the pushing. The mechanism is that the AI band starts where real AI text ends, so any edit at all crosses the line.** This is the cost of Problem 1. I couldn't put the cutoff lower without accusing plain writers, because signal two can't tell plain writers from AI.

### Problem 4: signal one reads noise as human (EV01, plus MF03, MF04 and EV08)

**EV01 broke.**

- **The attack was aimed at signal two**, adding typos to raise word variety. It did, but in the AI direction: style went *up* to 0.928, because I flipped type-token ratio.
- **What actually moved was signal one.** GPT-2 has never seen "importnace" and finds it unpredictable. The model score fell from 0.754 to 0.164.
- **The cap kicked in.** The signals split by 0.76, so the rule capped the result, and it landed in "unsure" at 0.546.

**The stage is signal one. The mechanism is that perplexity measures surprise, and typos, junk and very short text are all surprising.** The same thing drives MF03 (0.000), MF04 (0.011) and EV08 (0.245). Signal one's strongest "human" readings in the whole run went to garbage. My own writing scored 0.36–0.75.

### Problem 5: the route doesn't catch a signal exception (MF02)

**MF02 broke.** A single character `"a"` passes validation, because it's a non-empty string. `detector.perplexity` then raises `ValueError("Text is too short to score…")` because one token has nothing to predict. `app.py::submit` doesn't catch it, so Flask returns an HTML 500. The exception happens before `audit.log_decision`, so **the request leaves no log entry at all**.

**The stage is the route. The mechanism is that it validates "is this a non-empty string" but never "can the signals score this", and nothing catches a signal failure.**

### Criterion 4 miss: everything collapses to the middle

**Two of three clearly-human inputs landed in "unsure"**, and they were both my own informal writing (0.494 and 0.434).

- **Signal two is middling on every measure** (0.469 and 0.475). Neither piece is extreme in any direction. The sample that did reach "human" scored 0.070 on style, because its sentences range from 2 to 40+ words and it's full of dashes and quotes.
- **Signal one has a high floor for real prose.** Its midpoint is a perplexity of 45, which scores 0.5, and ordinary human writing sits around there. My ten pieces scored 0.36–0.75 on the model, and only noise ever gets it below 0.3 (Problem 4).

So reaching the human band (under 0.35) takes a style score near 0.1, and only unusually showy prose gets that. **The stage is the label mapping together with signal one's midpoint. The mechanism is that, for ordinary human writing, neither signal ever moves far below 0.5, so the combined score can't reach 0.35.**

### Was any target too easy?

Criterion 1 passed (0 of 10 called AI), but **it passed for the same reason criterion 4 failed**. All ten of my pieces landed in "unsure", and none came back human. A criterion that only counts AI labels can't see that a writer is never believed. I'd tighten it to also require that at least half of my own pieces are labelled human. That target would have failed: 0 of 10.

Criteria 3 and 5 are route checks with exact expected status codes, so they're either met or not. They held, but criterion 5 only lists four bad inputs, and the attack set found a fifth (a single character → 500) that it didn't cover.


---

## The Improvement

**What I changed:**

One change, to one measure inside signal two: the punctuation density measure in `stylometry.py::style_signal`. It now turns around below a new constant, `PUNCT_AI_FLOOR = 0.04`.

- **At 0.04 and above, nothing changed.** It's the same line as before, with human at 0.12 and AI at 0.02.
- **Below 0.04,** which is sparser than any AI calibration text, AI-ness falls in a straight line from 0.8 to 0 at no punctuation. Very sparse punctuation now counts as a sign of a plain human writer, not of AI.

```python
punct = punctuation_density(text)
if punct >= PUNCT_AI_FLOOR:
    punct_ai = _scale(punct, human=0.12, ai=0.02)       # unchanged above the floor
else:
    peak = _scale(PUNCT_AI_FLOOR, human=0.12, ai=0.02)  # 0.8, where the two lines meet
    punct_ai = peak * punct / PUNCT_AI_FLOOR            # falls to 0 at no punctuation
```

The 0.04 comes from the calibration inputs, not the attack set. The three clearly-AI inputs scored 0.0435, 0.0549 and 0.0532. Every human calibration input and all ten of my own pieces scored 0.046 or higher. The writers the attack set accused scored 0.000–0.029. I left all weights, cutoffs, the combining rule and signal one untouched.

**Which diagnosis pointed at it:** Problem 1, the one behind all five false positives. Plain and formal writers use *less* punctuation than real AI text does, so the old measure rated them more AI-like than the AI. I chose it over the cheaper Problem 2 fix because a false positive accuses a real person. This was the expensive error, and the attack set's FP family was where it showed up.

Before changing anything, I simulated the change offline, using the before run's model scores (GPT-2 gives the same score every time) with the new style scores. The prediction matched the real after-run on every row.

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

`python run_attacks.py --set attack_set --label after`. Before: [`results/attack_run_2026-11-11_0000.md`](results/attack_run_2026-11-11_0000.md). After: [`results/attack_run_2026-11-11_0034_after.md`](results/attack_run_2026-11-11_0034_after.md). I marked verdicts with the same rules as the before run. ⬅ marks a row whose verdict changed.

| Family | Attacks | Before: held / broke | After: held / broke |
|---|---|---|---|
| evasion | 10 | 2 / 8 | **0 / 10** |
| false_positive | 8 | 3 / 5 | **8 / 0** |
| prompt_injection | 6 | 6 / 0 | 6 / 0 |
| malformed | 20 | 17 / 3 | 17 / 3 |
| flood_same_creator | 12 | 12 / 0 | 12 / 0 |
| **Total** | **56** | **40 / 16** | **43 / 13** |

| ID | Family | Before (guess, score) | After (guess, score) | style before → after | Before | After |
|---|---|---|---|---|---|---|
| EV01 | evasion | unsure 0.546 | unsure 0.518 | 0.9282 → 0.8718 | **BROKE** | **BROKE** |
| EV02 | evasion | unsure 0.560 | unsure 0.518 | 0.5262 → 0.4422 | **BROKE** | **BROKE** |
| EV03 | evasion | unsure 0.691 | unsure 0.691 | 0.7153 → 0.7153 | **BROKE** | **BROKE** |
| EV04 ⬅ | evasion | ai 0.771 | unsure 0.741 | 0.9309 → 0.8697 | HELD | **BROKE** |
| EV05 | evasion | unsure 0.408 | unsure 0.408 | 0.4952 → 0.4952 | **BROKE** | **BROKE** |
| EV06 | evasion | unsure 0.511 | unsure 0.466 | 0.4484 → 0.3596 | **BROKE** | **BROKE** |
| EV07 | evasion | unsure 0.543 | unsure 0.543 | 0.5 → 0.5 | **BROKE** | **BROKE** |
| EV08 | evasion | unsure 0.373 | unsure 0.373 | 0.5 → 0.5 | **BROKE** | **BROKE** |
| EV09 | evasion | unsure 0.738 | unsure 0.738 | 0.7722 → 0.7722 | **BROKE** | **BROKE** |
| EV10 ⬅ | evasion | ai 0.858 | unsure 0.600 | 0.7374 → 0.3374 | HELD | **BROKE** |
| FP01 | false_positive | unsure 0.684 | unsure 0.562 | 0.7513 → 0.5065 | HELD | HELD |
| FP02 ⬅ | false_positive | ai 0.779 | unsure 0.632 | 0.8196 → 0.5252 | **BROKE** | HELD |
| FP03 ⬅ | false_positive | ai 0.828 | unsure 0.600 | 0.8506 → 0.4506 | **BROKE** | HELD |
| FP04 ⬅ | false_positive | ai 0.830 | unsure 0.689 | 0.8266 → 0.5442 | **BROKE** | HELD |
| FP05 ⬅ | false_positive | ai 0.783 | unsure 0.715 | 0.7656 → 0.6288 | **BROKE** | HELD |
| FP06 ⬅ | false_positive | ai 0.771 | unsure 0.600 | 0.6599 → 0.3847 | **BROKE** | HELD |
| FP07 | false_positive | unsure 0.600 | unsure 0.600 | 0.4571 → 0.3839 | HELD | HELD |
| FP08 | false_positive | unsure 0.411 | unsure 0.411 | 0.5 → 0.5 | HELD | HELD |
| PI01 | prompt_injection | unsure 0.602 | unsure 0.402 | 0.7415 → 0.3415 | HELD | HELD |
| PI02 | prompt_injection | unsure 0.436 | unsure 0.436 | 0.6679 → 0.6679 | HELD | HELD |
| PI03 | prompt_injection | unsure 0.701 | unsure 0.701 | 0.8066 → 0.8066 | HELD | HELD |
| PI04 | prompt_injection | unsure 0.556 | unsure 0.556 | 0.6119 → 0.6119 | HELD | HELD |
| PI05 | prompt_injection | unsure 0.570 | unsure 0.570 | 0.5 → 0.5 | HELD | HELD |
| PI06 | prompt_injection | unsure 0.662 | unsure 0.533 | 0.7656 → 0.5072 | HELD | HELD |
| MF01 | malformed | 400 | 400 | — | HELD | HELD |
| MF02 | malformed | 500 | 500 | — | **BROKE** | **BROKE** |
| MF03 | malformed | human 0.250 | human 0.250 | 0.5 → 0.5 | **BROKE** | **BROKE** |
| MF04 | malformed | human 0.256 | human 0.256 | 0.5 → 0.5 | **BROKE** | **BROKE** |
| MF05 | malformed | unsure 0.600 | unsure 0.600 | 0.5 → 0.5 | HELD | HELD |
| MF06 | malformed | unsure 0.600 | unsure 0.600 | 0.5 → 0.5 | HELD | HELD |
| MF07 | malformed | unsure 0.600 | unsure 0.600 | 0.5 → 0.5 | HELD | HELD |
| MF08 | malformed | 400 | 400 | — | HELD | HELD |
| RQ01 | malformed | 400 | 400 | — | HELD | HELD |
| RQ02 | malformed | unsure 0.370 | unsure 0.370 | 0.5 → 0.5 | HELD | HELD |
| RQ03 | malformed | 400 | 400 | — | HELD | HELD |
| RQ04 | malformed | 400 | 400 | — | HELD | HELD |
| RQ05 | malformed | 400 | 400 | — | HELD | HELD |
| RQ06 | malformed | human 0.275 | human 0.275 | 0.5 → 0.5 | HELD | HELD |
| RQ07 | malformed | 400 | 400 | — | HELD | HELD |
| RQ08 | malformed | 400 | 400 | — | HELD | HELD |
| RQ09 | malformed | 400 | 400 | — | HELD | HELD |
| RQ10 | malformed | 429 | 429 | — | HELD | HELD |
| RQ11 | malformed | 429 | 429 | — | HELD | HELD |
| RQ12 | malformed | 400 | 400 | — | HELD | HELD |
| FL01_01–12 | flood_same_creator | `200 200 200 200 200 429 429 429 429 429 429 429` | `200 200 200 200 200 429 429 429 429 429 429 429` | — | HELD ×12 | HELD ×12 |

### Run Log — After

`python run_eval.py --label after`, three trials. Before: [`results/run_2026-11-11_0020_before.md`](results/run_2026-11-11_0020_before.md). After: [`results/run_2026-11-11_0034_after.md`](results/run_2026-11-11_0034_after.md).

| Criterion | Target | Before: Run 1 / 2 / 3 | Before | After: Run 1 / 2 / 3 | After |
|---|---|---|---|---|---|
| 1. My own writing labelled high-confidence AI | ≤ 1 of 10 | 0/10 · 0/10 · 0/10 | MET | 0/10 · 0/10 · 0/10 | MET |
| 2. Clearly-AI average minus clearly-human average | ≥ 0.30 | 0.403 · 0.403 · 0.403 | MET | 0.403 · 0.403 · 0.403 | MET |
| 3. Appeals → 200 + `under_review` + logged; unknown → 404 | 10/10, 2/2 | 10/10, 2/2 ×3 | MET | 10/10, 2/2 ×3 | MET |
| 4. All three labels reached; ≤ 1 of 3 clearly-human in "unsure" | 3/3, ≤ 1 | 3/3, 2 of 3 ×3 | MISSED | 3/3, 2 of 3 ×3 | MISSED |
| 5. Bad input → 400 `{error, message}`, logged | 4 of 4 | 4/4 ×3 | MET | 4/4 ×3 | MET |

The after-run output for every criterion is identical to the before-run output (see Run Log and Verdicts above). The only differences are `content_id`s and timestamps. That's expected: every calibration input and every piece of my own writing has punctuation density of 0.0435 or higher, so none of them reached the code I changed.

**Real output from the after run** (`run_eval.py::main` → `app.py::submit`, criterion 4, trial 1, abridged to the fields that matter):

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.775,
    "model_score": 0.7544,
    "style_score": 0.7955,
    "sent": "The importance of effective time management cannot be overstated in to"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7787,
    "model_score": 0.6999,
    "style_score": 0.8574,
    "sent": "Remote work has fundamentally transformed the modern workplace. Organi"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8394,
    "model_score": 0.9073,
    "style_score": 0.7714,
    "sent": "Regular physical activity offers numerous benefits for both physical a"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4236,
    "model_score": 0.3489,
    "style_score": 0.4983,
    "sent": "Time management matters more than people admit, especially now that wo"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.659,
    "model_score": 0.5813,
    "style_score": 0.7366,
    "sent": "Time management matters a lot in todays fast-paced work environment. P"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4082,
    "model_score": 0.3212,
    "style_score": 0.4952,
    "sent": "Communication at work matters more than people say it does — and I mea"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2572,
    "model_score": 0.4445,
    "style_score": 0.07,
    "sent": "I didn't sleep. Not properly, anyway — I lay there listening to the bo"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4936,
    "model_score": 0.5183,
    "style_score": 0.469,
    "sent": "Hey guys. I have admitted defeat for the gif pause challenge. Your rew"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4339,
    "model_score": 0.3925,
    "style_score": 0.4753,
    "sent": "We have a questionnaire of topics that you can talk about. However we "
  }
]
```

**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->

**It did what it was meant to do.** It also cost something real, and I'm counting it as a trade, not a clean win.

**What it fixed: all five false positives.**

- FP02–FP06 went from "high-confidence AI" (0.771–0.830) to "unsure" (0.600–0.715).
- Their style scores fell by 0.14–0.40. Their model scores didn't change, which shows the improvement came from exactly the measure I targeted.
- FP03, the ESL writer and my worst outcome from the before run, went from 0.828 to 0.600. FP06 and EV10 also landed on exactly 0.600. That's my disagreement cap: with style now low, the two signals split by more than 0.35, and the rule I wrote in Milestone 4 caught it. The two fixes worked together.
- **Overall, false positives went from 5 of 8 to 0 of 8.**

**What it cost: the last two evasions got through.**

- **EV10** (repeated stanza) has no punctuation at all, 0.000 per word. That's below the floor, so the change reads it as a plain human writer. Its style score fell from 0.737 to 0.337, it split from the model score (0.979), and the cap held it at 0.600 ("unsure").
- **EV04** (unusual words) sits at 0.0330, just under the floor. It dropped from 0.771 to 0.741, just below the 0.75 cutoff.
- **Evasion went from 8 of 10 broken to 10 of 10.** Now no AI text in the attack set reaches the AI label unless it's completely unedited.

**Why I'd still keep it.**

- The two errors don't cost the same. Five real writers lost an accusation, and two pieces of AI text lost a flag.
- The trade comes from the measure itself, not from a slip in the change. Sparse punctuation is honestly ambiguous: it's what plain human writers do, *and* it's what a stripped-down AI output looks like. The old measure settled that ambiguity against the human. The new one settles it in their favour.
- Nothing became an accusation: no row moved *into* the AI label.

**What it didn't fix.**

- **The 0.75 cutoff is still the narrow point (Problem 3).** FP05 sits at 0.715, only 0.035 below it, and the clean AI sample still scores just 0.775.
- **The fixed writers only got as far as "unsure", not "human".** They now read "We can't tell either way" instead of "patterns common in AI". It's better, but it isn't belief.
- **Criterion 4 is still missed, with identical numbers.** The change couldn't reach it, because my own informal writing was never below the floor. Its cause is the middle-collapse described in the diagnosis: signal one's floor plus the 0.35 human cutoff.
- **MF02 still returns a 500, and MF03/MF04 are still labelled "human".** Those are Problems 5 and 2, which I didn't touch.

**How I know it was this change and nothing else:**

- The prediction matched every row exactly.
- Only rows with punctuation below 0.04 changed.
- Model scores, status codes, rate-limit 429s and all five criteria were identical across the before and after runs.
- Before the after-runs, I restarted the service and confirmed it was serving the new code: FP03 returned style 0.4506, combined 0.600.


---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
