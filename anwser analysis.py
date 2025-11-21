import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

with open("convert_data.json", "r", encoding="utf-8") as f:
    qdata = json.load(f)
questions = qdata["questions"]

with open("simulated_responses.json", "r", encoding="utf-8") as f:
    rdata = json.load(f)
responses = rdata["responses"]

qid_to_type = {q["id"]: q["question_type"] for q in questions}
qid_to_cat = {q["id"]: q["category"] for q in questions}

type_stats = defaultdict(lambda: {"answered": 0, "total": 0})

for resp in responses:
    if not resp.get("effective", True):
        continue

    qid = resp["question_id"]
    ans = resp["answer"]
    q_type = resp.get("question_type") or qid_to_type.get(qid)
    if q_type is None:
        continue

    type_stats[q_type]["total"] += 1
    if ans != "not_answered":
        type_stats[q_type]["answered"] += 1

type_answer_rate = {}
for q_type, st in type_stats.items():
    total = st["total"]
    answered = st["answered"]
    rate = answered / total if total > 0 else 0.0
    type_answer_rate[q_type] = rate

print("answer rate：")
for t, r in type_answer_rate.items():
    print(f"{t}: {r:.3f}")


types = list(type_answer_rate.keys())
rates = list(type_answer_rate.values())

plt.figure(figsize=(8, 5))
plt.bar(types, rates, color="steelblue", edgecolor="black")
plt.title("Answer Rate by Question Type (Effective Users Only)")
plt.xlabel("Question Type")
plt.ylabel("Answer Rate")

for i, r in enumerate(rates):
    plt.text(i, r + 0.01, f"{r:.2f}", ha="center", fontsize=10)

plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig("answer_rate_by_type_effective_only.png", dpi=150)
plt.close()
print("saved as answer_rate_by_type_effective_only.png")


cat_total = Counter()
cat_effectless = Counter()

for resp in responses:
    qid = resp["question_id"]
    cat = resp.get("category") or qid_to_cat.get(qid)
    if cat is None:
        continue

    cat_total[cat] += 1
    if resp.get("effective") is False:
        cat_effectless[cat] += 1

cat_effectless_prob = {}
for cat in cat_total:
    prob = cat_effectless[cat] / cat_total[cat] if cat_total[cat] > 0 else 0.0
    cat_effectless_prob[cat] = prob

print("effectless rate：")
for cat, p in cat_effectless_prob.items():
    print(f"{cat}: {p:.3f}")

cats = list(cat_effectless_prob.keys())
probs = [cat_effectless_prob[c] for c in cats]

plt.figure(figsize=(8, 5))
plt.bar(cats, probs, color="indianred", edgecolor="black")
plt.title("Probability of Effectless Responses by Category")
plt.xlabel("Category")
plt.ylabel("Effectless Probability")

for i, p in enumerate(probs):
    plt.text(i, p + 0.01, f"{p:.2f}", ha="center", fontsize=10)

plt.ylim(0, 1.05)
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("effectless_probability_by_category.png", dpi=150)
plt.close()
print("save as effectless_probability_by_category.png")
