import os
import requests
from dotenv import load_dotenv
from langchain_ibm import ChatWatsonx
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

# 1. Tool definitions pointing to your local FastAPI router paths
@tool
def generate_image_tool(script_id: str, scene_index: int, style: str = "cinematic") -> str:
    """Generates an image asset for a specific scene index in a script."""
    payload = {
        "script_id": script_id,
        "scene_index": scene_index,
        "style": style,
        "language": "en"
    }
    response = requests.post("http://127.0.0.1:8000/api/generate/storyboard", json=payload)
    return response.json().get("image_url", "Failed to generate image")

@tool
def generate_audio_tool(prompt: str) -> str:
    """Generates an audio asset or soundscape from a descriptive text prompt."""
    response = requests.post("http://127.0.0.1:8000/api/generate/audio", json={"prompt": prompt})
    return response.json().get("audio_url", "Failed to generate audio")

tools = [generate_image_tool, generate_audio_tool]

# 2. Watsonx Granite model initialization
# Using ibm/granite-3-8b-instruct which is optimized for tool calling
# 2. Watsonx model initialization
llm = ChatWatsonx(
    model_id="meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    url="https://us-south.ml.cloud.ibm.com",
    project_id=os.environ.get("WATSONX_PROJECT_ID"),
    params={
        "decoding_method": "greedy",
        "temperature": 0.0,
        "max_new_tokens": 500
    }
)

# 3. Compile the ReAct agent executor
agent_executor = create_react_agent(llm, tools)

def run_orchestrator(user_prompt: str):
    """Execution function to be called by your primary application entry points."""
    response = agent_executor.invoke({"messages": [("human", user_prompt)]})
    return response