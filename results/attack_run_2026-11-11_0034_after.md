# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-11 00:34
- Auto-marked BROKE (5xx, crash, no response): **1**
- Left for you to judge: **55**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `c_41ded8b95c47` | unsure | 0.518 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `c_a5cf2b6d6d50` | unsure | 0.518 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `c_aaaacd2a9ec9` | unsure | 0.691 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `c_c8f5aa21d65f` | unsure | 0.741 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `c_a21316aded17` | unsure | 0.408 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `c_2b9d91eba057` | unsure | 0.466 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `c_51ec4352ef3a` | unsure | 0.543 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `c_d11c0f33a56c` | unsure | 0.373 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `c_1f2221e893fd` | unsure | 0.738 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `c_97df059f7114` | unsure | 0.600 | BROKE |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `c_e5af08bcfc88` | unsure | 0.562 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `c_b8ab7528a4e8` | unsure | 0.632 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `c_b6c61a2039e0` | unsure | 0.600 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | `c_85f1d427adb2` | unsure | 0.689 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | `c_d80cb75f5bbe` | unsure | 0.715 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | `c_934287d84358` | unsure | 0.600 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `c_9f4763b214cb` | unsure | 0.600 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | `c_8f00b4b99466` | unsure | 0.411 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `c_4f5360574aac` | unsure | 0.402 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `c_b8c86e77a246` | unsure | 0.436 | HELD |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `c_33343933aea7` | unsure | 0.701 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `c_c020755ff666` | unsure | 0.556 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `c_fd8f097ffccc` | unsure | 0.570 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `c_2f803a8f1102` | unsure | 0.533 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 500 | `—` | — | — | BROKE |
| MF03 | malformed | text is control characters | 200 | `c_69696d23f37d` | human | 0.250 | BROKE |
| MF04 | malformed | text is only punctuation | 200 | `c_a31cfcd2fd47` | human | 0.256 | BROKE |
| MF05 | malformed | text is a very long single word | 200 | `c_559b1d4b09c1` | unsure | 0.600 | HELD |
| MF06 | malformed | text is emoji only | 200 | `c_a716acc9029a` | unsure | 0.600 | HELD |
| MF07 | malformed | text is right-to-left script | 200 | `c_27b68908c851` | unsure | 0.600 | HELD |
| MF08 | malformed | text is 60,000 characters | 400 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 200 | `c_68232a23c222` | unsure | 0.370 | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 200 | `c_aa43c5902277` | human | 0.275 | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_7d2b0c1cd9b7` | human | 0.264 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_fe919766060e` | human | 0.264 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_96a306e09ab9` | human | 0.264 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_ebcdb8769973` | human | 0.264 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_b64ddee5732d` | human | 0.264 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 1 | 19 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "c_41ded8b95c47",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.5177,
  "model_score": 0.1635,
  "style_score": 0.8718,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "c_a5cf2b6d6d50",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.5182,
  "model_score": 0.5943,
  "style_score": 0.4422,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "c_aaaacd2a9ec9",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6907,
  "model_score": 0.6662,
  "style_score": 0.7153,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "c_c8f5aa21d65f",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.7406,
  "model_score": 0.6114,
  "style_score": 0.8697,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "c_a21316aded17",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.4082,
  "model_score": 0.3212,
  "style_score": 0.4952,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "c_2b9d91eba057",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4661,
  "model_score": 0.5727,
  "style_score": 0.3596,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "c_51ec4352ef3a",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5431,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "c_d11c0f33a56c",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.3726,
  "model_score": 0.2452,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "c_1f2221e893fd",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.7382,
  "model_score": 0.7042,
  "style_score": 0.7722,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "c_97df059f7114",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9792,
  "style_score": 0.3374,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "c_e5af08bcfc88",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.562,
  "model_score": 0.6175,
  "style_score": 0.5065,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "c_b8ab7528a4e8",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.632,
  "model_score": 0.7387,
  "style_score": 0.5252,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "c_b6c61a2039e0",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.8051,
  "style_score": 0.4506,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "c_85f1d427adb2",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.6885,
  "model_score": 0.8329,
  "style_score": 0.5442,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "c_d80cb75f5bbe",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.7147,
  "model_score": 0.8005,
  "style_score": 0.6288,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "c_934287d84358",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.8814,
  "style_score": 0.3847,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "c_9f4763b214cb",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.8816,
  "style_score": 0.3839,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "c_8f00b4b99466",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.4112,
  "model_score": 0.3223,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "c_4f5360574aac",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.402,
  "model_score": 0.4625,
  "style_score": 0.3415,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "c_b8c86e77a246",
  "creator_id": "attacker_PI02",
  "guess": "unsure",
  "confidence": 0.4362,
  "model_score": 0.2044,
  "style_score": 0.6679,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "c_33343933aea7",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.7005,
  "model_score": 0.5943,
  "style_score": 0.8066,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "c_c020755ff666",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5558,
  "model_score": 0.4998,
  "style_score": 0.6119,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "c_fd8f097ffccc",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.57,
  "model_score": 0.6401,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "c_2f803a8f1102",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5328,
  "model_score": 0.5583,
  "style_score": 0.5072,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 500,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": "response wasn't JSON: <!doctype html>\n<html lang=en>\n  <head>\n    <title>ValueError: Text is too short to score \u2014 a few sentences at least.\n // Werkzeug Debugger</title>\n    <link rel=\"stylesheet\" href=\"?__debugger__=yes&a",
  "verdict": "BROKE"
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "c_69696d23f37d",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.25,
  "model_score": 0.0,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "c_a31cfcd2fd47",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.2556,
  "model_score": 0.0112,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "c_559b1d4b09c1",
  "creator_id": "attacker_MF05",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9976,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "c_a716acc9029a",
  "creator_id": "attacker_MF06",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "c_27b68908c851",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 200,
  "content_id": "c_68232a23c222",
  "creator_id": null,
  "guess": "unsure",
  "confidence": 0.3698,
  "model_score": 0.2395,
  "style_score": 0.5,
  "label": "We can't tell either way. This piece has some patterns that often show up in AI-generated text and some that are typical of people, and plenty of people simply write this way. We're not saying it was made with AI.",
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 200,
  "content_id": "c_aa43c5902277",
  "creator_id": {
    "id": "x"
  },
  "guess": "human",
  "confidence": 0.2746,
  "model_score": 0.0492,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "c_7d2b0c1cd9b7",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2643,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "c_fe919766060e",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2643,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "c_96a306e09ab9",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2643,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "c_ebcdb8769973",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2643,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "c_b64ddee5732d",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2643,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person. Our checks didn't find the patterns we usually see in AI-generated text.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
