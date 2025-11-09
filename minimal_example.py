import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# 1. Definition der Datenbasis
# -----------------------------

operations = pd.DataFrame([
    ["Rahmen", "Schweißen", "M1", 3, "Lackieren"],
    ["Rahmen", "Lackieren", "M2", 2, "Montage"],
    ["Laufrad", "Speichen", "M1", 1, "Zentrieren"],
    ["Laufrad", "Zentrieren", "M2", 1, "Montage"],
    ["Fahrrad", "Montage", "M3", 2, None]
], columns=["Produkt", "Vorgang", "Maschine", "Dauer", "Nachfolger"])

due_date = 10.0
plan = []
visited = set()  # <-- neu: verhindert Wiederholung

# -----------------------------
# 2. Rückwärtsterminierung
# -----------------------------

def backward_schedule(product, successor_end_time):
    """Plane alle Vorgänge für ein Produkt rückwärts."""
    ops = operations[operations["Produkt"] == product].copy()

    # Iteration rückwärts durch die Vorgangskette
    for _, op in ops[::-1].iterrows():
        op_id = (op["Produkt"], op["Vorgang"])
        if op_id in visited:
            continue  # Vorgang schon verarbeitet

        visited.add(op_id)
        end_time = successor_end_time
        start_time = end_time - op["Dauer"]
        plan.append({
            "Produkt": op["Produkt"],
            "Vorgang": op["Vorgang"],
            "Maschine": op["Maschine"],
            "Start": start_time,
            "Ende": end_time
        })

        # Rückwärtige Planung für Vorgänger
        prev_ops = operations[operations["Nachfolger"] == op["Vorgang"]]
        for _, prev in prev_ops.iterrows():
            backward_schedule(prev["Produkt"], start_time)

# Starte mit Endprodukt
backward_schedule("Fahrrad", due_date)

# -----------------------------
# 3. Konfliktlösung (EDD-Regel)
# -----------------------------

plan_df = pd.DataFrame(plan)

result = []
for machine, group in plan_df.groupby("Maschine"):
    group = group.sort_values("Ende")  # Earliest Due Date First
    current_time = 0
    for _, op in group.iterrows():
        start = max(current_time, op["Start"])
        end = start + (op["Ende"] - op["Start"])
        result.append({**op, "Start": start, "Ende": end})
        current_time = end

schedule = pd.DataFrame(result).sort_values("Start")

# -----------------------------
# 4. Ergebnis anzeigen
# -----------------------------
print("\n--- Geplanter Ablauf ---")
print(schedule)

# -----------------------------
# 5. Gantt-Chart
# -----------------------------
fig, ax = plt.subplots(figsize=(8,4))
colors = {"M1":"tab:blue", "M2":"tab:orange", "M3":"tab:green"}

for _, row in schedule.iterrows():
    ax.barh(row["Maschine"], row["Ende"]-row["Start"],
            left=row["Start"], color=colors[row["Maschine"]])
    ax.text(row["Start"]+0.1, row["Maschine"],
            f"{row['Produkt']}-{row['Vorgang']}", va='center', color='white')

ax.set_xlabel("Zeit [h]")
ax.set_ylabel("Maschine")
ax.set_title("Einfacher Rückwärtsterminierungsplan (EDD-Regel)")
plt.tight_layout()
plt.show()
