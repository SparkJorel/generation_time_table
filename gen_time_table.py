from ortools.sat.python import cp_model
import json

# 1. Charger les données JSON
with open("subjects.json") as f:
    subjects_data = json.load(f)
with open("rooms.json") as f:
    rooms_data = json.load(f)

# 2. Extraire les cours (ex: niveau 4, semestre 2)
courses = subjects_data["niveau"]["4"]["s2"]["subjects"]
rooms = rooms_data["Informatique"]

days = list(range(6))      # 0=Lundi ... 5=Samedi
periods = list(range(5))   # 0=P1 (7h-9h55) ... 4=P5 (19h-21h55)
weights = [1, 2, 3, 4, 5]  # w1 < w2 < ... < w5

# 3. Créer le modèle
model = cp_model.CpModel()

# 4. Variables X[c, r, d, p]
x = {}
for c_idx, course in enumerate(courses):
    for r_idx, room in enumerate(rooms):
        for d in days:
            for p in periods:
                x[c_idx, r_idx, d, p] = model.NewBoolVar(
                    f"x_c{c_idx}_r{r_idx}_d{d}_p{p}"
                )

# 5. Contrainte 1 : chaque cours planifié exactement 1 fois
for c_idx in range(len(courses)):
    model.Add(
        sum(x[c_idx, r_idx, d, p]
            for r_idx in range(len(rooms))
            for d in days
            for p in periods) == 1
    )

# 6. Contrainte 2 : une seule salle, une seule période = 1 cours max
for r_idx in range(len(rooms)):
    for d in days:
        for p in periods:
            model.Add(
                sum(x[c_idx, r_idx, d, p]
                    for c_idx in range(len(courses))) <= 1
            )

# 7. Contrainte 3 : un enseignant ne peut être en 2 endroits en même temps
# Regrouper les cours par enseignant
from collections import defaultdict
teacher_courses = defaultdict(list)
for c_idx, course in enumerate(courses):
    teacher = course.get("Course Lecturer", [""])[0]
    if teacher:
        teacher_courses[teacher].append(c_idx)

for teacher, c_list in teacher_courses.items():
    for d in days:
        for p in periods:
            model.Add(
                sum(x[c_idx, r_idx, d, p]
                    for c_idx in c_list
                    for r_idx in range(len(rooms))) <= 1
            )

# 8. Fonction objectif : minimiser la somme pondérée (favoriser le matin)
objective = sum(
    weights[p] * x[c_idx, r_idx, d, p]
    for c_idx in range(len(courses))
    for r_idx in range(len(rooms))
    for d in days
    for p in periods
)
model.Minimize(objective)

# 9. Résoudre
solver = cp_model.CpSolver()
status = solver.Solve(model)

# 10. Afficher les résultats
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("=== EMPLOI DU TEMPS GÉNÉRÉ ===")
    day_names = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]
    period_names = ["7h-9h55","10h05-12h55","13h05-15h55","16h05-18h55","19h05-21h55"]
    for c_idx, course in enumerate(courses):
        for r_idx, room in enumerate(rooms):
            for d in days:
                for p in periods:
                    if solver.Value(x[c_idx, r_idx, d, p]) == 1:
                        print(f"{course['code']} | {room['num']} | {day_names[d]} | {period_names[p]}")
else:
    print("Aucune solution trouvée.")