"""Build the axis-D ontology skeleton (D2: schema) and instantiate the
hasPrerequisite relation (D6: group-A hard facts, no LLM inference) per
PROJECT_DESIGN.md §7 축D / §12.3.

Schema follows the doc's schema draft exactly:
  Classes: Course, Lab, Professor, ResearchTopic, Skill, Department
  Properties: hasPrerequisite(transitive), isSubfieldOf(transitive),
    partOfDepartment, coversTopic, requiresSkill, providesSkill,
    hasSynergyWith(non-transitive)

`specializesIn` is listed in the schema draft but not used by any CQ and its
domain/range were never pinned down in discussion — declared but left
uninstantiated, flagged as an open item rather than guessed.

CQ3 (prerequisite cycle detection) was originally meant to be answered by
declaring hasPrerequisite Transitive + Asymmetric + Irreflexive, so a cycle
would make the ontology reasoner-inconsistent. That doesn't work: OWL 2 DL
forbids a Transitive property from also being Asymmetric/Irreflexive (a
"non-simple property" restriction, needed to keep the logic decidable) —
HermiT rejects the ontology outright with a structural error, not a
consistency failure. So the schema here matches the design doc exactly
(hasPrerequisite/isSubfieldOf: Transitive only), and cycle detection is done
as a separate graph check below, not via reasoner inconsistency.
"""
import json

from owlready2 import (
    DataProperty,
    FunctionalProperty,
    ObjectProperty,
    Thing,
    TransitiveProperty,
    get_ontology,
    sync_reasoner_hermit,
)

CURRICULUM = "UG_2026_curriculum_courses.jsonl"
PREREQ_PAIRS = "UG_2026_axisA_pairs_a.jsonl"
OUT = "curri.owl"

onto = get_ontology("http://3min-curri.postech.ac.kr/onto.owl")


def safe_name(course_code):
    """OWL individual names can't contain '/', ',', spaces."""
    return "C_" + course_code.replace("/", "_").replace(", ", "_").replace(",", "_").replace(" ", "")


with onto:
    # --- D2: classes ---
    class Course(Thing):
        pass

    class Lab(Thing):
        pass

    class Professor(Thing):
        pass

    class ResearchTopic(Thing):
        pass

    class Skill(Thing):
        pass

    class Department(Thing):
        pass

    # --- D2: object properties ---
    class hasPrerequisite(ObjectProperty, TransitiveProperty):
        domain = [Course]
        range = [Course]

    class isSubfieldOf(ObjectProperty, TransitiveProperty):
        domain = [ResearchTopic]
        range = [ResearchTopic]

    class partOfDepartment(ObjectProperty, FunctionalProperty):
        domain = [Course]
        range = [Department]

    class coversTopic(ObjectProperty):
        domain = [Lab]
        range = [ResearchTopic]

    class requiresSkill(ObjectProperty):
        domain = [Lab]
        range = [Skill]

    class providesSkill(ObjectProperty):
        domain = [Course]
        range = [Skill]

    class hasSynergyWith(ObjectProperty):
        domain = [Course]
        range = [Course]

    # specializesIn: declared per schema draft, domain/range left unpinned —
    # NOT instantiated. See open_items in PROJECT_DESIGN.md.
    class specializesIn(ObjectProperty):
        pass

    class courseNameKr(Course >> str, DataProperty, FunctionalProperty):
        pass


def load_courses():
    return [json.loads(l) for l in open(CURRICULUM, encoding="utf-8")]


def main():
    courses = load_courses()

    # --- Department individuals, derived from course_code prefix ---
    depts = {}
    import re

    for c in courses:
        m = re.match(r"^([A-Z]{2,4})", c["course_code"])
        if not m:
            continue
        dept_code = m.group(1)
        if dept_code not in depts:
            depts[dept_code] = onto.Department(dept_code)

    # --- Course individuals ---
    course_individuals = {}
    for c in courses:
        code = c["course_code"]
        ind = onto.Course(safe_name(code))
        ind.courseNameKr = c.get("course_name_kr") or ""
        course_individuals[code] = ind
        m = re.match(r"^([A-Z]{2,4})", code)
        if m and m.group(1) in depts:
            ind.partOfDepartment = depts[m.group(1)]

    # --- hasPrerequisite instances (group A, hard facts, no LLM) ---
    n_edges = 0
    missing = []
    for line in open(PREREQ_PAIRS, encoding="utf-8"):
        row = json.loads(line)
        anchor = row["anchor_course"]  # prerequisite
        positive = row["positive_course"]  # course that requires it
        if anchor not in course_individuals or positive not in course_individuals:
            missing.append((anchor, positive))
            continue
        course_individuals[positive].hasPrerequisite.append(course_individuals[anchor])
        n_edges += 1

    print(f"Departments: {len(depts)}")
    print(f"Courses: {len(course_individuals)}")
    print(f"hasPrerequisite edges inserted: {n_edges}")
    print(f"skipped (code not found): {len(missing)}")

    onto.save(file=OUT, format="rdfxml")
    print(f"saved: {OUT}")

    # --- CQ3: prerequisite cycle detection (graph check, not reasoner —
    # see module docstring for why Transitive+Irreflexive doesn't work) ---
    print("\nChecking for hasPrerequisite cycles (CQ3)...")
    import sys
    from collections import defaultdict

    graph = defaultdict(list)
    for line in open(PREREQ_PAIRS, encoding="utf-8"):
        row = json.loads(line)
        graph[row["positive_course"]].append(row["anchor_course"])

    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    cycles = []
    sys.setrecursionlimit(10000)

    def dfs(u, path):
        color[u] = GRAY
        path.append(u)
        for v in graph[u]:
            if color[v] == GRAY:
                cycles.append(path[path.index(v):] + [v])
            elif color[v] == WHITE:
                dfs(v, path)
        path.pop()
        color[u] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node, [])

    if cycles:
        print(f"  FOUND {len(cycles)} cycle(s) — CQ3 answer is YES, data has a contradiction:")
        for c in cycles:
            print(f"    {' -> '.join(c)}")
    else:
        print("  No cycles found — CQ3 answer is NO.")

    # --- D9: reasoner consistency check (schema/instance-level, separate
    # from the cycle check above) ---
    print("\nRunning HermiT reasoner...")
    try:
        with onto:
            sync_reasoner_hermit(infer_property_values=True)
        print("Reasoner finished: ontology is CONSISTENT.")
    except Exception as e:
        print("Reasoner FAILED — ontology is INCONSISTENT (or reasoner error):")
        print(f"  {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
