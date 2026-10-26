"""Tests for the core agent/task/crew orchestration."""

import pytest

from agents_framework import Agent, Crew, Task, Tool
from agents_framework.agents import business_analyst, project_manager
from agents_framework.tasks import (
    build_prl_task,
    plan_timebox_task,
    prioritise_task,
)


class _EchoTool(Tool):
    name = "echo"
    description = "Return its input doubled."

    def run(self, value):
        return value * 2


def test_agent_use_unknown_tool_returns_error_result():
    agent = Agent(role="Tester", goal="test", tools=[])
    result = agent.use("nope")
    assert result.ok is False
    assert "no tool" in result.error


def test_agent_use_tool_success():
    agent = Agent(role="Tester", goal="test", tools=[_EchoTool()])
    assert agent.use("echo", value=21).unwrap() == 42


def test_crew_threads_context_between_tasks():
    agent = Agent(role="Worker", goal="work", tools=[_EchoTool()])

    def make(value):
        produced = value

        def handler(_agent, ctx):
            base = ctx.get("seed", 1)
            return _agent.use("echo", value=base).unwrap()

        return Task(name=f"task-{produced}", description="", agent=agent, handler=handler, produces=produced)

    crew = Crew(agents=[agent], tasks=[make("a"), make("b")])
    result = crew.kickoff(inputs={"seed": 5})
    assert result.ok
    assert result.output("a") == 10
    assert result.output("b") == 10


def test_crew_records_task_failure_without_crashing():
    agent = Agent(role="Worker", goal="work", tools=[])

    def boom(_agent, _ctx):
        raise ValueError("kaboom")

    crew = Crew(agents=[agent], tasks=[Task("bad", "", agent, boom, produces="x")])
    result = crew.kickoff()
    assert result.ok is False
    assert result.errors[0].error == "kaboom"
    assert result.output("x") is None     # failed tasks do not write to context


def test_dsdm_foundations_flow_end_to_end():
    analyst = business_analyst()
    manager = project_manager()
    crew = Crew(
        agents=[analyst, manager],
        tasks=[
            build_prl_task(analyst),
            prioritise_task(analyst),
            plan_timebox_task(manager),
        ],
    )
    result = crew.kickoff(
        inputs={
            "raw_requirements": [
                {"title": "login", "priority": "M", "effort": 5},
                {"title": "dashboard", "priority": "S", "effort": 4},
                {"title": "pdf export", "priority": "C", "effort": 4},
            ],
            "timebox_capacity": 10,
        }
    )
    assert result.ok
    assert len(result.output("prl")) == 3
    assert result.output("moscow")["minimum_usable_subset"][0]["title"] == "login"
    plan = result.output("timebox_plan")
    assert {r["title"] for r in plan["deferred"]} == {"pdf export"}
