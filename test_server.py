import pytest
from fastapi.testclient import TestClient
from server import app
import os
import csv

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns server info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Calculator MCP Server"
        assert "available_tools" in data

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestMCPProtocol:
    """Test MCP protocol endpoints"""

    def test_tools_list(self):
        """Test MCP tools/list method"""
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
        assert len(data["result"]["tools"]) == 5

    def test_tool_call_plus(self):
        """Test MCP tools/call for addition"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "plus",
                    "arguments": {"a": 5, "b": 3}
                },
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "content" in data["result"]
        assert "8" in data["result"]["content"][0]["text"]

    def test_tool_call_sub(self):
        """Test MCP tools/call for subtraction"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "sub",
                    "arguments": {"a": 10, "b": 4}
                },
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "6" in data["result"]["content"][0]["text"]

    def test_tool_call_mul(self):
        """Test MCP tools/call for multiplication"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "mul",
                    "arguments": {"a": 6, "b": 7}
                },
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "42" in data["result"]["content"][0]["text"]

    def test_tool_call_div(self):
        """Test MCP tools/call for division"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "div",
                    "arguments": {"a": 20, "b": 4}
                },
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "5" in data["result"]["content"][0]["text"]

    def test_tool_call_div_by_zero(self):
        """Test division by zero returns error"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "div",
                    "arguments": {"a": 10, "b": 0}
                },
                "id": 1
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Division by zero" in data["error"]["message"]

    def test_tool_call_missing_params(self):
        """Test tool call with missing parameters"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "plus",
                    "arguments": {"a": 5}
                },
                "id": 1
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_unknown_tool(self):
        """Test calling unknown tool"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "unknown_tool",
                    "arguments": {"a": 1, "b": 2}
                },
                "id": 1
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data


class TestDirectEndpoints:
    """Test direct REST API endpoints"""

    def test_plus_endpoint(self):
        """Test direct addition endpoint"""
        response = client.post("/plus", json={"a": 10, "b": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15
        assert data["operation"] == "plus"

    def test_sub_endpoint(self):
        """Test direct subtraction endpoint"""
        response = client.post("/sub", json={"a": 10, "b": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 7

    def test_mul_endpoint(self):
        """Test direct multiplication endpoint"""
        response = client.post("/mul", json={"a": 4, "b": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 20

    def test_div_endpoint(self):
        """Test direct division endpoint"""
        response = client.post("/div", json={"a": 20, "b": 4})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5.0

    def test_div_endpoint_zero(self):
        """Test division by zero on direct endpoint"""
        response = client.post("/div", json={"a": 10, "b": 0})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_endpoint_missing_params(self):
        """Test direct endpoint with missing parameters"""
        response = client.post("/plus", json={"a": 5})
        assert response.status_code == 400


class TestHistory:
    """Test calculation history functionality"""

    def test_history_endpoint(self):
        """Test history endpoint returns data"""
        # First, make some calculations
        client.post("/plus", json={"a": 1, "b": 1})
        client.post("/mul", json={"a": 2, "b": 3})

        # Get history
        response = client.get("/history?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data

    def test_history_mcp_tool(self):
        """Test history via MCP protocol"""
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "history",
                    "arguments": {"limit": 5}
                },
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
