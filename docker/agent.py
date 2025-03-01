from tools import search_news, search_wikipedia, get_weather, update_memory, get_memory, record_notes_on_info, record_notes_on_news, record_notes_on_weather, set_final_response, set_weather_location, set_news_query, set_wiki_page_name
from llama_index.core.agent.workflow import (
    ReActAgent,
)
from llama_index.llms.groq import Groq

f = open("/run/secrets/groq_key")
groq_api_key = f.read()
f.close()

llm = Groq(api_key=groq_api_key, model="llama-3.3-70b-versatile")

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
        "When the user asks a question and you think that you need to access the memory for that question, you must get information from the memory calling the 'get_memory' and passing a question that you want  to ask to the memory."
        "When the user asks a question that requires you to tell them the weather of a location, you must store the location to search the weather (using 'set_weather_location') and then hand off that task to the WeatherAgent"
        "When the user asks a question that requires you to gather the news about a topic, you must store the query to search the news (using 'set_news_query') and then hand off that task to the NewsSeachAgent."
        "When the user asks you for information about a topic, before activating the InfoSearchAgent you should:"
        "1. First of all, search your semantic cache for the piece of information the user is asking for, using the 'search_semantic_cache' tool and passing the user's question to it."
        "2a. If you get out an answer from this search, you should use the 'set_final_answer' tool to return the answer from the cache and close the workflow. Otherwise proceed to point 2b and beyond."
        "2b. If you DO NOT get out answer from searching the question, you must store the topic to search Wikipedia (using 'set_wiki_page_name') and then hand off that task to the InfoSearchAgent."
        "3. Once you got the answer from the InfoSearchAgent you activated, you MUST update the semantic cache using the 'update_semantic_cache' tool, passing the user's question and your final answer to that question."
        "4. When you think that you can answer to the user without further action, after having activated the necessary agents and tools, you MUST generate a final response (using the tool 'set_final_response' and passing the final response to it) and, once you successfully set the final response, close the workflow and return it to the user."
        "IMPORTANT INSTRUCTIONS:"
        "Using the 'set_final_response' is ALWAYS MANDATORY for you when you have the final answer to the user."
    ),
    llm=llm,
    tools=[update_memory, get_memory, search_semantic_cache, update_semantic_cache, set_news_query, set_wiki_page_name, set_weather_location, set_final_response],
    can_handoff_to=["NewsSearchAgent", "InfoSearchAgent", "WeatherAgent"],
)
