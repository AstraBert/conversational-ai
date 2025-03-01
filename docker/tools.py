from wikipediaapi import Wikipedia
from pydantic import BaseModel, Field
from llama_index.core.workflow import Context
import pgsql
import python_weather
from tavily import AsyncTavilyClient
from llama_index.llms.groq import Groq
from llama_index.core.llms import ChatMessage
from semantic import AsyncQdrantClient, AsyncSemanticCache, MistralAIEmbedding

f = open("/run/secrets/groq_key")
groq_api_key = f.read()
f.close()
f = open("/run/secrets/tavily_key")
tavily_api_key = f.read()
f.close()
f = open("/run/secrets/mistral_key")
mistral_api_key = f.read()
f.close()

wclient = python_weather.Client(unit=python_weather.IMPERIAL)
connection = pgsql.Connection(("postgres",5432), user="localhost", password="admin", database="postgres")
connection.execute("CREATE TABLE IF NOT EXISTS memory (username TEXT, message TEXT, importance INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
llm_query = Groq(api_key=groq_api_key, model="llama-3.1-8b-instant")

client = AsyncTavilyClient(api_key=tavily_api_key)

wiki = Wikipedia(user_agent='MyProjectName (merlin@example.com)', language='en')

qc = AsyncQdrantClient(host="qdrant", port=6333)
embed_model = MistralAIEmbedding(api_key=mistral_api_key)
semantic_cache = AsyncSemanticCache(client=qc, embedding_model=embed_model)

class MemoryPiece(BaseModel):
    username: str = Field(description="Username")
    memory: str = Field(description="Memory piece")
    importance: int = Field(description="Importance of the memory piece")

async def search_semantic_cache(ctx: Context, question: str) -> str:
    """Useful to search the semantic cache for the answer to a user's question"""
    state = await ctx.get("state")
    res = await semantic_cache.search_cache(question=question)
    if not res:
        return "There is no cache information about the question"
    else:
        state["final_response"] = res
        await ctx.set("state", state)
        return res

async def update_semantic_cache(ctx: Context, question: str, answer: str):
    """Useful to update the semantic cache with the answer to a user's question"""
    state = await ctx.get("state")
    state["final_response"] = answer
    await ctx.set("state", state)
    cp = await semantic_cache.create_cache_piece(question, answer)
    if cp:
        uc = await semantic_cache.update_cache()
        if uc:
            return "Cache updated successfully"
        else:
            return "Cache was not updated due to an error..."
    else: 
        return "Cache was not updated due to an error..."

async def search_news(ctx: Context) -> str:
    """Useful to search the web about news in the last week about a specific topic"""
    current_state = await ctx.get("state")
    query = current_state["news_query"]
    response = await client.search(
        query=query,
        topic="news",
        time_range="w",
        include_answer="basic"
    )
    answer = response.get("answer", "No overall summary")
    results = [f"### {res['title']}\n\n### Content\n\n{res['content']}" for res in response["results"]]
    txt = "\n\n".join(results)+"### Overall summary"+answer
    return txt

async def search_wikipedia(ctx: Context) -> str:
    """Useful for searching Wikipedia pages for information"""
    current_state = await ctx.get("state")
    page_name = current_state["wikipedia_page_name"]
    pg = wiki.page(page_name)
    if pg.exists():
        summary = pg.summary
        title = pg.title
        url = pg.fullurl
        return f"## {title}\n\n{summary}\n\nURL: {url}"
    else:
        return f"## PAGE NOT FOUND"

async def record_notes_on_info(ctx: Context, notes: str, notes_title: str) -> str:
    """Useful for recording notes on information retrieved about a given topic. Your input should be information with a title to save the information under."""
    current_state = await ctx.get("state")
    if "info" not in current_state:
        current_state["info"] = {}
    current_state["info"][notes_title] = notes
    await ctx.set("state", current_state)
    return "Info recorded."

async def record_notes_on_news(ctx: Context, notes: str, notes_title: str) -> str:
    """Useful for recording notes on news about a given topic. Your input should be notes on news with a title to save the notes under."""
    current_state = await ctx.get("state")
    if "notes_on_news" not in current_state:
        current_state["notes_on_news"] = {}
    current_state["notes_on_news"][notes_title] = notes
    await ctx.set("state", current_state)
    return "Notes on news recorded."

async def record_notes_on_weather(ctx: Context, location: str, weather_description: str) -> str:
    """Useful for recording notes about the weather in a specific location. You should provide the location and a description of the weather in that location."""
    current_state = await ctx.get("state")
    if "weather" not in current_state:
        current_state["weather"] = {}
    current_state["weather"][location] = weather_description
    await ctx.set("state", current_state)
    return "Weather recorded."

async def get_weather(ctx: Context) -> str:
    """Useful for getting today's weather"""
    current_state = await ctx.get("state")
    location = current_state["weather_location"]
    weather = await wclient.get(location, unit=python_weather.METRIC)
    daytime = weather.datetime
    day, month, year, hour, minute = daytime.day, daytime.month, daytime.year, daytime.hour, daytime.minute
    temperature = weather.temperature
    humidity = weather.humidity
    precipitations = weather.precipitation
    wind_speed = weather.wind_speed
    text = f"### Weather for {location}\n\n**Current time**: {hour}:{minute} - {month}/{day}/{year}\n\n**Temperature**: {temperature} °C\n\n**Humidity**: {humidity}%\n\n**Precipitations**: {precipitations} mm\n\n**Wind Speed**: {wind_speed} km/h"
    return text

async def update_memory(ctx: Context, memory_info: str = Field(description="Important information to store into memory"), importance_score: int = Field(description="Importance score as an integer between 0 and 100 defining how important is that piece of memory")) -> str:
    """Useful for updating the memory"""
    current_state = await ctx.get("state")
    username = current_state["username"]
    true_message = memory_info.replace("'", "''")
    try:
        connection.execute(f"INSERT INTO memory (username, message, importance) VALUES ('{username}', '{true_message}', {importance_score})")
    except Exception as e:
        return "Failed"
    else:
        return "Success"

async def get_memory(ctx: Context, question: str) -> str:
    """Useful to get the memory about the conversation starting from a specific question"""
    current_state = await ctx.get("state")
    username = current_state["username"]
    memories = connection(f"SELECT * FROM MEMORY WHERE username = '{username}' ORDER BY importance DESC, created_at DESC LIMIT 30;")
    mems_to_return = []
    for m in memories:
        mems_to_return.append(m)
    if len(mems_to_return) == 0:
        return "There is no memory content"
    else:
        mems_to_return = [MemoryPiece(memory=m.message, username=m.username, importance=m.importance) for m in mems_to_return]
        messages = [ChatMessage.from_str(content = m.memory + f"\nThis message is of importance: {m.importance}/100", role="assistant") for m in mems_to_return]
        messages.append(ChatMessage.from_str("Based on the information that you have, you should answer this question:\n\n"+question, role="user"))
        response = await llm_query.achat(messages=messages)
        return response.message.blocks[0].text
    
async def set_final_response(ctx: Context, final_response: str) -> str:
    """Useful to create the final response to the user prompt. You should pass the final response"""
    current_state = await ctx.get("state")
    if "final_response" not in current_state:
        current_state["final_response"] = ""
    current_state["final_response"] = final_response
    return "Final response created"

async def set_news_query(ctx: Context, news_query: str) -> str:
    """Useful to create the query to ask the NewsSearchAgent. You should pass the news query."""
    current_state = await ctx.get("state")
    if "news_query" not in current_state:
        current_state["news_query"] = ""
    current_state["news_query"] = news_query
    return "Final response created"

async def set_wiki_page_name(ctx: Context, wikipedia_page_name: str) -> str:
    """Useful to create the Wikipedia page name to ask the InfoSearchAgent. You should pass the Wikipedia page name."""
    current_state = await ctx.get("state")
    if "wikipedia_page_name" not in current_state:
        current_state["wikipedia_page_name"] = ""
    current_state["wikipedia_page_name"] = wikipedia_page_name
    return "Wikipedia page name created"

async def set_weather_location(ctx: Context, weather_location: str) -> str:
    """Useful to create the location to pass to the WeatherAgent. You should pass the location."""
    current_state = await ctx.get("state")
    if "weather_location" not in current_state:
        current_state["weather_location"] = ""
    current_state["weather_location"] = weather_location
    return "Weather location created"
