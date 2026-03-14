"""
Tests for the Task Planner (trunk/task-planner/planner.py).
"""
import pytest

from trunk.task_planner.planner import TaskPlanner


@pytest.fixture()
def planner():
    return TaskPlanner()


class TestDecompose:
    def test_verify_contribution_steps(self, planner):
        steps = planner.decompose("verify_contribution", {})
        assert len(steps) == 5
        assert steps[0]["step"] == 1

    def test_create_success_story_steps(self, planner):
        steps = planner.decompose("create_success_story", {})
        assert len(steps) == 4

    def test_portfolio_update_steps(self, planner):
        steps = planner.decompose("portfolio_update", {})
        assert len(steps) == 3

    def test_unknown_goal_returns_generic_plan(self, planner):
        steps = planner.decompose("unknown_goal", {})
        assert len(steps) >= 1


class TestCreateExecutionPlan:
    def test_returns_dict_with_goal(self, planner):
        plan = planner.create_execution_plan("verify_contribution", {"id": 1})
        assert plan["goal"] == "verify_contribution"
        assert plan["status"] == "planned"
        assert isinstance(plan["steps"], list)

    def test_total_steps_match(self, planner):
        plan = planner.create_execution_plan("portfolio_update", {})
        assert plan["total_steps"] == len(plan["steps"])
