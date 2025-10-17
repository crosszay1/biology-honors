import pandas as pd
import plotly.express as px

generations = []
masses = []

with open("mass_list.txt", "r") as file:
    for line in file:
        parts = line.strip().split()
        if len(parts) >= 5 and parts[0] == "Winner" and parts[1] == "mass:":
            mass = float(parts[2])
            generation = int(parts[4])
            masses.append(mass)
            generations.append(generation)

# Create a DataFrame
df = pd.DataFrame({"Generation": generations, "Winner Mass": masses})

fig = px.line(
    df,
    x="Generation",
    y="Winner Mass",
    title="Winner Mass vs Generation",
    markers=True
)

fig.update_traces(line=dict(width=2), marker=dict(size=6))
fig.show()

fig.write_html("winner_mass_graph.html")
print("Interactive graph saved as winner_mass_graph.html")
