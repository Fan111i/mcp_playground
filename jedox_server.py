from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Jedox MCP Server", version="1.0.0")

# ========================================
# Jedox Configuration
# ========================================
# Load from environment variables for security
JEDOX_SERVER = os.getenv("JEDOX_SERVER", "https://your-jedox-server.com")
JEDOX_TOKEN = os.getenv("JEDOX_TOKEN", "your_access_token_here")

# Request headers for Jedox API
JEDOX_HEADERS = {
    "Authorization": f"Bearer {JEDOX_TOKEN}",
    "Content-Type": "application/json"
}

# ========================================
# Jedox API Helper Functions
# ========================================

def jedox_login(username: str, password: str) -> Dict[str, str]:
    """
    Authenticate with Jedox and get access token

    Args:
        username: Jedox username
        password: Jedox password

    Returns:
        Dict with access_token and refresh_token
    """
    try:
        url = f"{JEDOX_SERVER}/api/auth/login"
        response = requests.post(
            url,
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully logged in as {username}")
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in", 3600)
        }
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return {"error": str(e)}


def list_databases() -> List[Dict[str, str]]:
    """
    List all available Jedox databases

    Returns:
        List of databases with name and id
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases"
        response = requests.get(url, headers=JEDOX_HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Retrieved {len(data.get('databases', []))} databases")
        return data.get("databases", [])
    except Exception as e:
        logger.error(f"Failed to list databases: {str(e)}")
        return []


def list_cubes(database: str) -> List[Dict[str, str]]:
    """
    List all cubes in a database

    Args:
        database: Database name

    Returns:
        List of cubes with name and id
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases/{database}/cubes"
        response = requests.get(url, headers=JEDOX_HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Retrieved {len(data.get('cubes', []))} cubes from {database}")
        return data.get("cubes", [])
    except Exception as e:
        logger.error(f"Failed to list cubes: {str(e)}")
        return []


def list_dimensions(database: str) -> List[Dict[str, Any]]:
    """
    List all dimensions in a database

    Args:
        database: Database name

    Returns:
        List of dimensions
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases/{database}/dimensions"
        response = requests.get(url, headers=JEDOX_HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Retrieved {len(data.get('dimensions', []))} dimensions")
        return data.get("dimensions", [])
    except Exception as e:
        logger.error(f"Failed to list dimensions: {str(e)}")
        return []


def read_jedox_cell(database: str, cube: str, coordinates: List[str]) -> Any:
    """
    Read a single cell value from Jedox Cube

    Args:
        database: Database name
        cube: Cube name
        coordinates: List of coordinate values [Year, Region, Measure, ...]

    Returns:
        Cell value (number, string, or None)
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases/{database}/cubes/{cube}/cells"
        payload = {"coordinates": [coordinates]}

        response = requests.post(url, json=payload, headers=JEDOX_HEADERS)
        response.raise_for_status()
        data = response.json()

        if data.get("cells") and len(data["cells"]) > 0:
            cell_value = data["cells"][0].get("value")
            logger.info(f"Read cell {coordinates}: {cell_value}")
            return cell_value

        logger.warning(f"No data found for coordinates: {coordinates}")
        return None

    except Exception as e:
        logger.error(f"Failed to read cell: {str(e)}")
        return {"error": str(e)}


def write_jedox_cell(database: str, cube: str, coordinates: List[str], value: Any) -> Dict[str, str]:
    """
    Write a value to a Jedox Cube cell

    Args:
        database: Database name
        cube: Cube name
        coordinates: List of coordinate values
        value: Value to write (number or string)

    Returns:
        Status dict
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases/{database}/cubes/{cube}/cells/write"
        payload = {
            "cells": [{
                "coordinates": coordinates,
                "value": value
            }]
        }

        response = requests.post(url, json=payload, headers=JEDOX_HEADERS)
        response.raise_for_status()

        logger.info(f"Wrote value {value} to {coordinates}")
        return {
            "status": "success",
            "message": f"Successfully wrote {value} to cell {coordinates}"
        }

    except Exception as e:
        logger.error(f"Failed to write cell: {str(e)}")
        return {"status": "error", "error": str(e)}


def read_jedox_range(database: str, cube: str, coordinates_list: List[List[str]]) -> List[Dict]:
    """
    Read multiple cells from Jedox Cube

    Args:
        database: Database name
        cube: Cube name
        coordinates_list: List of coordinate arrays

    Returns:
        List of cell data
    """
    try:
        url = f"{JEDOX_SERVER}/api/databases/{database}/cubes/{cube}/cells"
        payload = {"coordinates": coordinates_list}

        response = requests.post(url, json=payload, headers=JEDOX_HEADERS)
        response.raise_for_status()
        data = response.json()

        cells = data.get("cells", [])
        logger.info(f"Read {len(cells)} cells")
        return cells

    except Exception as e:
        logger.error(f"Failed to read range: {str(e)}")
        return []


# ========================================
# MCP Tools Definition
# ========================================

tools = [
    {
        "name": "jedox_list_databases",
        "description": "List all available Jedox databases",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "jedox_list_cubes",
        "description": "List all cubes in a specific Jedox database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name"
                }
            },
            "required": ["database"]
        }
    },
    {
        "name": "jedox_list_dimensions",
        "description": "List all dimensions in a Jedox database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name"
                }
            },
            "required": ["database"]
        }
    },
    {
        "name": "jedox_read_cell",
        "description": "Read a single cell value from a Jedox Cube",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name"
                },
                "cube": {
                    "type": "string",
                    "description": "Cube name"
                },
                "coordinates": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Cell coordinates, e.g., ['2024', 'Beijing', 'Revenue']"
                }
            },
            "required": ["database", "cube", "coordinates"]
        }
    },
    {
        "name": "jedox_write_cell",
        "description": "Write a value to a Jedox Cube cell (⚠️ This will modify the database)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name"
                },
                "cube": {
                    "type": "string",
                    "description": "Cube name"
                },
                "coordinates": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Cell coordinates"
                },
                "value": {
                    "type": "number",
                    "description": "Value to write"
                }
            },
            "required": ["database", "cube", "coordinates", "value"]
        }
    },
    {
        "name": "jedox_read_range",
        "description": "Read multiple cells from a Jedox Cube",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "cube": {"type": "string"},
                "coordinates_list": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "List of coordinate arrays"
                }
            },
            "required": ["database", "cube", "coordinates_list"]
        }
    }
]

# ========================================
# MCP Endpoint
# ========================================

@app.post("/mcp")
async def handle_mcp(request: Request):
    """
    Main MCP endpoint - handles all MCP protocol requests

    Supported methods:
    - tools/list: Return available tools
    - tools/call: Execute a specific tool
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", 1)

        # ========== MCP Method: tools/list ==========
        if method == "tools/list":
            logger.info("Returning tools list")
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            })

        # ========== MCP Method: tools/call ==========
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            logger.info(f"Calling tool: {tool_name} with args: {arguments}")

            # --- Tool: jedox_list_databases ---
            if tool_name == "jedox_list_databases":
                databases = list_databases()
                result_text = "Available Jedox Databases:\n"
                for db in databases:
                    result_text += f"- {db.get('name')} (ID: {db.get('id')})\n"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Tool: jedox_list_cubes ---
            elif tool_name == "jedox_list_cubes":
                database = arguments.get("database")
                cubes = list_cubes(database)
                result_text = f"Cubes in database '{database}':\n"
                for cube in cubes:
                    result_text += f"- {cube.get('name')} (ID: {cube.get('id')})\n"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Tool: jedox_list_dimensions ---
            elif tool_name == "jedox_list_dimensions":
                database = arguments.get("database")
                dimensions = list_dimensions(database)
                result_text = f"Dimensions in database '{database}':\n"
                for dim in dimensions:
                    result_text += f"- {dim.get('name')}\n"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Tool: jedox_read_cell ---
            elif tool_name == "jedox_read_cell":
                database = arguments.get("database")
                cube = arguments.get("cube")
                coordinates = arguments.get("coordinates")

                cell_value = read_jedox_cell(database, cube, coordinates)

                if isinstance(cell_value, dict) and "error" in cell_value:
                    result_text = f"Error: {cell_value['error']}"
                else:
                    result_text = f"Cell value at {coordinates}:\n{cell_value}"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Tool: jedox_write_cell ---
            elif tool_name == "jedox_write_cell":
                database = arguments.get("database")
                cube = arguments.get("cube")
                coordinates = arguments.get("coordinates")
                value = arguments.get("value")

                result = write_jedox_cell(database, cube, coordinates, value)

                if result.get("status") == "success":
                    result_text = f"Success: {result['message']}"
                else:
                    result_text = f"Error: {result.get('error')}"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Tool: jedox_read_range ---
            elif tool_name == "jedox_read_range":
                database = arguments.get("database")
                cube = arguments.get("cube")
                coordinates_list = arguments.get("coordinates_list")

                cells = read_jedox_range(database, cube, coordinates_list)

                result_text = f"Read {len(cells)} cells:\n"
                for cell in cells:
                    coords = cell.get("coordinates", [])
                    value = cell.get("value")
                    result_text += f"- {coords}: {value}\n"

                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": result_text
                        }]
                    },
                    "id": request_id
                })

            # --- Unknown Tool ---
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    },
                    "id": request_id
                })

        # ========== Unknown Method ==========
        else:
            logger.warning(f"Unknown method: {method}")
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                },
                "id": request_id
            })

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": 1
        })


# ========================================
# Health Check & Info Endpoints
# ========================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Jedox MCP Server",
        "version": "1.0.0",
        "description": "MCP Server for Jedox API integration",
        "endpoints": {
            "/mcp": "MCP protocol endpoint",
            "/health": "Health check",
            "/tools": "List available tools"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "jedox_server": JEDOX_SERVER,
        "token_configured": bool(JEDOX_TOKEN and JEDOX_TOKEN != "your_access_token_here")
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    return {"tools": tools}


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Starting Jedox MCP Server")
    print("=" * 60)
    print(f"Jedox Server: {JEDOX_SERVER}")
    print(f"Token configured: {bool(JEDOX_TOKEN and JEDOX_TOKEN != 'your_access_token_here')}")
    print("\nAvailable tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    print("\nEndpoints:")
    print("  - http://localhost:8023/mcp (MCP protocol)")
    print("  - http://localhost:8023/health (Health check)")
    print("  - http://localhost:8023/tools (List tools)")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8023)
