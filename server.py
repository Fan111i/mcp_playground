from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import os
import csv
from pathlib import Path

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CSV file path
CSV_FILE = os.path.join(os.path.dirname(__file__), "calculation_history.csv")

def init_csv():
    """Initialize CSV file with headers if it doesn't exist"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'operation', 'operand_a', 'operand_b', 'result', 'timestamp'])
        logging.info(f"Created CSV file: {CSV_FILE}")

def save_calculation(operation, a, b, result):
    """Save calculation to CSV file"""
    try:
        init_csv()

        # Get next ID
        next_id = 1
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                rows = list(reader)
                if rows:
                    next_id = int(rows[-1][0]) + 1

        # Append new calculation
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                next_id,
                operation,
                a,
                b,
                result,
                datetime.now().isoformat()
            ])

        logging.info(f"Saved: {operation}({a}, {b}) = {result}")
    except Exception as e:
        logging.error(f"CSV error: {e}")

def get_calculation_history(limit=10):
    """Get calculation history from CSV file"""
    try:
        init_csv()

        history = []
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Get last N rows
            for row in reversed(rows[-limit:]):
                history.append({
                    "id": int(row['id']),
                    "operation": row['operation'],
                    "operand_a": float(row['operand_a']),
                    "operand_b": float(row['operand_b']),
                    "result": float(row['result']),
                    "timestamp": row['timestamp']
                })

        return history
    except Exception as e:
        logging.error(f"CSV error: {e}")
        return []

# Define all math operation tools
tools = [
    {
        "name": "plus",
        "description": "Add two numbers together",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The first number"
                },
                "b": {
                    "type": "number",
                    "description": "The second number"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "sub",
        "description": "Subtract second number from first number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The first number"
                },
                "b": {
                    "type": "number",
                    "description": "The second number"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "mul",
        "description": "Multiply two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The first number"
                },
                "b": {
                    "type": "number",
                    "description": "The second number"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "div",
        "description": "Divide first number by second number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The dividend"
                },
                "b": {
                    "type": "number",
                    "description": "The divisor"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "history",
        "description": "Get calculation history from database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Number of recent calculations to retrieve (default: 10)"
                }
            }
        }
    }
]

@app.post("/mcp")
async def handle_mcp(request: Request):
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        # Handle tools list request
        if method == "tools/list":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "result": {
                    "tools": tools
                },
                "id": request_id
            })

        # Handle tool call request
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Get parameters
            a = arguments.get("a")
            b = arguments.get("b")

            # Validate parameters
            if a is None or b is None:
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameters: a and b"
                    },
                    "id": request_id
                }, status_code=400)

            # Execute the corresponding math operation
            if tool_name == "plus":
                result = a + b
                save_calculation("plus", a, b, result)
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Addition: {a} + {b} = {result}"
                            }
                        ]
                    },
                    "id": request_id
                })

            elif tool_name == "sub":
                result = a - b
                save_calculation("sub", a, b, result)
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Subtraction: {a} - {b} = {result}"
                            }
                        ]
                    },
                    "id": request_id
                })

            elif tool_name == "mul":
                result = a * b
                save_calculation("mul", a, b, result)
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Multiplication: {a} * {b} = {result}"
                            }
                        ]
                    },
                    "id": request_id
                })

            elif tool_name == "div":
                # Check if divisor is zero
                if b == 0:
                    return JSONResponse(content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Division by zero is not allowed"
                        },
                        "id": request_id
                    }, status_code=400)

                result = a / b
                save_calculation("div", a, b, result)
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Division: {a} / {b} = {result}"
                            }
                        ]
                    },
                    "id": request_id
                })

            elif tool_name == "history":
                limit = arguments.get("limit", 10)
                history = get_calculation_history(limit)
                history_text = "\n".join([
                    f"{h['id']}. {h['operation']}: {h['operand_a']} and {h['operand_b']} = {h['result']} ({h['timestamp']})"
                    for h in history
                ])
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Calculation History (last {limit}):\n{history_text}" if history else "No calculation history found"
                            }
                        ]
                    },
                    "id": request_id
                })

            else:
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    },
                    "id": request_id
                }, status_code=400)

        else:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            }, status_code=400)

    except Exception as e:
        logging.error(f"Error handling MCP request: {e}")
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": data.get("id") if 'data' in locals() else None
        }, status_code=500)

@app.get("/")
async def root():
    return {
        "message": "Calculator MCP Server",
        "mcp_version": "1.0",
        "capabilities": ["tools"],
        "available_tools": ["plus", "sub", "mul", "div", "history"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Separate endpoints for each math operation
@app.post("/plus")
async def plus_endpoint(request: Request):
    data = await request.json()
    a = data.get("a")
    b = data.get("b")

    if a is None or b is None:
        return JSONResponse(
            content={"error": "Missing required parameters: a and b"},
            status_code=400
        )

    result = a + b
    save_calculation("plus", a, b, result)
    return {
        "operation": "plus",
        "a": a,
        "b": b,
        "result": result
    }

@app.post("/sub")
async def sub_endpoint(request: Request):
    data = await request.json()
    a = data.get("a")
    b = data.get("b")

    if a is None or b is None:
        return JSONResponse(
            content={"error": "Missing required parameters: a and b"},
            status_code=400
        )

    result = a - b
    save_calculation("sub", a, b, result)
    return {
        "operation": "sub",
        "a": a,
        "b": b,
        "result": result
    }

@app.post("/mul")
async def mul_endpoint(request: Request):
    data = await request.json()
    a = data.get("a")
    b = data.get("b")

    if a is None or b is None:
        return JSONResponse(
            content={"error": "Missing required parameters: a and b"},
            status_code=400
        )

    result = a * b
    save_calculation("mul", a, b, result)
    return {
        "operation": "mul",
        "a": a,
        "b": b,
        "result": result
    }

@app.post("/div")
async def div_endpoint(request: Request):
    data = await request.json()
    a = data.get("a")
    b = data.get("b")

    if a is None or b is None:
        return JSONResponse(
            content={"error": "Missing required parameters: a and b"},
            status_code=400
        )

    if b == 0:
        return JSONResponse(
            content={
                "error": "Division by zero is not allowed",
                "operation": "div",
                "a": a,
                "b": b
            },
            status_code=400
        )

    result = a / b
    save_calculation("div", a, b, result)
    return {
        "operation": "div",
        "a": a,
        "b": b,
        "result": result
    }

@app.get("/history")
async def history_endpoint(limit: int = 10):
    """Get calculation history"""
    history = get_calculation_history(limit)
    return {
        "history": history,
        "count": len(history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8022)
