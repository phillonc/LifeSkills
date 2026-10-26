"""Reproduce DSDM planning and run the independently authored app acceptance suite.

Run from repository root: python -m examples.life_skills_delivery
This deterministic framework runs explicit handlers. It does not generate code.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from agents_framework import Crew, Task
from agents_framework.agents import business_analyst, project_manager, solution_developer, solution_tester
from agents_framework.tasks import build_prl_task, prioritise_task, plan_timebox_task

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "life-skills"

def implementation_evidence(agent, context):
    required = ["server.py", "learning.py", "content.json", "static/index.html", "static/app.js", "static/styles.css", "tests/test_http.py", "tests/test_learning.py", "scripts/browser-acceptance.cjs", "requirements.json"]
    missing = [name for name in required if not (APP / name).is_file()]
    if missing:
        raise RuntimeError("Missing implementation files: " + ", ".join(missing))
    return {"agent": agent.role, "files": {
        name: hashlib.sha256((APP / name).read_bytes()).hexdigest() for name in required}}

def acceptance_evidence(agent, context):
    if "implementation" not in context:
        raise RuntimeError("Implementation evidence required before QA")
    tests = list((APP / "tests").glob("test_*.py"))
    if not tests:
        raise RuntimeError("No independent acceptance tests found")
    run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(APP / "tests"), "-v"],
                         cwd=ROOT, text=True, capture_output=True, timeout=180)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return {"agent": agent.role, "command": "python -m unittest discover -s apps/life-skills/tests -v",
            "exit_code": run.returncode, "output": run.stdout + run.stderr}

def main():
    analyst, manager = business_analyst(), project_manager()
    developer, tester = solution_developer(), solution_tester()
    crew = Crew(agents=[analyst, manager, developer, tester], tasks=[
        build_prl_task(analyst), prioritise_task(analyst), plan_timebox_task(manager),
        Task("Record implementation", "Hash implementation files", developer, implementation_evidence, produces="implementation"),
        Task("Independent acceptance", "Run behavior and security checks", tester, acceptance_evidence, produces="acceptance"),
    ])
    requirements = [
        {"title": "Secure learner account lifecycle", "priority": "Must", "effort": 8},
        {"title": "Learning catalog, exercises and persistent progress", "priority": "Must", "effort": 8},
        {"title": "Budgeting and financial calculators", "priority": "Must", "effort": 5},
        {"title": "Goals, journal and achievements", "priority": "Should", "effort": 5},
        {"title": "Responsive accessible interface and themes", "priority": "Should", "effort": 5},
        {"title": "Data portability and account deletion", "priority": "Should", "effort": 4},
        {"title": "Native mobile clients", "priority": "Won't", "effort": 13},
        {"title": "AI coaches and marketplace integrations", "priority": "Won't", "effort": 21},
    ]
    result = crew.kickoff({"raw_requirements": requirements, "timebox_capacity": 35})
    print(json.dumps({"ok": result.ok, "products": result.context,
                      "errors": [{"task": r.task, "error": r.error} for r in result.errors]}, indent=2))
    return 0 if result.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
