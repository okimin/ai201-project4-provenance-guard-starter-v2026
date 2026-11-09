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

**The rule:**

**The numbers:**

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



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
  -d '{"text": "...", "creator_id": "..."}'
```

```json

```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

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
