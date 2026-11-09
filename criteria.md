# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1.

<!-- Your criterion. It must name a number. -->
Of 10 pieces I wrote myself, at most 1 is labeled high-confidence AI in any of the 3 trials.

**Why this target:**
Multiple real pieces considered AI will unjustly ruined a person's reputation.


---

## 2.

<!-- Your criterion. -->
The average combined score of clearly-AI samples is at least 0.30 higher than the average for clearly-human samples, in every trial.


**Why this target:**
Users with real posts should given way more credibility compared to AI posts.


---

## 3.

<!-- Your criterion. -->
10 of 10 appeals on real content_ids return 200 with status: "under_review" and add an appeal entry to the log. An unknown id returns 404 every time.


**Why this target:**
Unverified ids will give the site lack of credibility to users.


---

## 4.

<!-- Your criterion. -->
Each of the 3 labels (human, borderline, AI) is produced at least once from a calibration set of 9 inputs in all 3 trials. Also, at most 1 of the 3 clearly-human inputs lands in "unsure" in any trial.


**Why this target:**
A label nobody can reach is a promise the site can't keep. If "high-confidence human" never shows up, every honest writer gets doubt at best. The second part stops me from passing by making "unsure" so wide that it swallows everyone: a wrong "unsure" is milder than a wrong "AI" but still makes a real writer second-guess their own work.


---

## 5.

<!-- Your criterion. -->
Missing text, text: "", text: null and a 100,000-character text each return a 400 with {error, message}, never a 500, and each one is logged as a rejection.


**Why this target:**
A crash tells an attacker where the edges are and tells a real user nothing about what to fix. Bad input should get a clear message, not a stack trace. Rejecting enormous text also keeps one request from tying up the model for everyone else. Logging the rejections means probing attempts can still be seen afterwards.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
