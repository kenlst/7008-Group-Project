import json
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")
with open("convert_data.json", "r", encoding="utf-8") as f:
    qdata = json.load(f)
questions = qdata["questions"]

qid_to_type = {q["id"]: q["question_type"] for q in questions}
with open("simulated_responses.json", "r", encoding="utf-8") as f:
    rdata = json.load(f)
responses = rdata["responses"]


stats = defaultdict(lambda: {"answered": 0, "total": 0})

for resp in responses:
    qid = resp["question_id"]
    ans = resp["answer"]
    q_type = qid_to_type.get(qid)
    if q_type is None:
        continue

    stats[q_type]["total"] += 1
    if ans != "not_answered":
        stats[q_type]["answered"] += 1

type_rates = {}
for q_type, st in stats.items():
    total = st["total"]
    answered = st["answered"]
    rate = answered / total if total > 0 else 0.0
    type_rates[q_type] = rate

print("completion rate", type_rates)

sum_rates = sum(type_rates.values())
type_pref_prob = {t: r / sum_rates for t, r in type_rates.items()}

print("normalize：", type_pref_prob)
print("Sum：", sum(type_pref_prob.values()))

types = list(type_pref_prob.keys())
probs = list(type_pref_prob.values())

plt.figure(figsize=(8, 5))
plt.bar(types, probs, color="steelblue", edgecolor="black")

plt.title("User Preference over Question Types\n(Assuming Equal Type Proportions)", fontsize=14)
plt.xlabel("Question Type")
plt.ylabel("Preference Probability (Sum = 1)")

for i, p in enumerate(probs):
    plt.text(i, p + 0.01, f"{p:.2f}", ha="center", fontsize=10)

plt.ylim(0, max(probs) * 1.15)
plt.tight_layout()
plt.savefig("question_type_preference_equal_proportion.png", dpi=150)
plt.close()

print("saved as question_type_preference_equal_proportion.png")
