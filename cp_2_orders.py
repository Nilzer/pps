from ortools.sat.python import cp_model
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# 1. Basisdaten: Operationen
# -----------------------------
# Produktstruktur bleibt gleich
BOM = [
    ["Rahmen", "Schweißen", "M1", 3, "Lackieren"],
    ["Rahmen", "Lackieren", "M2", 2, "Montage"],
    ["Laufrad", "Speichen", "M1", 1, "Zentrieren"],
    ["Laufrad", "Zentrieren", "M2", 1, "Montage"],
    ["Fahrrad", "Montage", "M3", 2, None]
]

# Aufträge
orders = pd.DataFrame([
    ["A", 12, 1],  # (Auftrag, Liefertermin, Priorität)
    ["B", 16, 2]
], columns=["Auftrag", "Liefertermin", "Priorität"])

machines = sorted({r[2] for r in BOM})

# -----------------------------
# 2. CP-Modell
# -----------------------------
model = cp_model.CpModel()

task_starts, task_ends, task_intervals = {}, {}, {}

# Vorgänge erzeugen für jeden Auftrag
for _, order in orders.iterrows():
    for product, op, machine, dur, succ in BOM:
        name = f"{order['Auftrag']}-{product}-{op}"
        start = model.NewIntVar(0, 100, f"start_{name}")
        end = model.NewIntVar(0, 100, f"end_{name}")
        interval = model.NewIntervalVar(start, dur, end, f"int_{name}")
        task_starts[name] = start
        task_ends[name] = end
        task_intervals[name] = interval

# -----------------------------
# 3. Abhängigkeitsbedingungen
# -----------------------------
for _, order in orders.iterrows():
    for product, op, machine, dur, succ in BOM:
        if succ:
            pred = f"{order['Auftrag']}-{product}-{op}"
            succ_ops = [r for r in BOM if r[1] == succ]
            for s_product, s_op, s_machine, _, _ in succ_ops:
                s_name = f"{order['Auftrag']}-{s_product}-{s_op}"
                model.Add(task_starts[s_name] >= task_ends[pred])

# -----------------------------
# 4. Maschinenkapazität
# -----------------------------
for m in machines:
    intervals = [task_intervals[n] for n in task_intervals if f"-{m}-" not in n and m in n]
    # Korrektur: passendes Maschinenlabel finden
    intervals = [task_intervals[name] for name, _ in task_intervals.items()
                 if f"-{m}-" in name]
    model.AddNoOverlap(intervals)

# -----------------------------
# 5. Verspätungs- und Zieldefinition
# -----------------------------
tardiness_vars = []
tardiness_dict = {}

for _, order in orders.iterrows():
    final_task = f"{order['Auftrag']}-Fahrrad-Montage"
    end_time = task_ends[final_task]
    due = order["Liefertermin"]

    tardiness = model.NewIntVar(0, 100, f"tardiness_{order['Auftrag']}")
    model.Add(tardiness >= end_time - due)

    weighted_tardiness = model.NewIntVar(0, 1000, f"weighted_tard_{order['Auftrag']}")
    model.AddMultiplicationEquality(weighted_tardiness, [tardiness, order["Priorität"]])

    tardiness_vars.append(weighted_tardiness)
    tardiness_dict[order["Auftrag"]] = tardiness  # <- Speichern

# Ziel: Minimierung der gewichteten Verspätung
model.Minimize(sum(tardiness_vars))

# -----------------------------
# 6. Solver ausführen
# -----------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10
solver.parameters.num_search_workers = 8
result = solver.Solve(model)

# -----------------------------
# 7. Ergebnisse
# -----------------------------
if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("\n--- Plan mit mehreren Aufträgen ---")
    rows = []
    for name in task_starts:
        parts = name.split("-")
        auftrag, produkt, vorgang = parts[0], parts[1], parts[2]
        start = solver.Value(task_starts[name])
        end = solver.Value(task_ends[name])
        maschine = [r[2] for r in BOM if r[1] == vorgang][0]
        rows.append({
            "Auftrag": auftrag,
            "Produkt": produkt,
            "Vorgang": vorgang,
            "Maschine": maschine,
            "Start": start,
            "Ende": end
        })
    schedule = pd.DataFrame(rows).sort_values(["Start", "Auftrag"])
    print(schedule)

    # Verspätungen anzeigen
    print("\n--- Liefertermine ---")
    for _, order in orders.iterrows():
        t = solver.Value(tardiness_dict[order["Auftrag"]])
        print(f"Auftrag {order['Auftrag']} Verspätung: {t}h (Liefertermin {order['Liefertermin']})")

    # -----------------------------
    # 8. Gantt-Diagramm
    # -----------------------------
    fig, ax = plt.subplots(figsize=(9,4))
    colors = {"M1": "tab:blue", "M2": "tab:orange", "M3": "tab:green"}
    for _, row in schedule.iterrows():
        label = f"{row['Auftrag']}-{row['Produkt']}-{row['Vorgang']}"
        ax.barh(row["Maschine"], row["Ende"]-row["Start"],
                left=row["Start"], color=colors[row["Maschine"]])
        ax.text(row["Start"]+0.1, row["Maschine"], label, va='center', color='white')
    ax.set_xlabel("Zeit [h]")
    ax.set_ylabel("Maschine")
    ax.set_title("Mehrauftragsplanung mit Prioritäten (CP-SAT)")
    plt.tight_layout()
    plt.show()
else:
    print("Keine Lösung gefunden.")
