from ortools.sat.python import cp_model
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# 1. Datengrundlage
# -----------------------------
operations = pd.DataFrame([
    ["Rahmen", "Schweißen", "M1", 3, "Lackieren"],
    ["Rahmen", "Lackieren", "M2", 2, "Montage"],
    ["Laufrad", "Speichen", "M1", 1, "Zentrieren"],
    ["Laufrad", "Zentrieren", "M2", 1, "Montage"],
    ["Fahrrad", "Montage", "M3", 2, None]
], columns=["Produkt", "Vorgang", "Maschine", "Dauer", "Nachfolger"])

# Maschinenliste
machines = sorted(operations["Maschine"].unique())

# -----------------------------
# 2. Modell erstellen
# -----------------------------
model = cp_model.CpModel()

# Variablen für Start, Ende, Intervall
task_starts = {}
task_ends = {}
task_intervals = {}

for i, op in operations.iterrows():
    name = f"{op['Produkt']}-{op['Vorgang']}"
    start = model.NewIntVar(0, 100, f"start_{name}")
    end = model.NewIntVar(0, 100, f"end_{name}")
    interval = model.NewIntervalVar(start, op["Dauer"], end, f"interval_{name}")
    task_starts[name] = start
    task_ends[name] = end
    task_intervals[name] = interval

# -----------------------------
# 3. Abhängigkeitsbedingungen
# -----------------------------
for _, op in operations.iterrows():
    if op["Nachfolger"]:
        pred = f"{op['Produkt']}-{op['Vorgang']}"
        succ_ops = operations[operations["Vorgang"] == op["Nachfolger"]]
        for _, succ in succ_ops.iterrows():
            succ_name = f"{succ['Produkt']}-{succ['Vorgang']}"
            model.Add(task_starts[succ_name] >= task_ends[pred])

# -----------------------------
# 4. Maschinenkapazität (keine Überlappung)
# -----------------------------
for m in machines:
    intervals = [task_intervals[f"{r['Produkt']}-{r['Vorgang']}"]
                 for _, r in operations.iterrows() if r["Maschine"] == m]
    model.AddNoOverlap(intervals)

# -----------------------------
# 5. Ziel: Minimierung des Makespan
# -----------------------------
makespan = model.NewIntVar(0, 100, "makespan")
for name, end in task_ends.items():
    model.Add(makespan >= end)
model.Minimize(makespan)

# -----------------------------
# 6. Lösen
# -----------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10
solver.parameters.num_search_workers = 8  # Multi-Threading
result = solver.Solve(model)

# -----------------------------
# 7. Ergebnis ausgeben
# -----------------------------
if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("\n--- Optimaler Plan ---")
    rows = []
    for i, op in operations.iterrows():
        name = f"{op['Produkt']}-{op['Vorgang']}"
        start = solver.Value(task_starts[name])
        end = solver.Value(task_ends[name])
        rows.append({
            "Produkt": op["Produkt"],
            "Vorgang": op["Vorgang"],
            "Maschine": op["Maschine"],
            "Start": start,
            "Ende": end
        })
    schedule = pd.DataFrame(rows).sort_values("Start")
    print(schedule)
    print(f"\nMinimaler Makespan: {solver.Value(makespan)} Stunden")

    # -----------------------------
    # 8. Visualisierung (Gantt)
    # -----------------------------
    colors = {"M1": "tab:blue", "M2": "tab:orange", "M3": "tab:green"}
    fig, ax = plt.subplots(figsize=(8,4))
    for _, row in schedule.iterrows():
        ax.barh(row["Maschine"], row["Ende"]-row["Start"], left=row["Start"],
                color=colors[row["Maschine"]])
        ax.text(row["Start"]+0.1, row["Maschine"],
                f"{row['Produkt']}-{row['Vorgang']}",
                va='center', color='white')
    ax.set_xlabel("Zeit [h]")
    ax.set_ylabel("Maschine")
    ax.set_title("Optimaler Produktionsplan (CP-SAT)")
    plt.tight_layout()
    plt.show()
else:
    print("Keine Lösung gefunden.")
