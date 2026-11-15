#!/usr/bin/env python3
"""Lee ../plan_4dias_cuerpo_completo.txt y genera plan.js (la app lee plan.js).
Uso:  python3 generar_plan.py [ruta_al_txt]"""
import re, json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "plan_4dias_cuerpo_completo.txt")
lines = open(src, encoding="utf-8").read().splitlines()

def is_div(l): return re.fullmatch(r"-{10,}", l.strip()) is not None
# --- separar secciones (divisor / titulo / divisor)
secs, cur, i = [], {"title": "Resumen", "lines": []}, 0
while i < len(lines):
    l = lines[i]
    if is_div(l) and i + 2 < len(lines) and lines[i+1].strip() and is_div(lines[i+2]):
        secs.append(cur); cur = {"title": lines[i+1].strip(), "lines": []}; i += 3; continue
    if not l.startswith("="): cur["lines"].append(l)
    i += 1
secs.append(cur)

days, help_ = [], []
ex_re = re.compile(r"^\s*\d+\.\s+(.*?):\s+(\d+)\s*x\s*(\d+(?:-\d+)?(?:\s*s)?)\s*(?:RIR\s*(\d+(?:-\d+)?))?\s*$")
for s in secs:
    m = re.match(r"DIA (\d+) \((\w+)\)\s*-\s*(.*?):\s*(.*)$", s["title"])
    if m:
        ex = []
        for l in s["lines"]:
            e = ex_re.match(l)
            if e:
                name, n, reps, rir = e.groups()
                time = reps.endswith("s")
                ex.append([name.strip(), int(n), reps.strip(), rir or "", time])
        days.append({"id": "d" + m.group(1), "wd": m.group(2).upper(),
                     "title": f"Día {m.group(1)} · " + re.sub(r" (\w)$", lambda x: " " + x.group(1).upper(), m.group(3).capitalize()),
                     "sub": m.group(4).capitalize(), "ex": ex})
    else:
        items = []
        for l in s["lines"]:
            if not l.strip():
                continue
            if l[0] in " \t" and items:
                items[-1] += " " + l.strip()
            else:
                items.append(l.strip())
        if items: help_.append({"title": s["title"], "items": items})

out = "// Generado por generar_plan.py desde el txt. No editar a mano.\nconst PLAN=" + json.dumps({"days": days, "help": help_}, ensure_ascii=False, indent=1) + ";\n"
open(os.path.join(here, "plan.js"), "w", encoding="utf-8").write(out)
print("OK:", len(days), "dias,", sum(len(d["ex"]) for d in days), "ejercicios,", len(help_), "secciones de ayuda")
