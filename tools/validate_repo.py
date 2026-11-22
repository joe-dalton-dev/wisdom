"""Basic repository checks run by CI: YAML and JSON files parse, codebook IDs are unique,
and every theme points at a defined domain."""
import json
import pathlib
import sys

import yaml

root = pathlib.Path(__file__).resolve().parent.parent
errors = []

for path in list(root.glob("codebook/*.yaml")) + list(root.glob("agents/*.yaml")):
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        errors.append(f"{path.name}: {e}")

for path in root.glob("schemas/*.json"):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{path.name}: {e}")

themes = yaml.safe_load((root / "codebook/themes.yaml").read_text(encoding="utf-8"))
topics = yaml.safe_load((root / "codebook/topics.yaml").read_text(encoding="utf-8"))
domains = {d["id"] for d in themes["domains"]}
ids = [t["id"] for t in themes["themes"]] + [t["id"] for t in topics["topics"]]
dupes = {i for i in ids if ids.count(i) > 1}
if dupes:
    errors.append(f"duplicate label IDs: {sorted(dupes)}")
for t in themes["themes"]:
    if t["domain"] not in domains:
        errors.append(f"{t['id']} points at unknown domain {t['domain']}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"ok: {len(themes['themes'])} themes, {len(topics['topics'])} topics, {len(domains)} domains")
