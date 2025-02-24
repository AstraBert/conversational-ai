from llama_index.core.agent.workflow import AgentWorkflow
from agent import news_search_agent, info_search_agent, weather_agent, conversational_agent
import uuid

username = str(uuid.uuid4())

agent_workflow = AgentWorkflow(
    agents=[conversational_agent, news_search_agent, info_search_agent, weather_agent],
    root_agent=conversational_agent.name,
    initial_state={
        "notes_on_news": {},
        "info": {},
        "weather": {},
        "username": username,
        "final_response": "",
        "weather_location": "",
        "news_query": "",
        "wikipedia_page_name": "",
    },
)


