"""MCP (Model Context Protocol) layer for DEMON."""

from DEMON.mcp.client import MCPClient
from DEMON.mcp.protocol import MCPError, MCPNotification, MCPRequest, MCPResponse
from DEMON.mcp.server import MCPServer
from DEMON.mcp.transport import (
    InProcessTransport,
    MCPTransport,
    SSETransport,
    StdioTransport,
    StreamableHTTPTransport,
)

__all__ = [
    "MCPClient",
    "MCPError",
    "MCPNotification",
    "MCPRequest",
    "MCPResponse",
    "MCPServer",
    "MCPTransport",
    "InProcessTransport",
    "SSETransport",
    "StdioTransport",
    "StreamableHTTPTransport",
]
