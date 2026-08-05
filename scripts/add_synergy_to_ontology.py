"""Load the existing curri.owl (built by build_ontology.py) and add
hasSynergyWith instances from UG_2026_axisD_hasSynergyWith.jsonl (grp B,
soft/explanatory relation — no reasoner-inconsistency semantics attached,
unlike hasPrerequisite). Re-saves curri.owl and re-runs the reasoner.
"""
import json

from owlready2 import get_ontology, sync_reasoner_hermit

OWL_FILE = "curri.owl"
SYNERGY_PAIRS = "UG_2026_axisD_hasSynergyWith.jsonl"


def safe_name(course_code):
    return "C_" + course_code.replace("/", "_").replace(", ", "_").replace(",", "_").replace(" ", "")


def main():
    onto = get_ontology(f"file://{OWL_FILE}").load()
    hasSynergyWith = onto.hasSynergyWith
    course_cls = onto.Course

    inserted = 0
    missing = []
    for line in open(SYNERGY_PAIRS, encoding="utf-8"):
        row = json.loads(line)
        a_name = safe_name(row["anchor_course"])
        b_name = safe_name(row["positive_course"])
        a_ind = onto.search_one(iri=f"*{a_name}")
        b_ind = onto.search_one(iri=f"*{b_name}")
        if a_ind is None or b_ind is None:
            missing.append((row["anchor_course"], row["positive_course"]))
            continue
        hasSynergyWith[a_ind].append(b_ind)
        inserted += 1

    print(f"hasSynergyWith instances inserted: {inserted}")
    print(f"skipped (course individual not found): {len(missing)}")

    onto.save(file=OWL_FILE, format="rdfxml")
    print(f"saved: {OWL_FILE}")

    print("\nRunning HermiT reasoner...")
    try:
        with onto:
            sync_reasoner_hermit(infer_property_values=True)
        print("Reasoner finished: ontology is CONSISTENT.")
    except Exception as e:
        print("Reasoner FAILED:")
        print(f"  {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
