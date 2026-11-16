#!/usr/bin/env python3
"""Lee el txt del plan y genera plan.js (la app lee plan.js).
Uso:  python3 generar_plan.py [ruta_al_txt]
Por defecto: ../plan_4dias_torso_pierna.txt"""
import re, json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "plan_4dias_torso_pierna.txt")
lines = open(src, encoding="utf-8").read().splitlines()

DAYWORD = r"(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)"
day_new = re.compile(DAYWORD + r"\s*-\s*(.*)$")                       # LUNES - TORSO A (prioridad: ...)
day_old = re.compile(r"DIA (\d+) \(" + DAYWORD[1:-1].join(["(", ")"]) + r"\)\s*-\s*(.*?):\s*(.*)$")  # DIA 1 (LUNES) - X: Y
ex_re = re.compile(r"^\s*\d+\.\s+(.*?):\s+(\d+)\s*x\s*(\d+(?:-\d+)?(?:\s*s)?)\s*(?:RIR\s*(\d+(?:-\d+)?))?\s*$")
head_re = re.compile(r"^[A-Z][A-Z ]+$")                                # REGLAS, AJUSTES...
block_re = re.compile(r"^(?:BLOQUE\s+)?([A-Z][A-Z /]+)$")

def is_div(l): return re.fullmatch(r"-{10,}", l.strip()) is not None
def fix_caps(t):
    t = t.capitalize()
    return re.sub(r"\b[a-z]\b", lambda x: x.group(0).upper(), t)       # "torso a" -> "Torso A"

# --- separar en secciones (divisor / titulo / divisor)
secs, cur, i = [], {"title": "Resumen", "lines": []}, 0
while i < len(lines):
    l = lines[i]
    if is_div(l) and i + 2 < len(lines) and lines[i+1].strip() and is_div(lines[i+2]):
        secs.append(cur); cur = {"title": lines[i+1].strip(), "lines": []}; i += 3; continue
    if not l.startswith("="): cur["lines"].append(l)
    i += 1
secs.append(cur)

def join_names(ls):  # une nombres de ejercicio partidos en dos lineas
    out = []
    for l in ls:
        if out and l[:1] in " \t" and re.match(r"^\s*\d+\.\s", out[-1]) and not ex_re.match(out[-1]):
            out[-1] = out[-1].rstrip() + " " + l.strip()
        else:
            out.append(l)
    return out

def to_items(ls):
    items = []
    for l in ls:
        if not l.strip(): continue
        if l[0] in " \t" and items: items[-1] += " " + l.strip()
        else: items.append(l.strip())
    return items

days, help_ = [], []
for s in secs:
    title, d = s["title"], None
    m = day_new.match(title)
    if m:
        rest = m.group(2)
        p = re.match(r"^(.*?)\s*\((.*)\)\s*$", rest)
        name, sub = (p.group(1), p.group(2)) if p else (rest, "")
        d = {"wd": m.group(1), "title": fix_caps(name), "sub": sub.capitalize()}
    else:
        m = day_old.match(title)
        if m:
            d = {"wd": m.group(2), "title": fix_caps(m.group(3)), "sub": m.group(4).capitalize()}
    if d:
        n = len(days) + 1
        ex, block = [], ""
        for l in join_names(s["lines"]):
            e = ex_re.match(l)
            if e:
                name, sets, reps, rir = e.groups()
                ex.append([name.strip(), int(sets), reps.strip(), rir or "", reps.endswith("s"), block])
                continue
            b = block_re.match(l.strip()) if l and l[0] not in " \t" else None
            if b: block = b.group(1).strip().capitalize()
        d.update({"id": f"d{n}", "title": f"Día {n} · " + d["title"], "ex": ex})
        days.append(d)
    else:
        # seccion informativa; dentro puede haber subtitulos en mayusculas (REGLAS, AJUSTES...)
        parts, cur2 = [], {"title": title, "lines": []}
        for l in s["lines"]:
            if head_re.match(l.strip()) and l[:1] not in " \t":
                parts.append(cur2); cur2 = {"title": l.strip().capitalize(), "lines": []}
            else:
                cur2["lines"].append(l)
        parts.append(cur2)
        for p in parts:
            items = to_items(p["lines"])
            if items: help_.append({"title": p["title"] if not p["title"].split("(")[0].isupper() else p["title"].capitalize(), "items": items})

out = "// Generado por generar_plan.py desde el txt. No editar a mano.\nconst PLAN=" + json.dumps({"days": days, "help": help_}, ensure_ascii=False, indent=1) + ";\n"
open(os.path.join(here, "plan.js"), "w", encoding="utf-8").write(out)
print("OK:", len(days), "dias,", sum(len(d["ex"]) for d in days), "ejercicios,", len(help_), "secciones de ayuda")
for d in days: print(" ", d["id"], d["wd"], "|", d["title"], "|", d["sub"], "|", len(d["ex"]), "ej")
for h in help_: print("  ayuda:", h["title"][:60], len(h["items"]))
