"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

# Words per window for the moving-average type-token ratio.
TTR_WINDOW = 50

# Below this much text the shape means nothing, and style_signal returns 0.5.
MIN_WORDS = 30
MIN_SENTENCES = 3

# How much each measure counts in style_signal. Spread and punctuation
# separated the calibration inputs cleanly; TTR is weighted lower because its
# direction runs against the usual expectation and rests on few examples.
WEIGHT_SPREAD = 0.4
WEIGHT_PUNCT = 0.4
WEIGHT_TTR = 0.2


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    # One sentence has no spread to measure. 0.0 reads as "no variation";
    # style_signal treats too-short text as neutral instead of trusting this.
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    toks = words(text)
    if not toks:
        return 0.0
    # Plain TTR falls as text gets longer, so length alone would look like a
    # signal. A moving-average TTR over a fixed window cancels most of that:
    # every window is the same length, so long and short texts compare fairly.
    window = TTR_WINDOW
    if len(toks) <= window:
        return round(len(set(toks)) / len(toks), 4)
    ratios = [
        len(set(toks[i:i + window])) / window
        for i in range(len(toks) - window + 1)
    ]
    return round(statistics.mean(ratios), 4)


def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.
    """
    n_words = len(words(text))
    if n_words == 0:
        return 0.0
    # Full stops are left out on purpose: every writer uses them. What varies
    # between writers is commas, dashes, semicolons, colons, brackets, quotes,
    # question marks and exclamations.
    marks = re.findall(r"[,;:!?()\"\u2014\u2013\u201c\u201d]|--| - ", text)
    return round(len(marks) / n_words, 4)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.
    """
    n_words = len(words(text))
    n_sents = len(sentences(text))
    # Too little text to measure shape. Say "no opinion" rather than guess.
    if n_words < MIN_WORDS or n_sents < MIN_SENTENCES:
        return 0.5

    # Each measure becomes an "AI-ness" score from 0 to 1 by placing it
    # between two anchors taken from the calibration inputs (see README).
    #
    #   spread  low  = AI-like   (sentences march in step)
    #   punct   low  = AI-like   (few commas, dashes, semicolons, quotes)
    #   ttr     HIGH = AI-like   — the opposite of the usual hint. In every
    #           calibration input the AI text used the most varied vocabulary
    #           and plain human writing the least. Flipping it also protects
    #           plain writers, who are the people this signal wrongly accuses.
    spread_ai = _scale(sentence_length_spread(text), human=0.90, ai=0.30)
    punct_ai = _scale(punctuation_density(text), human=0.12, ai=0.02)
    ttr_ai = _scale(type_token_ratio(text), human=0.75, ai=0.95)

    score = (
        WEIGHT_SPREAD * spread_ai
        + WEIGHT_PUNCT * punct_ai
        + WEIGHT_TTR * ttr_ai
    )
    return round(score, 4)


def _scale(value: float, human: float, ai: float) -> float:
    """
    Map a raw measure onto 0–1 AI-ness. `human` is the value that scores 0.0,
    `ai` the value that scores 1.0, linear between, clipped outside. Works
    whichever way round the anchors are.
    """
    t = (value - human) / (ai - human)
    return min(max(t, 0.0), 1.0)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
