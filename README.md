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
| Punctuation density (`, ; : ! ? ( ) " —` per word, full stops excluded) | 0.12 | 0.02 | 0.4 |
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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



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
