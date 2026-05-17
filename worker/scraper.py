import asyncio
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Read the local Ollama address configured in docker-compose
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama-service:11434")

config_path = str((Path(__file__).parent.joinpath("playwright-mcp-config.json")).resolve())

# Configure the system to launch the external Playwright MCP server process
mcp_server_params = StdioServerParameters(
    command="npx",
    args=["-y", 
          "@playwright/mcp@latest", 
          "--headless", 
          "--config", config_path],
)

async def run_playwright_check(url: str) -> str | None:
    """
    Spins up Playwright, navigates to the URL, and returns the verified page title.
    """
    async with async_playwright() as p:
        # Launch a headless browser instance
        print(f'[PLAYWRIGHT] Launching headless browser for {url}', flush=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f'[PLAYWRIGHT] Launching browser to navigate to {url}', flush=True)
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Fetch the page title to prove it worked
            page_title = await page.title()
            print(f'[PLAYWRIGHT] Successfully verified page title: "{page_title}"', flush=True)
            return page_title
            
        except Exception as e:
            print(f'[PLAYWRIGHT ERROR] Failed to load {url}: {e}', flush=True)
            return None
            
        finally:
            # Clean up browser processes
            await browser.close()

def get_url_title(url: str) -> str | None:
    """
    Synchronous wrapper that bridges external synchronous code 
    to the internal async Playwright logic.
    """
    print(f'[PLAYWRIGHT] Starting Playwright check for {url}', flush=True)
    return asyncio.run(run_playwright_check(url))

async def run_mcp_scrape(target_url: str) -> str | None:
    """
    Connects to the Playwright MCP server, exposes the browser tools to local Qwen,
    and returns a summarized analysis of the webpage content.
    """
    # 1. Properly format and clean up the incoming Ollama URL string
    raw_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama-service:11434")
    ollama_base = raw_url.rstrip('/')
    OLLAMA_URL = f"{ollama_base}/v1"
    
    # Initialize the client pointing to our local Ollama container
    ai_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
    
    # --- AUTOMATIC MODEL PULL LAYER ---
    model_name = "qwen2.5:7b"
    print(f"[SCRAPER] Verifying that {model_name} is available on Ollama...", flush=True)
    try:
        # Get the list of models currently loaded in Ollama
        available_models = [m.id for m in ai_client.models.list().data]
        
        if model_name not in available_models:
            print(f"[OLLAMA] {model_name} not found locally. Initiating automatic pull...", flush=True)
            
            # Make a direct call to Ollama's native streaming pull endpoint
            import requests
            req_url = f"{ollama_base}/api/pull"
            
            # Using stream=True ensures we don't time out during a large download
            with requests.post(req_url, json={"name": model_name}, stream=True) as response:
                if response.status_code == 200:
                    print(f"[OLLAMA] Downloading layers for {model_name}...", flush=True)
                    # Iterate over the response lines to keep the connection alive
                    for line in response.iter_lines():
                        if line:
                            status = json.loads(line.decode('utf-8'))
                            # Optional: print progress status updates if you want verbose logs
                            if status.get("status") == "success":
                                print(f"[OLLAMA] Successfully pulled {model_name}!", flush=True)
                else:
                    print(f"[OLLAMA ERROR] Pull failed with status code: {response.status_code}", flush=True)
        else:
            print(f"[SCRAPER] {model_name} verified and ready to handle tasks.", flush=True)
            
    except Exception as e:
        print(f"[SCRAPER WARNING] Could not automatically verify or pull model: {e}", flush=True)
    # ----------------------------------
    
    print(f"[SCRAPER] Initializing Playwright MCP subprocess...", flush=True)
    
    try:
        # Establish the standard I/O communication streams with the MCP server
        async with stdio_client(mcp_server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Complete the protocol handshake
                await session.initialize()
                
                # Discover what browser tools are exposed by the MCP server
                mcp_tools = await session.list_tools()
                
                # Format the tools into the strict OpenAI schema Qwen expects
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

                # High-level prompt giving the agent full structural autonomy
                prompt = (
                    f"Navigate to {target_url}, wait for the page to finish loading, "
                    f"and provide a concise summary of the primary details on the page."
                )
                messages = [{"role": "user", "content": prompt}]
                
                print(f"[SCRAPER] Requesting tool execution path from Qwen...", flush=True)
                
                # First LLM Call: Ask Qwen which browser tools it needs to achieve the goal
                response = ai_client.chat.completions.create(
                    model=model_name,  # Replaced hardcoded string with our verified variable
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                    temperature=0.0  # Keep it deterministic for reliable tool calling
                )
                
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                # If Qwen decided it needs to use the browser (e.g., calling playwright_navigate)
                if tool_calls:
                    messages.append(response_message)
                    
                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"[AGENT DECISION] Qwen invoked tool: '{tool_name}' with args: {tool_args}", flush=True)
                        
                        # Physically execute the browser action inside the container
                        mcp_result = await session.call_tool(tool_name, arguments=tool_args)
                        
                        # Feed the raw visual/textual output of the browser back into the model's history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(mcp_result.content)
                        })
                    
                    print(f"[SCRAPER] Generating final summary from browser context...", flush=True)
                    
                    # Second LLM Call: Qwen reads the browser's output and extracts the final text
                    final_response = ai_client.chat.completions.create(
                        model=model_name,
                        messages=messages
                    )
                    
                    return final_response.choices[0].message.content
                else:
                    print("[SCRAPER WARNING] Qwen did not invoke any browser tools.", flush=True)
                    return response_message.content

    except Exception as e:
        print(f"[SCRAPER ERROR] MCP execution failed for {target_url}: {e}", flush=True)
        return None
    
def get_llm_title(url: str) -> str | None:
    """
    Synchronous wrapper that bridges external synchronous code 
    to the internal async Playwright logic.
    """
    print(f'[PLAYWRIGHT] Starting Playwright check for {url}', flush=True)
    return asyncio.run(run_mcp_scrape(url))