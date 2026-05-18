import asyncio
import json
import logging
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
import requests

# 1. Logger Setup (hooks into main.py configuration automatically)
logger = logging.getLogger(__name__)

# 2. Normalized Configuration Parameters
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama-service:11434").rstrip('/')
OLLAMA_V1_API = f"{OLLAMA_BASE_URL}/v1"
MODEL_NAME = "qwen2.5:7b"

CONFIG_PATH = (Path(__file__).parent / "playwright_mcp_config.json").resolve()

# 3. Setup the external Playwright MCP process specification
mcp_server_params = StdioServerParameters(
    command="npx",
    args=[
        "-y", 
        "@playwright/mcp@latest", 
        "--headless", 
        "--config", str(CONFIG_PATH)
    ],
)


def ensure_ollama_model_pulled(ai_client: OpenAI) -> None:
    """
    Verifies the target LLM is available in Ollama. 
    If missing, handles the streaming layer pull natively.
    """
    logger.info(f"Verifying presence of local model entry: {MODEL_NAME}")
    
    # --- PHASE 1: THE CHECK ---
    try:
        # Fetch the raw response data object safely
        model_response = ai_client.models.list()
        
        # Safe Guard: Fallback to an empty list if .data is None or missing entirely
        raw_data = model_response.data if model_response.data is not None else []
        
        # Build the tracking array using our safe list reference
        available_models = [m.id for m in raw_data]
        
        if MODEL_NAME in available_models:
            logger.info(f"Model {MODEL_NAME} verified and hot in memory.")
            return
            
        logger.warning(f"Model {MODEL_NAME} not found. Initiating background cluster pull sequence...")
        
    except Exception as e:
        logger.critical(f"Failed to connect to Ollama to verify models: {e}")
        raise RuntimeError(f"Cannot verify model state due to connection error.") from e

    # --- PHASE 2: THE INSTALLATION ---
    try:
        pull_url = f"{OLLAMA_BASE_URL}/api/pull"
        
        with requests.post(pull_url, json={"name": MODEL_NAME}, stream=True) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Ollama cluster rejected pull request with status: {response.status_code}")
                
            logger.info(f"Downloading artifact layers for {MODEL_NAME}...")
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                status = json.loads(line.decode('utf-8'))
                
                if status.get("status") == "success":
                    logger.info(f"Successfully deployed and synchronized {MODEL_NAME}!")
                    return  

    except Exception as e:
        logger.critical(f"CRITICAL: Failed to download and install model {MODEL_NAME}: {e}")
        raise RuntimeError(f"Required model {MODEL_NAME} could not be installed.") from e


async def _scrape_with_mcp(url: str) -> str | None:
    """
    Connects to the Playwright MCP server, exposes the browser tools to local Qwen,
    and returns a summarized analysis of the webpage content.
    """
    ai_client = OpenAI(base_url=OLLAMA_V1_API, api_key="ollama")
    ensure_ollama_model_pulled(ai_client)
    
    logger.info("Spawning subprocess and establishing standard I/O communication streams...")
    try:
        async with stdio_client(mcp_server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # Retrieve tools exposed by MCP and parse cleanly to OpenAI Function patterns
                mcp_tools = await session.list_tools()
                openai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    } for tool in mcp_tools.tools
                ]

                messages = [{
                    "role": "user", 
                    "content": f"Navigate to {url}, wait for the page to finish loading, "
                               f"and provide a concise summary of the primary details on the page."
                               f"Keep the summary to under 1500 words and focus on key insights, main topics, and any notable information."
                }]
                
                logger.info("Requesting initial execution strategy matrix from agent engine...")
                response = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                    temperature=0.0
                )
                
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if not tool_calls:
                    logger.warning("Agent finalized tracking processing path without invoking browser actions.")
                    return response_message.content

                # Execute requested browser steps sequentially
                messages.append(response_message)
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing Browser Tool: '{tool_name}' -> Arguments: {tool_args}")
                    mcp_result = await session.call_tool(tool_name, arguments=tool_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(mcp_result.content)
                    })
                
                logger.info("Extracting synthesis output from context results...")
                final_response = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages
                )
                return final_response.choices[0].message.content

    except Exception:
        logger.exception(f"Playwright MCP engine loop threw a critical crash evaluating: {url}")
        return None
    

def scrape_with_mcp(url: str) -> str | None:
    """
    Synchronous wrapper that bridges external synchronous code 
    to the internal async Playwright logic.
    """
    logger.info(f"Starting Playwright MCP scraper for {url}")
    return asyncio.run(_scrape_with_mcp(url))