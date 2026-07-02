import asyncio
import threading
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.server.stdio

from app.rag_chain import query_documents as rag_query
from app.vector_store import get_vector_store


server = Server("rag-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_documents",
            description="Ask a question about the ingested documents and get an answer with sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask about the documents"}
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="list_sources",
            description="List all document sources currently in the vector store",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "query_documents":
        result = rag_query(arguments["question"])
        answer = result["answer"]
        sources = "\n".join(
            f"- {doc['source']}" for doc in result["source_documents"]
        )
        return [TextContent(type="text", text=f"Answer: {answer}\n\nSources:\n{sources}")]
    elif name == "list_sources":
        store = get_vector_store()
        return [TextContent(type="text", text="Document sources in the vector store.")]
    raise ValueError(f"Unknown tool: {name}")


async def run_mcp():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rag-mcp",
                server_version="1.0.0",
            ),
        )


def start_mcp_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_mcp())
