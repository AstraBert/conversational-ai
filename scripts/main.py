from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import gradio as gr
from workflow import agent_workflow
from llama_index.core.agent.workflow import (
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from pydantic import BaseModel, Field
import requests as rq

class UserInput(BaseModel):
    prompt: str = Field(description="Prompt from the user")

class AgentOutput(BaseModel):
    process: str = Field(description="The agent process")
    final_response: str = Field(description="The agent final response")

app = FastAPI(default_response_class=ORJSONResponse)

@app.post("/chat")
async def post(prompt: UserInput) -> AgentOutput:
    prmpt = prompt.prompt
    handler = agent_workflow.run(user_msg=prmpt)
    current_agent = None
    agent_process = ""
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            agent_process += f"\n{'='*50}"
            agent_process += f"🤖 Agent: {current_agent}"
            agent_process += f"{'='*50}\n"
        elif isinstance(event, AgentOutput):
            if event.response.content:
                agent_process += "📤 Output:" + event.response.content
            if event.tool_calls:
                agent_process += "🛠️  Planning to use tools:" + ', '.join([call.tool_name for call in event.tool_calls])
        elif isinstance(event, ToolCallResult):
            agent_process += f"🔧 Tool Result ({event.tool_name}):"
            agent_process += f"  Arguments: {event.tool_kwargs}"
            agent_process += f"  Output: {event.tool_output}"
        elif isinstance(event, ToolCall):
            agent_process += f"🔨 Calling Tool: {event.tool_name}"
            agent_process += f"  With arguments: {event.tool_kwargs}"
    state = await handler.ctx.get("state")
    fin_report = state["final_response"]
    return AgentOutput(process=agent_process, final_response=fin_report)

def reply(message, history):
    response = rq.post("http://localhost:8000/chat", json=UserInput(prompt=message).model_dump())
    res = response.json()
    process = res["process"]
    report = res["final_response"]
    text = f"<details>\n\t<summary><b>Agent Process</b></summary>\n\n{process}\n\n</details>\n\n{report}"
    return text

io = gr.ChatInterface(fn=reply, title="conversation.ai☕", theme=gr.Theme(primary_hue="rose",secondary_hue="emerald", font=["Arial", "sans-serif"]), examples=["Can you give me some information about Barack Obama?", "What are the latest news about AI?", "What is the weather now in San Francisco?"])
app = gr.mount_gradio_app(app, io, path="/app")
    