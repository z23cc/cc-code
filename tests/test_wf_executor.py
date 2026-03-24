"""Unit tests for cc_flow.wf_executor — workflow parsing, topo sort, chain export."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cc_flow.wf_executor import (
    _chain_to_workflow,
    _describe_node,
    _load_workflow,
    _topo_sort,
)


class TestTopoSort:
    """Test topological sort of workflow DAGs."""

    def test_linear_chain(self):
        nodes = [
            {"id": "a", "type": "start"},
            {"id": "b", "type": "subAgent"},
            {"id": "c", "type": "end"},
        ]
        connections = [
            {"from": "a", "to": "b"},
            {"from": "b", "to": "c"},
        ]
        ordered, node_map, adj = _topo_sort(nodes, connections)
        assert ordered == ["a", "b", "c"]
        assert len(node_map) == 3

    def test_parallel_nodes(self):
        nodes = [
            {"id": "s", "type": "start"},
            {"id": "x", "type": "subAgent"},
            {"id": "y", "type": "subAgent"},
            {"id": "e", "type": "end"},
        ]
        connections = [
            {"from": "s", "to": "x"},
            {"from": "s", "to": "y"},
            {"from": "x", "to": "e"},
            {"from": "y", "to": "e"},
        ]
        ordered, node_map, adj = _topo_sort(nodes, connections)
        assert ordered[0] == "s"
        assert ordered[-1] == "e"
        assert set(ordered[1:3]) == {"x", "y"}

    def test_empty_graph(self):
        ordered, node_map, adj = _topo_sort([], [])
        assert ordered == []

    def test_single_node(self):
        nodes = [{"id": "only", "type": "start"}]
        ordered, node_map, adj = _topo_sort(nodes, [])
        assert ordered == ["only"]

    def test_connection_with_condition(self):
        nodes = [{"id": "a", "type": "start"}, {"id": "b", "type": "end"}]
        connections = [{"from": "a", "to": "b", "condition": "yes"}]
        ordered, _, _ = _topo_sort(nodes, connections)
        assert ordered == ["a", "b"]

    def test_adjacency_list(self):
        nodes = [{"id": "a", "type": "start"}, {"id": "b", "type": "end"}]
        connections = [{"from": "a", "to": "b"}]
        _, _, adj = _topo_sort(nodes, connections)
        assert ("b", "") in adj["a"]


class TestDescribeNode:
    """Test node description generation."""

    def test_start_node(self):
        result = _describe_node({"type": "start", "data": {}})
        assert result["action"] == "start"

    def test_end_node(self):
        result = _describe_node({"type": "end", "data": {}})
        assert result["action"] == "end"

    def test_prompt_node(self):
        result = _describe_node({"type": "prompt", "data": {"prompt": "Hello user"}})
        assert result["action"] == "prompt"
        assert "Hello user" in result["instruction"]

    def test_subagent_node(self):
        result = _describe_node({
            "type": "subAgent",
            "data": {"name": "researcher", "description": "Find bugs", "prompt": "Look", "model": "opus"},
        })
        assert result["action"] == "agent"
        assert result["name"] == "researcher"
        assert "opus" in result["instruction"]

    def test_skill_node(self):
        result = _describe_node({
            "type": "skill",
            "data": {"name": "cc-review", "executionMode": "execute"},
        })
        assert result["action"] == "skill"
        assert "cc-review" in result["instruction"]

    def test_mcp_node(self):
        result = _describe_node({
            "type": "mcp",
            "data": {"serverId": "rp", "toolName": "search", "parameterValues": {"q": "test"}},
        })
        assert result["action"] == "mcp"
        assert result["server"] == "rp"

    def test_ask_user_question_node(self):
        result = _describe_node({
            "type": "askUserQuestion",
            "data": {
                "questionText": "Continue?",
                "options": [{"label": "Yes", "description": "proceed"}],
            },
        })
        assert result["action"] == "ask"
        assert result["question"] == "Continue?"
        assert "Yes" in result["options"]

    def test_if_else_node(self):
        result = _describe_node({
            "type": "ifElse",
            "data": {
                "evaluationTarget": "status",
                "branches": [{"label": "pass", "condition": "==ok"}],
            },
        })
        assert result["action"] == "branch"

    def test_unknown_node(self):
        result = _describe_node({"type": "custom_thing", "data": {}})
        assert result["action"] == "unknown"


class TestChainToWorkflow:
    """Test chain-to-workflow export."""

    def test_basic_export(self):
        chain_data = {
            "description": "Test chain",
            "skills": [
                {"skill": "/cc-brainstorm", "role": "ideate"},
                {"skill": "/cc-plan", "role": "plan"},
            ],
        }
        wf = _chain_to_workflow("test-chain", chain_data)
        assert wf["name"] == "test-chain"
        assert wf["description"] == "Test chain"
        assert len(wf["nodes"]) == 4  # start + 2 skills + end
        assert len(wf["connections"]) == 3

    def test_empty_chain(self):
        wf = _chain_to_workflow("empty", {"skills": []})
        assert len(wf["nodes"]) == 2  # start + end
        assert len(wf["connections"]) == 1

    def test_node_types(self):
        chain_data = {"skills": [{"skill": "/cc-review", "role": "review"}]}
        wf = _chain_to_workflow("review", chain_data)
        types = [n["type"] for n in wf["nodes"]]
        assert "start" in types
        assert "end" in types
        assert "subAgent" in types

    def test_connections_are_sequential(self):
        chain_data = {
            "skills": [
                {"skill": "/cc-a", "role": "a"},
                {"skill": "/cc-b", "role": "b"},
                {"skill": "/cc-c", "role": "c"},
            ],
        }
        wf = _chain_to_workflow("seq", chain_data)
        # Each connection should link prev -> next
        for conn in wf["connections"]:
            assert "from" in conn
            assert "to" in conn
            assert conn["from"] != conn["to"]

    def test_schema_version(self):
        wf = _chain_to_workflow("x", {"skills": []})
        assert wf["schemaVersion"] == "1.1.0"
        assert "id" in wf
        assert "createdAt" in wf


class TestLoadWorkflow:
    """Test workflow file loading."""

    def test_load_valid_file(self, tmp_path):
        wf_file = tmp_path / "test.json"
        wf_file.write_text(json.dumps({
            "name": "test",
            "nodes": [{"id": "s", "type": "start"}],
            "connections": [],
        }))
        data, path = _load_workflow(str(wf_file))
        assert data["name"] == "test"
        assert path == wf_file
