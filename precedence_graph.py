import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -----------------------------
# 1. Definition der Operationen
# -----------------------------
operations = pd.DataFrame([
    ["Rahmen", "Schweißen", "M1", 3, "Lackieren"],
    ["Rahmen", "Lackieren", "M2", 2, "Montage"],
    ["Laufrad", "Speichen", "M1", 1, "Zentrieren"],
    ["Laufrad", "Zentrieren", "M2", 1, "Montage"],
    ["Fahrrad", "Montage", "M3", 2, None]
], columns=["Produkt", "Vorgang", "Maschine", "Dauer", "Nachfolger"])

due_date = 10.0

# -----------------------------
# 2. Graph aufbauen
# -----------------------------
G = nx.DiGraph()

# Knoten hinzufügen
for _, op in operations.iterrows():
    node = f"{op['Produkt']}-{op['Vorgang']}"
    G.add_node(node, **op.to_dict())

# Kanten (Abhängigkeiten) hinzufügen
for _, op in operations.iterrows():
    if op["Nachfolger"]:
        pred = f"{op['Produkt']}-{op['Vorgang']}"
        succ_ops = operations[operations["Vorgang"] == op["Nachfolger"]]
        for _, succ in succ_ops.iterrows():
            succ_node = f"{succ['Produkt']}-{succ['Vorgang']}"
            G.add_edge(pred, succ_node)

# -----------------------------
# 3. Rückwärtsterminierung
# -----------------------------
plan = {}
plan_times = {}

# Wir starten vom Endknoten (keine Nachfolger)
end_nodes = [n for n in G.nodes if G.out_degree(n) == 0]
for n in end_nodes:
    plan[n] = {"Ende": due_date, "Start": due_date - G.nodes[n]["Dauer"]}

# Rückwärts über alle Vorgänger
for node in reversed(list(nx.topological_sort(G))):
    if node not in plan:
        successors = list(G.successors(node))
        if successors:
            earliest_successor_start = min(plan[s]["Start"] for s in successors)
        else:
            earliest_successor_start = due_date
        duration = G.nodes[node]["Dauer"]
        plan[node] = {
            "Ende": earliest_successor_start,
            "Start": earliest_successor_start - duration
        }

# In DataFrame umwandeln
schedule = pd.DataFrame([
    {
        "Vorgang": node,
        "Maschine": G.nodes[node]["Maschine"],
        "Start": plan[node]["Start"],
        "Ende": plan[node]["Ende"]
    }
    for node in plan
]).sort_values("Start")

# -----------------------------
# 4. Ergebnis ausgeben
# -----------------------------
print("\n--- Automatisch erzeugter Rückwärtsterminplan ---")
print(schedule)

# -----------------------------
# 5. Graph visualisieren
# -----------------------------
plt.figure(figsize=(8,4))
pos = nx.shell_layout(G)
nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2500, font_size=9)
nx.draw_networkx_edge_labels(G, pos, edge_labels={(u,v):"→" for u,v in G.edges()})
plt.title("Vorgangsabhängigkeitsgraph")
plt.show()

# -----------------------------
# 6. Gantt-Diagramm
# -----------------------------
fig, ax = plt.subplots(figsize=(8,4))
for _, row in schedule.iterrows():
    ax.barh(row["Maschine"], row["Ende"]-row["Start"], left=row["Start"])
    ax.text(row["Start"]+0.1, row["Maschine"], row["Vorgang"], va='center', color='white')

ax.set_xlabel("Zeit [h]")
ax.set_ylabel("Maschine")
ax.set_title("Automatisch terminierter Plan")
plt.tight_layout()
plt.show()
