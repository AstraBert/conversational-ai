from tools import search_news, search_wikipedia, get_weather, update_memory, get_memory, record_notes_on_info, record_notes_on_news, record_notes_on_weather, set_final_response, set_weather_location, set_news_query, set_wiki_page_name
from llama_index.core.agent.workflow import (
    ReActAgent,
)
from llama_index.llms.anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

llm = Anthropic(api_key=os.getenv("anthropic_api_key"), model="claude-3-5-sonnet-20241022")

news_search_agent = ReActAgent(
    name="NewsSearchAgent",
    description="Useful for searching the web for news about a given topic and recording notes on the topic.",
    system_prompt=(
        "You are the NewsSearchAgent that can search the web for the latest news on a given topic and record notes on the topic."
        "Once notes are recorded and you are satisfied, you must hand off control to the ConversationalAgent to reply to the user about the news they asked for."
        "You must have at least some notes on the news about the given topic before handing off control to the ConversationalAgent."
        "Once you are done, you must handoff the control to the ConversationalAgent."
    ),
    llm=llm,
    tools=[search_news, record_notes_on_news],
    can_handoff_to=["ConversationalAgent"],
)

info_search_agent = ReActAgent(
    name="InfoSearchAgent",
    description="Useful for searching Wikipedia for information about a given topic",
    system_prompt=(
        "You are the InfoSearchAgent that can search Wikipedia for information about a given topic and you must record notes about that information."
        "Once notes are recorded and you are satisfied, you must hand off control to the ConversationalAgent to reply to the user about the information they asked for."
        "You must have at least some notes on the info about the given topic before handing off control to the ConversationalAgent."
        "Once you are done, you must handoff the control to the ConversationalAgent."
    ),
    llm=llm,
    tools=[search_wikipedia, record_notes_on_info],
    can_handoff_to=["ConversationalAgent"],
)

weather_agent = ReActAgent(
    name="WeatherAgent",
    description="Useful for getting the weather of a location",
    system_prompt=(
        "You are the WeatherAgent that can search for the weather of a given location and you must record notes about the weather of that location."
        "Once notes are recorded and you are satisfied, you must hand off control to the ConversationalAgent to reply to the user about the weather in the location they asked for."
        "You must have at least some notes on the weather about the given location before handing off control to the ConversationalAgent."
        "Once you are done, you must handoff the control to the ConversationalAgent."
    ),
    llm=llm,
    tools=[get_weather, record_notes_on_weather],
    can_handoff_to=["ConversationalAgent"],
)


conversational_agent = ReActAgent(
    name="ConversationalAgent",
    description="Useful for chatting with the user, getting memories of the previous conversation and update the memory about it",
    system_prompt=(
        "You are the ConversationalAgent. Your task is to chat with the user and store, in memory, important information that are given by the user to you: you must store the information in memory only when you think it is important and give it an importance score from 0 to 100."
        "When the user asks a question and you think that you need to access the memory for that question, you must get information from the memory."
        "When the user asks a question that requires you to gather information about a topic, you must hand off that task to the InfoSearchAgent."
        "When the user asks a question that requires you to gather the news about a topic, you must hand off that task to the NewsSeachAgent."
        "When the user asks a question that requires you to tell them the weather of a location, you must hand off that task to the WeatherAgent"
        "You must have at least some notes on the weather about the given location before handing off control to the ConversationalAgent."
        "After having activated the necessary agents and tools, you must generate a final response to return to the user."
    ),
    llm=llm,
    tools=[update_memory, get_memory, set_news_query, set_wiki_page_name, set_weather_location, set_final_response],
    can_handoff_to=["NewsSearchAgent", "InfoSearchAgent", "WeatherAgent"],
)
