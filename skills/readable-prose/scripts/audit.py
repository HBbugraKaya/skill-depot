#!/usr/bin/env python3
"""Readability audit for English prose, based on Clark, Martin & Mahowald (2026),
"Why is AI-generated language so hard to understand?" (arXiv:2610.29162).

Flags sentences that use constructions linked to human processing difficulty:
  INANIMATE_SUBJECT  inanimate subject + verb that normally needs an animate one
  STACKED_NOUNS      3+ nouns in a compound chain
  REDUCED_ORC        object relative clause without "that/which/who"
  GARDEN_PATH        complement clause without "that" after an NP-taking verb
  LONG_DEPENDENCY    subject/object/aux far from its head, or a very long sentence
  DASH_INSERTION     clause interrupted by a pair of dashes
  DENOMINAL_VERB     ad-hoc noun-to-verb coinage
  RARE_WORD          low-frequency word (needs `wordfreq`)

Usage:  audit.py FILE|-  [--json] [--model en_core_web_sm]
Flags are candidates for review, not verdicts.
"""
import argparse, json, re, sys

ANIMATE_VERBS_STRONG = {
    "swallow", "eat", "bite", "chew", "choke", "hate", "love", "promise", "lie", "cheat",
    "betray", "pretend", "refuse", "complain", "beg", "scream", "shout", "whisper", "panic",
    "sneak", "bleed", "sulk", "forgive", "worry", "fear", "hope", "wish", "enjoy", "trust",
    "forget", "care", "laugh", "cry", "steal", "starve", "breathe", "sleep", "smile", "lurk",
    "insist", "demand", "crave", "hunger", "argue", "gossip", "brag", "mourn",
}
ANIMATE_VERBS_SOFT = {"want", "ask", "expect", "know", "think", "believe", "understand",
                      "decide", "remember", "feel", "like", "notice", "realize", "assume"}
ANIMATE_NOUNS = {
    "user", "developer", "team", "people", "person", "reader", "customer", "student", "engineer",
    "author", "maintainer", "reviewer", "owner", "admin", "administrator", "manager", "kid",
    "parent", "partner", "friend", "child", "man", "woman", "dog", "cat", "teacher", "doctor",
    "client", "colleague", "boss", "human", "player", "member", "staff", "writer", "speaker",
    "everyone", "someone", "anyone", "nobody", "somebody", "everybody", "anybody", "folk",
}
ANIMATE_PRONOUNS = {"i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
                    "who", "whom", "yourself", "myself", "ourselves", "themselves"}
NP_TAKING_VERBS = {"know", "find", "see", "notice", "believe", "realize", "realise", "confirm",
                   "check", "verify", "show", "discover", "remember", "forget", "hear", "learn",
                   "understand", "suspect", "accept", "admit", "read", "feel", "guess", "prove",
                   "establish", "determine", "report", "mention", "note", "observe"}
DENOMINAL_LIST = {
    "footnote", "calendar", "papercut", "bookend", "ladder", "bucket", "sunset", "greenlight",
    "productize", "operationalize", "workshop", "task", "action", "solution", "architect",
    "dialogue", "timebox", "bikeshed", "bandaid", "spreadsheet", "whiteboard", "roadmap",
    "guardrail", "moat", "fence", "wall", "paper", "napkin", "sandwich", "gift", "language",
    "socialize", "learning", "ideate", "incentivize", "message", "journal", "storyboard",
    "speedrun", "doomscroll", "hack", "gaslight", "ghost", "bubble", "funnel", "pipeline",
}
CORE_DEPS = {"nsubj", "nsubjpass", "dobj", "aux", "auxpass", "attr"}
RELATIVIZERS = {"that", "which", "who", "whom", "whose", "where", "when", "why"}


def clean_markdown(text):
    """Return a list of text blocks (paragraphs / list items) with code removed."""
    text = re.sub(r"```.*?```", "\n\n", text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", "CODE", text)
    text = re.sub(r"https?://\S+", "LINK", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(\*\*|__|\*|_)(\S[^*_]*?)\1", r"\2", text)
    blocks = []
    for raw in re.split(r"\n\s*\n|\n(?=\s*(?:[-*+]|\d+[.)]|#{1,6})\s)", text):
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)]|#{1,6}|>)\s*", "", raw.strip())
        line = re.sub(r"\s*\|\s*", " ", line)  # table pipes
        line = " ".join(line.split())
        if line:
            blocks.append(line)
    return blocks


def is_animate(tok):
    low = tok.lower_
    if low in ANIMATE_PRONOUNS:
        return True
    if tok.ent_type_ in ("PERSON", "NORP"):
        return True
    if tok.lemma_.lower() in ANIMATE_NOUNS:
        return True
    return False


def noun_chain(head):
    """Nouns in the compound chain ending at `head` (including head)."""
    out = [head]
    for c in head.children:
        if c.dep_ == "compound" and c.pos_ in ("NOUN", "PROPN"):
            out.extend(noun_chain(c))
    return out


def audit_sentence(sent, zipf):
    flags = []
    words = [t for t in sent if not t.is_punct and not t.is_space]
    widx = {t.i: k for k, t in enumerate(words)}

    for tok in sent:
        # 1. inanimate subject + animate verb
        if tok.dep_ == "nsubj" and tok.head.pos_ == "VERB":
            lemma = tok.head.lemma_.lower()
            strong = lemma in ANIMATE_VERBS_STRONG
            soft = lemma in ANIMATE_VERBS_SOFT
            if (strong or soft) and not is_animate(tok):
                flags.append(("INANIMATE_SUBJECT",
                              f"'{tok.text}' + '{tok.head.text}'" + ("" if strong else " (soft)"),
                              "Name the real mechanism instead of personifying the subject."))
        # 1b. parser fallback: animate verb mis-tagged as plural noun ("this case bites")
        if tok.tag_ == "NNS" and tok.dep_ == "ROOT":
            base = re.sub(r"(es|s)$", "", tok.lower_)
            if base in ANIMATE_VERBS_STRONG or tok.lower_[:-1] in ANIMATE_VERBS_STRONG:
                flags.append(("INANIMATE_SUBJECT", f"'{tok.text}' (possible)",
                              "Name the real mechanism instead of personifying the subject."))

        # 2. stacked nouns
        if tok.pos_ in ("NOUN", "PROPN") and tok.dep_ != "compound":
            chain = sorted(noun_chain(tok), key=lambda t: t.i)
            if len(chain) >= 3 and not all(t.pos_ == "PROPN" for t in chain):
                span = sent.doc[chain[0].i: chain[-1].i + 1].text
                flags.append(("STACKED_NOUNS", f"'{span}'",
                              "Unpack with a verb, 'of', or a possessive."))

        # 3. reduced object relative
        if tok.dep_ == "relcl" and tok.pos_ in ("VERB", "AUX"):
            kids = list(tok.children)
            has_subj = any(c.dep_ == "nsubj" for c in kids)
            has_obj = any(c.dep_ in ("dobj", "nsubjpass") for c in kids)
            has_rel = any(c.lower_ in RELATIVIZERS or c.tag_ in ("WDT", "WP", "WP$", "WRB")
                          for c in tok.subtree)
            if has_subj and not has_obj and not has_rel:
                flags.append(("REDUCED_ORC", f"'{tok.head.text} … {tok.text}'",
                              "Add 'that/which', or rewrite as a main clause."))

        # 4. garden-path complement clause
        if tok.dep_ == "ccomp" and tok.i > tok.head.i and \
           tok.head.lemma_.lower() in NP_TAKING_VERBS:
            kids = list(tok.children)
            has_mark = any(c.dep_ == "mark" for c in kids)
            subj = [c for c in kids if c.dep_ in ("nsubj", "nsubjpass")]
            if not has_mark and subj and subj[0].pos_ in ("NOUN", "PROPN") \
               and subj[0].i == min(t.i for t in tok.subtree):
                flags.append(("GARDEN_PATH", f"'{tok.head.text} {subj[0].text} …'",
                              "Add 'that' after the verb."))
            elif not has_mark and subj and subj[0].pos_ in ("NOUN", "PROPN"):
                first = min(t.i for t in tok.subtree)
                if sent.doc[first].pos_ in ("DET", "ADJ", "NOUN", "PROPN", "NUM"):
                    flags.append(("GARDEN_PATH", f"'{tok.head.text} {sent.doc[first].text} …'",
                                  "Add 'that' after the verb."))

        # 5. long core dependency
        if tok.dep_ in CORE_DEPS and tok.i in widx and tok.head.i in widx:
            d = abs(widx[tok.i] - widx[tok.head.i])
            if d >= 8:
                flags.append(("LONG_DEPENDENCY",
                              f"{tok.dep_} '{tok.text}' is {d} words from '{tok.head.text}'",
                              "Move the head closer: shorten the subject, move lists/insertions to the end."))

        # 6. denominal verb
        if tok.pos_ == "VERB" and tok.lemma_.lower() in DENOMINAL_LIST:
            flags.append(("DENOMINAL_VERB", f"'{tok.text}'",
                          "Use a conventional verb phrase (e.g. 'put in a footnote')."))

        # 7. rare word
        if zipf and tok.is_alpha and len(tok.text) > 3 and tok.pos_ != "PROPN" \
           and tok.text not in ("CODE", "LINK") and not tok.text.isupper():
            z = max(zipf(tok.lower_, "en"), zipf(tok.lemma_.lower(), "en"))
            if z < 2.0:
                flags.append(("RARE_WORD", f"'{tok.text}' (zipf {z:.1f})",
                              "Prefer a common word unless this is the precise technical term."))

    # 3b. surface fallback for reduced object relatives: NOUN + (DET|PRON) ... finite verb, no object
    toks = list(sent)
    subj_pron = {"i", "we", "you", "they", "he", "she", "it"}
    for k, t in enumerate(toks[:-2]):
        if t.pos_ not in ("NOUN", "PROPN") or t.dep_ == "compound":
            continue
        nxt = toks[k + 1]
        if not ((nxt.pos_ == "DET" and nxt.lower_ not in ("that", "which")) or nxt.lower_ in subj_pron):
            continue
        for j in range(k + 2, min(k + 6, len(toks))):
            v = toks[j]
            after = toks[j + 1] if j + 1 < len(toks) else None
            verbish = v.tag_ in ("VBD", "VBZ", "VBP", "VBN") or \
                      (v.tag_ == "NNS" and after is not None and after.pos_ in ("AUX", "VERB"))
            if verbish:
                if after is None or after.pos_ not in ("DET", "NOUN", "PROPN", "PRON", "NUM"):
                    if not any(f[0] == "REDUCED_ORC" for f in flags):
                        flags.append(("REDUCED_ORC", f"'{t.text} {nxt.text} … {v.text}'",
                                      "Add 'that/which', or rewrite as a main clause."))
                break
            if v.pos_ not in ("ADJ", "NOUN", "PROPN", "ADV"):
                break

    if len(words) > 30:
        flags.append(("LONG_DEPENDENCY", f"sentence has {len(words)} words",
                      "Split into two or three sentences."))
    if sent.text.count("—") + sent.text.count(" – ") + sent.text.count(" -- ") >= 2:
        flags.append(("DASH_INSERTION", "paired dashes interrupt the clause",
                      "Move the inserted material to the end or to its own sentence."))

    # dedupe
    seen, out = set(), []
    for f in flags:
        if f[:2] not in seen:
            seen.add(f[:2]); out.append(f)
    return out, len(words)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="text/markdown file, or - for stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--model", default="en_core_web_sm")
    args = ap.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    if re.search(r"[ğışĞİŞ]", text) and len(re.findall(r"[ğışçöüĞİŞÇÖÜ]", text)) > len(text) / 200:
        print("Warning: text looks Turkish; these checks are English-only. "
              "Use the manual Turkish checklist in SKILL.md.", file=sys.stderr)

    try:
        import spacy
        nlp = spacy.load(args.model)
    except Exception as e:
        sys.exit(f"Could not load spaCy model '{args.model}': {e}\n"
                 "Install: pip install spacy wordfreq && python3 -m spacy download en_core_web_sm")
    try:
        from wordfreq import zipf_frequency as zipf
    except Exception:
        zipf = None

    results, n_sent, n_words, counts = [], 0, 0, {}
    for block in clean_markdown(text):
        for sent in nlp(block).sents:
            if not any(t.is_alpha for t in sent):
                continue
            n_sent += 1
            flags, nw = audit_sentence(sent, zipf)
            n_words += nw
            for f in flags:
                counts[f[0]] = counts.get(f[0], 0) + 1
            if flags:
                results.append({"n": n_sent, "sentence": sent.text.strip(),
                                "flags": [{"type": a, "detail": b, "fix": c} for a, b, c in flags]})

    summary = {"sentences": n_sent, "words": n_words,
               "flagged_sentences": len(results),
               "per_100_sentences": {k: round(100 * v / max(n_sent, 1), 1)
                                     for k, v in sorted(counts.items())},
               "rare_word_check": zipf is not None}
    if args.json:
        print(json.dumps({"summary": summary, "sentences": results}, ensure_ascii=False, indent=2))
        return
    print(f"{n_sent} sentences, {n_words} words, {len(results)} flagged")
    for k, v in summary["per_100_sentences"].items():
        print(f"  {k:<18} {v:>5} per 100 sentences")
    if zipf is None:
        print("  (RARE_WORD skipped: pip install wordfreq)")
    print("Note: unusual word pairings and vivid metaphors need a manual check.\n")
    for r in results:
        print(f"[S{r['n']}] {r['sentence']}")
        for f in r["flags"]:
            print(f"   - {f['type']}: {f['detail']}  → {f['fix']}")
        print()


if __name__ == "__main__":
    main()
