"""Q5_v1.py

Questionnaire generator (Objective 5).

This module reads a requirements JSON file (`questionaire_requirements.json` by
default), selects matching questions from a question bank (default
`convert_data.json`), ranks them using a lightweight approach (TF-IDF for
English when available, simple keyword/tag scoring for Chinese or as a
fallback), and writes two outputs:

- `output_questionaire.json`: structured JSON with selected questions
- `output_questionaire.txt`: human-readable, grouped by category

Provenance / copied-from-Part4 notes:
- The small CJK-based language detection heuristic used by `is_chinese` is
    derived from the `detect_lang` helper used in `Part4.py` (see
    `load_and_process_data` / `detect_lang`).
- The `topic_keywords_en` and `topic_keywords_zh` maps (used in the
    interactive inference block) are copied/derived from the
    `topic_keywords` definitions in `Part4.py` (see `analyze_dataset_content`).
- The approach of preferring TF-IDF for English and using simpler
    keyword/tag scoring as a fallback follows the design in `Part4.py`
    (see `generate_survey`).
"""

import json
import os
import re
from typing import List, Dict, Any
import sys

from survey_database import SurveyDatabase


def is_chinese(text: str) -> bool:
    """Return True if the string contains any CJK Unified Ideographs.

    This is a light-weight heuristic used to choose between English and
    Chinese ranking strategies.
    (Derived from `detect_lang` in `Part4.py`.)
    """
    if not isinstance(text, str):
        return False
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def load_requirements(path: str) -> Dict[str, Any]:
    """Load the JSON requirements file and return a Python dict.

    The requirements file is expected to contain a top-level `requirements`
    object with fields such as `topic`, `language`, `categories`, and
    `question_count`.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tfidf_rank(query: str, docs: List[str]) -> List[float]:
    """Compute TF-IDF cosine similarity between query and each doc.

    Returns a list of similarity scores aligned with docs.
    If sklearn isn't available, raises ImportError and caller should fallback.
    This implementation follows the TF-IDF + cosine-similarity pattern used
    in `Part4.py`'s `generate_survey`.
    """
    # Import inside function to allow graceful fallback if sklearn is not
    # installed in the environment.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    vec = TfidfVectorizer(stop_words="english")
    # Fit on docs + query so that query and docs share the same features
    X = vec.fit_transform(docs + [query])
    doc_vectors = X[:-1]
    query_vector = X[-1]
    sims = linear_kernel(query_vector, doc_vectors).flatten()
    return sims.tolist()


def keyword_score(query: str, docs: List[str]) -> List[float]:
    """A simple fallback scorer that counts query occurrences in each doc.

    The returned scores are normalized to the [0,1] range when possible.
    """
    q = (query or "").lower().strip()
    scores: List[float] = []
    for d in docs:
        dlow = (d or "").lower()
        if not q:
            scores.append(0.0)
            continue
        # simple frequency of the full query token in the doc text
        count = dlow.count(q)
        scores.append(float(count))
    # normalize to [0,1]
    maxv = max(scores) if scores else 0.0
    if maxv > 0:
        scores = [s / maxv for s in scores]
    return scores


def generate_questionnaire(req_path: str = "questionaire_requirements.json", db_path: str = "convert_data.json") -> Dict[str, Any]:
    """Generate a questionnaire according to the requirements file.

    Steps performed (high-level):
    - Load and normalize requirements
    - Load question bank via `SurveyDatabase`
    - Filter bank by language / category / difficulty
    - Rank remaining candidates (TF-IDF or keyword/tag scoring)
    - Ensure requested categories are represented where possible
    - Fill remaining slots with top-scoring items
    - Write organized JSON and text outputs and return the output object

    Arguments:
        req_path: path to the requirements JSON
        db_path: path to the question bank JSON used by `SurveyDatabase`
    """

    req = load_requirements(req_path)
    body = req.get("requirements", {})
    # Number of questions requested (default 5)
    qcount = int(body.get("question_count", 5))
    # Normalize categories to lowercase for matching
    categories = [c.lower() for c in body.get("categories", [])]
    difficulty_range = body.get("difficulty_range", None)
    language = body.get("language", None)
    topic = body.get("topic", "")

    db = SurveyDatabase(db_path)
    questions = db.get_all_questions()

    # --- Filtering phase ---
    # 1) Filter by language (if specified). Use is_chinese heuristic.
    if language in ("en", "zh"):
        questions = [q for q in questions if (is_chinese(q.get("question_text", "")) if language == "zh" else not is_chinese(q.get("question_text", "")))]

    # 2) Filter by category (if specified)
    if categories:
        questions = [q for q in questions if q.get("category", "").lower() in categories]

    # 3) Filter by difficulty range (if specified)
    if difficulty_range and len(difficulty_range) >= 2:
        lo, hi = difficulty_range[0], difficulty_range[1]
        questions = [q for q in questions if isinstance(q.get("difficulty"), (int, float)) and lo <= q.get("difficulty") <= hi]

    # --- Ranking phase ---
    docs = [q.get("question_text", "") for q in questions]
    query_text = " ".join([str(req.get(k, "")) for k in ("title", "description")]) + " " + str(topic)

    scores: List[float] = []
    # prefer TF-IDF for English when available
    if language == "en":
        try:
            scores = tfidf_rank(query_text, docs)
        except Exception:
            # graceful fallback to simple keyword scoring
            scores = keyword_score(topic, docs)
    else:
        # Chinese / other: basic heuristic combining presence in text and tags
        qtoken = str(topic).lower()
        for q in questions:
            s = 0.0
            text = (q.get("question_text", "") or "").lower()
            tags = " ".join([t.lower() for t in q.get("tags", []) if isinstance(t, str)])
            if qtoken and qtoken in text:
                s += 3.0
            if qtoken and qtoken in tags:
                s += 2.0
            scores.append(s)
        # normalize scores to [0,1]
        maxs = max(scores) if scores else 0.0
        if maxs > 0:
            scores = [s / maxs for s in scores]

    # Pair each question with its score and sort descending
    pairs = list(zip(questions, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)

    # --- Selection phase ---
    selected_pairs: List[Any] = []
    used_ids = set()
    assigned_cat: Dict[Any, Any] = {}

    req_cats = categories or []
    # Map category -> candidate pairs for quick lookup
    cat_map: Dict[str, List[Any]] = {}
    for p in pairs:
        q_obj = p[0]
        cat = (q_obj.get("category") or "").lower()
        cat_map.setdefault(cat, []).append(p)

    # Try to pick one top candidate from each requested category
    for rc in req_cats:
        candidates = cat_map.get(rc, [])
        if candidates:
            chosen = candidates[0]
            qid = chosen[0].get("id")
            if qid not in used_ids:
                selected_pairs.append(chosen)
                used_ids.add(qid)
                assigned_cat[qid] = rc

    # If some requested categories had no direct matches, attempt a tag/text search
    missing = [rc for rc in req_cats if not cat_map.get(rc)]
    if missing:
        full_bank = db.get_all_questions()
        synonyms = {
            "usage": ["usage", "frequency", "behavior"],
            "satisfaction": ["satisfaction", "satisfied", "satisfy"],
            "recommendation": ["recommend", "recommendation", "nps"]
        }
        for rc in missing:
            found = None
            rc_tokens = synonyms.get(rc, [rc])
            for q in full_bank:
                qtext = (q.get("question_text") or "").lower()
                qtags = " ".join([t.lower() for t in q.get("tags", []) if isinstance(t, str)])
                if any(tok in qtext or tok in qtags for tok in rc_tokens):
                    qid = q.get("id")
                    if qid not in used_ids:
                        # assign an intermediate fallback score
                        found = (q, 0.5)
                        break
            if found:
                selected_pairs.append(found)
                used_ids.add(found[0].get("id"))
                assigned_cat[found[0].get("id")] = rc

    # Fill remaining slots by overall ranking
    for p in pairs:
        if len(selected_pairs) >= qcount:
            break
        qid = p[0].get("id")
        if qid in used_ids:
            continue
        selected_pairs.append(p)
        used_ids.add(qid)

    selected = [p[0] for p in selected_pairs]

    # If still short, relax filters and append fallback items
    if len(selected) < qcount:
        fallback = db.get_all_questions()
        if language in ("en", "zh"):
            fallback = [q for q in fallback if (is_chinese(q.get("question_text", "")) if language == "zh" else not is_chinese(q.get("question_text", "")))]
        for q in fallback:
            if len(selected) >= qcount:
                break
            if q not in selected:
                selected.append(q)

    # --- Output construction ---
    out_json = "output_questionaire.json"
    out_txt = "output_questionaire.txt"

    ordered_questions: List[Dict[str, Any]] = []
    by_category: Dict[str, List[Any]] = {}
    for q, score in selected_pairs:
        qid = q.get("id")
        assigned = assigned_cat.get(qid)
        out_cat = assigned if assigned is not None else q.get("category")
        out_cat_display = out_cat.title() if isinstance(out_cat, str) else out_cat
        item = {
            "id": qid,
            "category": out_cat_display,
            "score": float(score),
            "difficulty": q.get("difficulty"),
            "question_text": q.get("question_text"),
            "options": q.get("options")
        }
        ordered_questions.append(item)
        cat = (item["category"] or "Uncategorized")
        by_category.setdefault(cat, []).append(item["id"]) 

    out_obj = {
        "requirements": req,
        "question_count_requested": qcount,
        "question_ids": [it["id"] for it in ordered_questions],
        "by_category": by_category,
        "ordered_questions": ordered_questions
    }

    # Persist outputs (JSON + human-readable text)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"Requirements: {json.dumps(req, ensure_ascii=False)}\n\n")
        for cat, ids in by_category.items():
            f.write(f"Category: {cat}\n")
            for i, qid in enumerate(ids, start=1):
                q = next((qq for qq in ordered_questions if qq["id"] == qid), None)
                if not q:
                    continue
                f.write(f"  {i}. [ID {q['id']}] (score={q['score']:.3f}, difficulty={q.get('difficulty')}) {q['question_text']}\n")
                opts = q.get("options")
                if isinstance(opts, str) and opts.strip():
                    f.write(f"     - options: {opts}\n")
                elif isinstance(opts, list):
                    for o in opts:
                        f.write(f"     - {o}\n")
            f.write("\n")

    return out_obj


if __name__ == "__main__":
    # Interactive mode: optionally accept free-text requirements from user
    req_file = "questionaire_requirements.json"
    if not os.path.exists(req_file):
        print(f"Requirements file not found: {req_file}")
    else:
        print("Enter free-text description to guide questionnaire generation (or press Enter to use existing requirements):")
        try:
            user_input = input('> ').strip()
        except EOFError:
            user_input = ''

        # Decide which requirements file to use.
        # If the user pressed Enter (no input), use the default requirements
        # file so we don't overwrite or corrupt the main `questionaire_requirements.json`.
        default_req_file = "questionaire_requirements_default.json"
        if not user_input:
            # Use default if it exists, otherwise fall back to the main file.
            if os.path.exists(default_req_file):
                used_req_file = default_req_file
                print(f"No free-text provided — using default requirements: {default_req_file}")
            else:
                used_req_file = req_file
                print(f"No free-text provided and default not found — using {req_file}")
            # Do not write anything to disk in this branch (no tracking field written).
            out = generate_questionnaire(used_req_file, db_path="convert_data.json")
            print(f"Wrote output_questionaire.json and output_questionaire.txt with {len(out.get('question_ids', []))} ids")
            # Exit after generation
            raise SystemExit(0)

        # If user provided free text, update `questionaire_requirements.json` with tracking and inferred fields.
        try:
            with open(req_file, 'r', encoding='utf-8') as fr:
                req_obj = json.load(fr)
        except Exception:
            req_obj = {}

        req_obj.setdefault('requirements', {})
        # store the raw free-text used
        req_obj['requirements']['free_text_input'] = user_input

        # If user provided free text, also update requirements JSON with inferred topic/language
        if user_input:
            # Interactive mode: optionally accept free-text requirements from user.
            # If the user presses Enter, we use a separate default requirements file
            # so the main `questionaire_requirements.json` is not overwritten.
            req_file = "questionaire_requirements.json"
            default_req_file = "questionaire_requirements_default.json"

            if not os.path.exists(req_file):
                print(f"Requirements file not found: {req_file}")
                sys.exit(1)

            print("Enter free-text description to guide questionnaire generation (or press Enter to use default requirements):")
            try:
                user_input = input('> ').strip()
            except EOFError:
                user_input = ''

            # If no free-text provided, use the default requirements file (if present)
            if not user_input:
                if os.path.exists(default_req_file):
                    used_req_file = default_req_file
                    print(f"No free-text provided — using default requirements: {default_req_file}")
                else:
                    used_req_file = req_file
                    print(f"No free-text provided and default not found — using {req_file}")

                out = generate_questionnaire(used_req_file, db_path="convert_data.json")
                print(f"Wrote output_questionaire.json and output_questionaire.txt with {len(out.get('question_ids', []))} ids")
                sys.exit(0)

            # At this point user_input is non-empty: update the main requirements file
            try:
                with open(req_file, 'r', encoding='utf-8') as fr:
                    req_obj = json.load(fr)
            except Exception:
                req_obj = {}

            req_obj.setdefault('requirements', {})
            req_obj['requirements']['free_text_input'] = user_input

            # Simple language detection (presence of CJK -> zh)
            lang = 'zh' if any('\u4e00' <= ch <= '\u9fff' for ch in user_input) else 'en'

            # Simple topic extraction: for English take first word >3 chars; for Chinese keep input
            if lang == 'en':
                tokens = [t.strip('.,!?()[]"\'"') for t in re.split(r"\s+", user_input) if len(t) > 3]
                topic_guess = tokens[0].lower() if tokens else user_input.lower()
            else:
                topic_guess = user_input

            # Topic keyword maps (copied from Part4.py -> analyze_dataset_content)
            topic_keywords_en = {
                "Hotel/Accommodation": ["hotel", "accommodation", "room", "stay", "inn"],
                "Travel/General": ["travel", "trip", "journey", "tour", "tourism"],
                "Flight/Transport": ["flight", "airline", "plane", "transport", "bus"],
                "Food/Dining": ["food", "meal", "dining", "restaurant", "eat"],
                "Service/Satisfaction": ["service", "staff", "satisfaction", "quality"]
            }
            topic_keywords_zh = {
                "Hotel/Accommodation": ["酒店", "住宿", "房间", "宾馆", "饭店"],
                "Travel/General": ["旅游", "旅行", "行程", "度假"],
                "Flight/Transport": ["航班", "飞机", "交通", "机场"],
                "Food/Dining": ["餐饮", "食物", "吃饭", "餐厅"],
                "Service/Satisfaction": ["服务", "满意", "推荐", "态度"]
            }

            # Infer categories from the free-text
            inferred_categories = []
            if lang == 'en':
                for label, kws in topic_keywords_en.items():
                    if any(k in user_input.lower() for k in kws):
                        if 'hotel' in label.lower() or 'service' in label.lower() or 'satisfaction' in label.lower():
                            inferred_categories.append('Satisfaction')
                        elif 'travel' in label.lower():
                            inferred_categories.append('Usage')
                        elif 'food' in label.lower():
                            inferred_categories.append('Recommendation')
                inferred_categories = list(dict.fromkeys(inferred_categories))
            else:
                for label, kws in topic_keywords_zh.items():
                    if any(k in user_input for k in kws):
                        if '酒店' in user_input or '酒店' in ''.join(kws):
                            inferred_categories.append('Satisfaction')
                inferred_categories = list(dict.fromkeys(inferred_categories))

            # Update and persist the main requirements file with inferred fields
            req_obj.setdefault('requirements', {})
            req_obj['requirements']['topic'] = topic_guess
            req_obj['requirements']['language'] = lang
            if inferred_categories:
                req_obj['requirements']['categories'] = inferred_categories

            with open(req_file, 'w', encoding='utf-8') as fw:
                json.dump(req_obj, fw, ensure_ascii=False, indent=2)

            print(f"Updated {req_file} with topic='{topic_guess}', language='{lang}', categories={inferred_categories}")

            out = generate_questionnaire(req_file, db_path="convert_data.json")
            print(f"Wrote output_questionaire.json and output_questionaire.txt with {len(out.get('question_ids', []))} ids")
            # Update inferred fields alongside the recorded free-text
            req_obj.setdefault('requirements', {})
            req_obj['requirements']['topic'] = topic_guess
            req_obj['requirements']['language'] = lang
            if inferred_categories:
                req_obj['requirements']['categories'] = inferred_categories

            with open(req_file, 'w', encoding='utf-8') as fw:
                json.dump(req_obj, fw, ensure_ascii=False, indent=2)

            print(f"Updated {req_file} with topic='{topic_guess}', language='{lang}', categories={inferred_categories}")

        out = generate_questionnaire(req_file, db_path="convert_data.json")
        print(f"Wrote output_questionaire.json and output_questionaire.txt with {len(out.get('question_ids', []))} ids")
