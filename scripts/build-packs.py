#!/usr/bin/env python3
"""Build word packs into packs/.

English answers come from common words (wordfreq) validated against the system
dictionary; guesses add dictionary words and common inflections. Other languages
use wordfreq alone and are marked beta until a native speaker reviews them.
Difficulty is computed by a simple solver. See WORD-PACK-SPEC.md for the format.

Usage: python3 scripts/build-packs.py   (needs: pip install wordfreq)
"""
import json, os, re, sys, statistics
from collections import Counter
from wordfreq import top_n_list, zipf_frequency

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'packs')
L = 5
EPOCH = '2026-10-21'

# ---------- word sources ----------
def dict_words(path):
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            return [w.strip() for w in f]
    except FileNotFoundError:
        return []

web2 = dict_words('/usr/share/dict/words')
WEB2 = set(w for w in web2 if w.islower() and w.isalpha())
FIRST_NAMES = set(w.lower() for w in dict_words('/usr/share/dict/propernames'))
PROPER = set(w.lower() for w in web2 if w[:1].isupper()) | FIRST_NAMES
# Place names and the like that are also common nouns stay as guesses (e.g. "china", "march").
PROPER -= WEB2
# First names are never answers, even when the dictionary also lists them lowercase ("benny", "maria").
NEVER_ANSWER = FIRST_NAMES | set("""norma rowan garth rufus bosch kerry roger twain emery aspen thine mamma hanna benny bobby maria hitler rufus""".split())

# Slurs and words nobody wants to see as "the answer was". Applied to both lists.
BLOCK_ALL = set("""nigga negro chink gooks spick spics kikes dykes faggy fagot bitch whore pussy cunts twats wanks cocks dicks shits turds nazis rapes raped rapey""".split())
# Fine as an accepted guess, never as an answer.
ANSWER_ONLY_BLOCK = set("""penis semen vulva anus boobs enema fetus feces urine vomit sperm nudes porno drugs heroin crack slave slaves hitler jihad bomb bombs""".split())
# Apostrophe-stripped and internet forms that frequency lists contain.
JUNK = set("""didnt thats youre wasnt arent hasnt hadnt whats heres youll theyd youve whove doesnt isnt wont cant shes dont gonna wanna gotta kinda sorta lotta thanx lmfao omfg https wwwww tumblr imgur pls plz ohhh ahhh hmmmm yeahh okayy lolol haha hahah hehe hehehe ummm uhhh ooooh sooo soooo soooo wooo yayyy""".split())
# Modern or everyday words the 1934 dictionary lacks.
MODERN = set("""pizza email emoji vegan robot pixel drone sushi ninja karma bagel latte mocha disco bingo condo intro retro promo combo nacho salsa pasta ramen kebab vodka pesto panda koala hippo rhino llama zebra tacos burger vinyl audio video radio laser sauna yoga mango kiwi tofu curry logo blog vlog wifi app apps admin bots memes meme emoji selfie photo motel hotel""".split())
MODERN = set(w for w in MODERN if len(w) == L)

def is_plural_or_inflection(w, base):
    """True if w looks like an inflected form of a word in base (plural -s/-es, past -ed, -ing)."""
    if w.endswith('s') and (w[:-1] in base or (w.endswith('es') and w[:-2] in base)):
        return True
    if w.endswith('ed') and (w[:-2] in base or w[:-1] in base or (len(w) > 3 and w[-3] == w[-4] and w[:-3] in base)):
        return True
    if w.endswith('ing') and (w[:-3] in base or w[:-3] + 'e' in base):
        return True
    return False

KEEP_INFLECTED = set("""tired fixed naked rated noted dated based added aimed armed cured faced famed fated jaded mixed moved paved posed ruled sized timed tried urged vexed wired bored dazed fried dried eased fazed hired lined mined owned paced paged piped raged razed sided toned tuned typed waved wiped zoned""".split())
KEEP_S = set("""teeth women chess glass grass dress press cross bless bliss gloss floss brass class mass moss boss loss toss fuss truss abyss amiss basis oasis bonus focus virus minus lotus nexus sinus opus ethos chaos civics""".split())
KEEP_S = set(w for w in KEEP_S if len(w) == L)

def build_english():
    freq = [w for w in top_n_list('en', 300000) if len(w) == L and w.isalpha() and w.islower()]
    base_vocab = WEB2 | MODERN
    answers, guesses = [], []
    for w in freq:
        z = zipf_frequency(w, 'en')
        if w in JUNK or w in BLOCK_ALL or w in PROPER: continue
        in_dict = w in base_vocab
        inflected = is_plural_or_inflection(w, WEB2)
        # Accepted guesses: dictionary words plus common inflections.
        if in_dict or (inflected and z >= 2.2):
            guesses.append(w)
        # Answers: common, in the dictionary, not an inflection, not crude.
        if in_dict and z >= 3.05 and w not in ANSWER_ONLY_BLOCK and w not in NEVER_ANSWER:
            if inflected and w not in KEEP_INFLECTED and w not in KEEP_S:
                continue
            if w.endswith('s') and w[:-1] in WEB2 and w not in KEEP_S:
                continue
            answers.append(w)
    # Fill the guess list with the rest of the dictionary (rare words are fine as guesses).
    seen = set(guesses)
    for w in sorted(WEB2):
        if len(w) == L and w not in seen and w not in BLOCK_ALL and w not in PROPER:
            guesses.append(w); seen.add(w)
    answers = answers[:2400]
    aset = set(answers)
    guesses = [w for w in guesses if w not in aset]
    return answers, guesses

def looks_like_noise(w):
    return bool(re.search(r'(.)\1\1', w)) or 'haha' in w or 'hehe' in w

def build_wordfreq_only(lang, english_guesses, min_zipf_answer=3.5, min_zipf_guess=2.6, max_answers=700):
    """Languages without a system dictionary: frequency only, with English collisions removed."""
    en = set(english_guesses)
    words = [w for w in top_n_list(lang, 200000) if len(w) == L and w.isalpha() and w.islower()]
    answers, guesses = [], []
    for w in words:
        z = zipf_frequency(w, lang)
        if w in en or w in PROPER or w in BLOCK_ALL or w in JUNK or looks_like_noise(w): continue
        ze = zipf_frequency(w, 'en')
        if ze >= z or ze >= 2.8: continue      # more English than local, or a name/brand seen in English text
        if z >= min_zipf_guess: guesses.append(w)
        if z >= min_zipf_answer and len(answers) < max_answers: answers.append(w)
    aset = set(answers)
    return answers, [w for w in guesses if w not in aset]

# ---------- difficulty solver ----------
def score(guess, answer):
    res = ['a'] * L; counts = Counter()
    for i in range(L):
        if guess[i] == answer[i]: res[i] = 'c'
        else: counts[answer[i]] += 1
    for i in range(L):
        if res[i] != 'c' and counts[guess[i]] > 0: res[i] = 'p'; counts[guess[i]] -= 1
    return ''.join(res)

def pick(cands):
    pos = [Counter() for _ in range(L)]
    for w in cands:
        for i, c in enumerate(w): pos[i][c] += 1
    best, bs = None, -1
    for w in cands:
        s = sum(pos[i][c] for i, c in enumerate(w)) * (1 + 0.15 * (len(set(w)) - 3))
        if s > bs: best, bs = w, s
    return best

def solve(answer, answers, opener):
    cands = answers; guess = opener
    for n in range(1, 7):
        if guess == answer: return n
        fb = score(guess, answer)
        cands = [w for w in cands if score(guess, w) == fb]
        if not cands: return 6
        guess = pick(cands)
    return 6.5

def difficulty(answers, openers):
    out = {}
    for a in answers:
        out[a] = round(max(2.6, statistics.mean(solve(a, answers, o) for o in openers)), 2)
    return out

def best_openers(answers, k=3):
    pos = [Counter() for _ in range(L)]
    for w in answers:
        for i, c in enumerate(w): pos[i][c] += 1
    ranked = sorted(answers, key=lambda w: -sum(pos[i][c] for i, c in enumerate(w)) * (len(set(w)) == L))
    return ranked[:k]

def write(pack):
    path = os.path.join(OUT, f"{pack['id']}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pack, f, ensure_ascii=False, separators=(',', ':'))
    print(f"{pack['id']}: {len(pack['answers'].split())} answers, {len(pack['guesses'].split())} guesses, {os.path.getsize(path)//1024} KB")

def main():
    os.makedirs(OUT, exist_ok=True)
    en_a, en_g = build_english()
    openers = best_openers(en_a)
    print('en openers', openers)
    en = dict(id='en', name='English', language='en', version=2, wordLength=L,
              alphabet='abcdefghijklmnopqrstuvwxyz', keyboard=['qwertyuiop', 'asdfghjkl', 'zxcvbnm'],
              epoch=EPOCH, answers=' '.join(en_a), guesses=' '.join(en_g), difficulty=difficulty(en_a, openers))
    write(en)
    manifest = [dict(id='en', name='English', language='en', file='packs/en.json')]
    for lang, name in [('ms', 'Bahasa Melayu'), ('id', 'Bahasa Indonesia'), ('fil', 'Filipino')]:
        a, g = build_wordfreq_only(lang, en_g + en_a)
        if len(a) < 400: print(f'{lang}: only {len(a)} answers, skipped'); continue
        ops = best_openers(a)
        pack = dict(id=lang, name=name, language=lang, version=1, wordLength=L, beta=True,
                    alphabet='abcdefghijklmnopqrstuvwxyz', keyboard=['qwertyuiop', 'asdfghjkl', 'zxcvbnm'],
                    epoch=EPOCH, answers=' '.join(a), guesses=' '.join(g), difficulty=difficulty(a, ops))
        write(pack)
        manifest.append(dict(id=lang, name=name, language=lang, file=f'packs/{lang}.json', beta=True))
    with open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('manifest', [m['id'] for m in manifest])

if __name__ == '__main__':
    main()
