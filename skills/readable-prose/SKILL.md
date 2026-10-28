---
name: readable-prose
description: >-
  Rewrite or audit a specific text so people can read it on the first pass, countering the dense
  "LLM dialect" described in Clark, Martin & Mahowald (2026, arXiv:2610.29162): personified code,
  stacked nouns, dropped "that", long subject-verb gaps, coined verbs, rare word pairings.
  Use when the user asks to simplify, clarify or de-AI a text or the previous reply, or says it
  is hard to read or too dense. Turkish: "bunu sadelestir", "anlasilir yaz".
disable-model-invocation: true
---

# Readable Prose

Use on a specific text: the previous reply, a summary, a PR description, or a draft the user
pastes. Rewrite it with the guidance below and return the rewritten version. If the user asked
only for a check, list the problem sentences with a suggested fix for each.

## Why this skill exists

Human language is shaped by a pressure for *successful communication*: readers have a lossy,
word-by-word working memory, so writers keep related words close, spell out optional signpost
words when the next part is unpredictable, and use familiar word combinations.

Recent models are post-trained heavily on math, code and agentic tasks where the reward is
"right answer, fewer tokens". The paper shows this pushes output toward the **shortest member of
every syntactic alternation**, even where a human writer would pick the longer, clearer one.
In a fine-tuning experiment, a small length penalty alone made a model drop optional words
almost categorically, and the habit spread to constructions it was never trained on.

The result is text that is grammatical but costly to process. Nine frontier models overused
these patterns versus human text, and the effect was **strongest in long chat and coding
sessions**, weaker in single-shot essays.

So the goal is not "write more" or "write less". It is: **keep the content, make the syntax easy.**
Keep every substantive point you would otherwise make (caveats, the practical tip, the "what to
check next"). Cut only repetition and filler. Do not cut the small words and structure that let a
reader parse a sentence without backtracking. A shorter answer that drops useful content is a
worse answer, even if each sentence is easier to read.

## The seven patterns to avoid

Each pattern saves a few tokens and costs the reader a re-read. For each: spot it, then
replace it with the plain version.

### 1. Inanimate subjects doing human things

Code, data or abstractions "swallow", "bite", "promise", "hate", "lie", "forget", "want",
"complain", "eat into". Readers use animacy as a parsing cue, so the mismatch forces a
reanalysis, and the metaphor hides what actually happens.

Fix: name the real mechanism.

- ✗ The cache swallows the error and the retry loop never finds out.
- ✓ The cache catches the error without logging it, so the retry loop never runs.
- ✗ This edge case bites when the list is empty.
- ✓ This edge case causes a crash when the list is empty.

Conventional technical idioms are fine ("the test expects 3", "the parser ignores whitespace").
Flag the vivid ones.

### 2. Stacked nouns (three or more in a row)

"user session token refresh logic". Each extra noun adds a bracketing choice the reader must
resolve: is it a refresh of the token, or a token of the refresh?

Fix: unpack with a verb, "of", or a possessive.

- ✗ the dotfile backup path handling fix
- ✓ the fix for how backup paths of dotfiles are handled
- ✓ (better) the fix for backing up dotfiles by absolute path

Established terms stay ("unit test", "pull request", "garbage collection").

### 3. Dropped signpost words

Keep optional words that announce structure, above all "that": after a noun ("the bug that…"),
after a verb ("found that…"), and after adjectives and "so" ("sure that…", "so that…"). In the
paper this is the habit that both Claude and GPT models showed most strongly, and the one that a
length penalty switched on fastest. Also keep "which/who" in relative clauses.

- ✗ The bug the patch fixed was in the parser.
- ✓ The bug that the patch fixed was in the parser.
- ✓ (better) The patch fixed a bug in the parser.

Object relatives without a relativizer ("the value the function returns") are the paper's
clearest signal. Add the "that", or turn the clause into a main clause.

### 4. Garden-path complement clauses

After verbs that can take a direct object (know, find, see, notice, believe, realize, confirm,
check, show), a missing "that" makes the reader first read the noun as the object.

- ✗ I found the config file was missing a key.
- ✓ I found that the config file was missing a key.

### 5. Long dependencies

The reader holds a subject in memory until its verb arrives. Every word in between costs effort.
Watch for: long subjects, long lists between a verb and its object, dash-insertions in the middle
of a clause, and relative clauses stacked inside relative clauses.

- ✗ All five expression shapes — attribute access, subscripts, calls, nested calls and string literals — now render correctly.
- ✓ All five expression shapes now render correctly: attribute access, subscripts, calls, nested calls and string literals.

Rules of thumb: put the subject and verb in the first ~8 words; move lists to the end;
split sentences over ~25 words; one em-dash insertion per paragraph at most.

### 6. Ad-hoc noun-to-verb coinages

"footnote it", "calendar it", "papercut users", "ladder up". Readers can decode them, but the
category switch triggers re-parsing. Conventional ones ("email", "log", "cache", "commit") are fine.

- ✗ We should footnote that caveat.
- ✓ We should mention that caveat in a footnote.

### 7. Rare words and unusual pairings

Low-frequency vocabulary and word pairs that rarely occur together ("reader-patience budget",
"gear trap", "legitimately protected") raise surprisal, which slows reading.

Fix: use the common word and the common collocation. If you coined a phrase, replace it with
its plain meaning. Keep a precise rare term only when it is the correct technical term, and
define it once.

## Workflow

1. **Draft** normally, focusing on content.
2. **Audit.** For English text longer than a short paragraph, run the checker:
   ```bash
   python3 <skill-dir>/scripts/audit.py draft.md          # human-readable report
   python3 <skill-dir>/scripts/audit.py draft.md --json   # machine-readable
   echo "some text" | python3 <skill-dir>/scripts/audit.py -
   ```
   It needs `spacy` + `en_core_web_sm` (and optionally `wordfreq`); install with
   `pip install spacy wordfreq && python3 -m spacy download en_core_web_sm`.
   If it can't run, go through the seven patterns by hand. The script cannot detect unusual
   word *pairings* (pattern 7) or judge metaphors, so always do a quick manual pass too.
3. **Revise only the flagged sentences.** Don't rewrite clean prose. The checker gives
   candidates, not verdicts: skip a flag when the plain version would be worse.
4. **Check meaning.** The rewrite must say exactly what the original said. Clearer, not vaguer.

In long sessions (many turns, agentic coding), re-apply the audit to your summaries:
this is where the paper found the drift is strongest.

## Don't over-correct

- Don't pad, and don't trim content either. Shorter sentences, same ideas. Removing a filler sentence is still good; removing a useful point is not.
- Don't strip all metaphor; strip the ones that obscure the mechanism.
- Don't expand established jargon your reader knows. Match the audience.
- Code identifiers, file paths and quoted output stay exactly as they are.
- Bullet lists are still fine for scannable content; each bullet should still parse easily.

## Turkish output (Türkçe metin)

Same principle; the patterns surface differently. The script is English-only, so check by hand:

1. **Cansız özne + insan fiili:** "Bu fonksiyon hatayı yutuyor" → "Bu fonksiyon hatayı yakalıyor ama loglamıyor."
2. **Uzun isim tamlaması zinciri:** "kullanıcı oturum anahtarı yenileme mantığı" → "kullanıcının oturum anahtarını yenileyen kod".
3. **Uzun sıfat-fiil öbeği (en büyük risk):** Türkçede niteleyici öbek ismin önüne gelir; uzadıkça okur ismi beklerken her şeyi aklında tutar.
   "Geçen sürümde boş liste geldiğinde çöken ve loglara hiçbir şey yazmayan servis düzeltildi." →
   "Servis düzeltildi. Geçen sürümde boş liste gelince çöküyor ve loga hiçbir şey yazmıyordu."
4. **Fiil cümle sonunda:** Türkçe SOV olduğu için uzun cümlede yüklem çok geç gelir. Cümleleri ~20 kelimenin altında tut.
5. **Gereksiz İngilizce türetme:** "bunu ship'leyelim", "footnote'layalım" → okura göre Türkçesini kullan.
6. **Nadir kelime / alışılmadık eşleşme:** "bütçe yiyen cümle" gibi uydurma imgeler yerine düz anlamı yaz.

## Source

Clark, T. H., Martin, M. B., & Mahowald, K. (2026). *Why is AI-generated language so hard to
understand?* arXiv:2610.29162, https://arxiv.org/abs/2610.29162 (licensed CC BY 4.0).

A copy of the paper is in `references/clark-martin-mahowald-2026-arxiv-2610.29162.pdf`.
Useful pages when refining this skill:

- Section 3.1: definitions and examples of the six features measured (Table 2 has real model sentences).
- Figures 4–6: which models over-use which feature.
- Figure 7 and Table 3: the length-penalty experiment and the alternations used.

Features studied: n-gram rarity, dependency length, object relative clauses (with/without
relativizer), stacked noun compounds, denominal verbs, inanimate subjects with animate verbs.
