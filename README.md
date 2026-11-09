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

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



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
