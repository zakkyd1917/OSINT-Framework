#!/usr/bin/env python3
"""Export a conservative CSV review queue; no network or JavaScript."""
import csv
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"public"/"arf.json").read_text(encoding="utf-8"))
observed=ROOT/"evidence"/"state.json"
state=json.loads(observed.read_text(encoding="utf-8")) if observed.exists() else {}
path=ROOT/"evidence"/"review_queue.csv"

def walk(node, parents=()):
    if isinstance(node.get("children"),list):
        for child in node["children"]:
            yield from walk(child,parents+(node.get("name",""),))
    elif node.get("url"):
        yield node, " / ".join(parents[1:])

columns=["catalogId","name","category","url","status","claimedStatus",
         "accessCost","claimedPricing","registration","payment","humanEffort",
         "requiresJavaScript","jsReview","lastCheckedAt","lastObservation",
         "confidence","editorialCaution"]
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("w",encoding="utf-8",newline="") as fp:
    writer=csv.DictWriter(fp,fieldnames=columns)
    writer.writeheader()
    for row,category in walk(data):
        access=row.get("access") or {}
        js=row.get("jsAssessment") or {}
        stateRow=state.get(row["url"],{})
        writer.writerow({
            "catalogId":row.get("catalogId"),"name":row.get("name"),
            "category":category,"url":row.get("url"),
            "status":row.get("status"),"claimedStatus":row.get("claimedStatus"),
            "accessCost":access.get("costModel"),"claimedPricing":row.get("claimedPricing"),
            "registration":access.get("registration"),
            "payment":access.get("payment"),"humanEffort":access.get("humanEffort"),
            "requiresJavaScript":js.get("requiresJavaScript"),
            "jsReview":js.get("review"),
            "lastCheckedAt":stateRow.get("lastCheckedAt"),
            "lastObservation":stateRow.get("lastObservation"),
            "confidence":access.get("confidence"),
            "editorialCaution":row.get("editorialCaution","")
        })
print(path)
