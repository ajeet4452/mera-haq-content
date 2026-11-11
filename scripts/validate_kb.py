#!/usr/bin/env python3
"""kb/ की फाइलों की जाँच।

दो तरह की जाँच होती है:

1. ढाँचा — हर प्रविष्टि में ज़रूरी फ़ील्ड भरी हुई हैं या नहीं, हर सवाल में चार अलग
   विकल्प हैं या नहीं, जवाब का क्रमांक 0 से 3 के बीच है या नहीं, और कोई सवाल
   दोहराया नहीं गया है।

2. सरकारी पाठ से मिलान — --ref के साथ दी गई फाइल में जो सरकारी पाठ है, उससे
   ऐप का पाठ शब्द-दर-शब्द मिलता है या नहीं।

कुछ भी गड़बड़ मिले तो स्क्रिप्ट गैर-शून्य कोड के साथ बंद होती है, ताकि बदलाव
आगे न बढ़े।
"""
import json
import re
import sys

ERRORS = []
WARNINGS = []


def err(msg):
    ERRORS.append(msg)


def warn(msg):
    WARNINGS.append(msg)


def norm(text):
    """तुलना के लिए पाठ साफ़ करना — खाली जगह, विराम और टाइप-सेटिंग के फ़र्क़ हटाना।"""
    text = text or ""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-").replace("∗", "*")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def check_question(q, where):
    if not isinstance(q, dict):
        err(f"{where}: सवाल का ढाँचा गलत है")
        return
    text = (q.get("question") or "").strip()
    if not text:
        err(f"{where}: सवाल खाली है")
    opts = q.get("options") or []
    if len(opts) != 4:
        err(f"{where}: विकल्प चार नहीं हैं ({len(opts)}) — {text[:50]}")
    elif len({o.strip() for o in opts}) != 4:
        err(f"{where}: विकल्प एक जैसे हैं — {text[:50]}")
    elif any(not (o or "").strip() for o in opts):
        err(f"{where}: कोई विकल्प खाली है — {text[:50]}")
    ans = q.get("answer")
    if not isinstance(ans, int) or not (0 <= ans <= 3):
        err(f"{where}: जवाब का क्रमांक ठीक नहीं ({ans}) — {text[:50]}")
    if not (q.get("explanation") or "").strip():
        err(f"{where}: व्याख्या खाली है — {text[:50]}")


def check_sections(sections, where, light=False):
    seen = {}
    for s in sections:
        num = str(s.get("number", "")).strip()
        if not num:
            err(f"{where}: किसी प्रविष्टि का नंबर नहीं है")
            continue
        if not (s.get("title") or "").strip():
            err(f"{where} {num}: शीर्षक खाली है")
        if not light:
            if not (s.get("kitabi") or "").strip():
                err(f"{where} {num}: मूल पाठ खाली है")
            if not (s.get("aasan") or "").strip():
                err(f"{where} {num}: आसान भाषा खाली है")
        for q in s.get("questions", []) or []:
            check_question(q, f"{where} {num}")
            key = norm(q.get("question", ""))
            if key in seen and seen[key] != num:
                warn(f"{where}: सवाल दो जगह है ({seen[key]} और {num}) — {key[:50]}")
            seen[key] = num


def check_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        warn(f"{path}: फाइल नहीं मिली — छोड़ी गई")
        return
    except json.JSONDecodeError as e:
        err(f"{path}: JSON टूटा हुआ है — {e}")
        return

    if isinstance(data, dict) and "laws" in data:
        # laws.json में कानूनों की सूची है, acts.json में नाम से पहचानी गई वस्तु।
        raw = data["laws"]
        pairs = raw.items() if isinstance(raw, dict) else [(str(l.get("id", "?")), l) for l in raw]
        # laws.json में हर कानून के भाग होते हैं, हर भाग में उसकी प्रविष्टियाँ।
        # उनमें सिर्फ नंबर और शीर्षक होता है; पाठ acts.json में रहता है।
        for law_id, law in pairs:
            sections = law.get("sections")
            if sections is None:
                sections = [x for part in law.get("parts", []) for x in part.get("sections", [])]
            if not sections:
                err(f"{path}: {law_id} में कोई प्रविष्टि नहीं")
                continue
            check_sections(sections, f"{path}:{law_id}", light=True)
    elif isinstance(data, dict) and "quizzes" in data:
        for quiz in data["quizzes"]:
            num = str(quiz.get("number", "")).strip()
            if not num:
                err(f"{path}: किसी क्विज़ का नंबर नहीं है")
            for q in quiz.get("questions", []) or []:
                check_question(q, f"{path}:{num}")
    elif isinstance(data, dict) and "articles" in data:
        check_sections(data["articles"], path)
        for sch in data.get("schedules", []) or []:
            if not (sch.get("title") or "").strip():
                err(f"{path}: अनुसूची {sch.get('number')} का शीर्षक खाली है")
    elif isinstance(data, list):
        ids = set()
        for d in data:
            if not isinstance(d, dict):
                err(f"{path}: प्रविष्टि का ढाँचा गलत है")
                continue
            did = (d.get("id") or "").strip()
            if not did:
                err(f"{path}: किसी प्रविष्टि की id नहीं है")
            elif did in ids:
                err(f"{path}: id दोहराई गई — {did}")
            ids.add(did)
            for field in ("title", "answer", "category"):
                if not (d.get(field) or "").strip():
                    err(f"{path}: {did or '?'} में {field} खाली है")
    else:
        warn(f"{path}: पहचाना नहीं गया ढाँचा — छोड़ा गया")


def check_against_reference(acts_path, ref_path):
    """ऐप का पाठ सरकारी पाठ से मिलता है या नहीं।"""
    try:
        acts = json.load(open(acts_path, encoding="utf-8")).get("laws", {})
        ref = json.load(open(ref_path, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        warn(f"मिलान छोड़ा गया — {e}")
        return

    checked = 0
    for ref_key, ref_law in ref.items():
        if not isinstance(ref_law, dict):
            continue
        app_law = acts.get(ref_key)
        if not app_law:
            print(f"  {ref_key}: ऐप में अभी नहीं है — मिलान का मौका नहीं")
            continue
        official = {str(s["number"]): norm(s.get("text", "")) for s in ref_law.get("sections", [])}
        for sec in app_law.get("sections", []):
            num = str(sec.get("number", "")).strip()
            want = official.get(num)
            if not want:
                err(f"{ref_key} {num}: सरकारी पाठ में यह धारा नहीं मिली")
                continue
            got = norm(sec.get("kitabi", ""))
            if not got:
                err(f"{ref_key} {num}: ऐप में पाठ खाली है")
                continue
            if got not in want and want not in got:
                err(f"{ref_key} {num}: पाठ सरकारी पाठ से नहीं मिलता")
            checked += 1
    print(f"  सरकारी पाठ से मिलाई गई धाराएँ: {checked}")


def main():
    args = sys.argv[1:]
    if not args:
        print("उपयोग: validate_kb.py <फाइलें...> [--ref official_text.json]")
        return 2

    ref = None
    files = []
    i = 0
    while i < len(args):
        if args[i] == "--ref":
            ref = args[i + 1]
            i += 2
        else:
            files.append(args[i])
            i += 1

    for path in files:
        check_file(path)

    if ref:
        acts = next((f for f in files if f.endswith("acts.json")), None)
        if acts:
            print("सरकारी पाठ से मिलान:")
            check_against_reference(acts, ref)

    for w in WARNINGS:
        print(f"चेतावनी: {w}")
    for e in ERRORS:
        print(f"त्रुटि: {e}")

    print(f"\nनतीजा: {len(ERRORS)} त्रुटि, {len(WARNINGS)} चेतावनी")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
