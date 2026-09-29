from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from tools import web_search

from model import model
import logging
from langchain.tools import tool
from prompt import SUBAGENT_2_PROMPT,MAIN_AGENT_PROMPT
from post_store import get_topics, publish_post as save_post


logging.basicConfig(
    level=logging.INFO
)



sa1=create_agent(
    model=model,
    tools=[web_search]
)
sa2=create_agent(
    model=model,
    system_prompt=SUBAGENT_2_PROMPT
)


@tool
def delegate_to_subagent1(query:str):
    """
    search the web for the given topic by delegating the task to subagent1 to do so
    
    """
    logging.info(f"delegating query to subagent1: {query}")
    res=sa1.invoke({"messages":[HumanMessage(content=query)]})
    return res["messages"][-1].content



@tool
def review_used_topics() -> str:
    """Return every topic already published so a new topic can be chosen."""
    topics = get_topics()
    if not topics:
        return "No topics have been published yet."
    return "Previously published topics:\n" + "\n".join(f"- {topic}" for topic in topics)


@tool
def publish_post(
    title: str,
    content: str,
    topic: str,
    tags: str = "AI, Agents, LangChain",
) -> str:
    """Publish a finished blog post with its topic, title, body, and comma-separated tags."""
    post = save_post(title, content, tags, topic)
    logging.info("Published post: %s", post["title"])
    return f"Published post: {post['title']}"


@tool
def delegate_to_subagent2(query:str):
    """
    for drafting the given content by delegating subagent2 to do so!
    
    """
    logging.info(f"delegating query to subagent2: {query}")
    res=sa2.invoke({"messages":[HumanMessage(content=query)]})
    return res["messages"][-1].content


agent=create_agent(
    model=model,
    tools=[review_used_topics,delegate_to_subagent1,delegate_to_subagent2,publish_post],
    system_prompt=MAIN_AGENT_PROMPT
)


def run_main_agent() -> str:
    """Run the main agent workflow; it publishes through the publish_post tool."""
    response = agent.invoke({
        "messages": [HumanMessage(content=(
            "Run the autonomous blog workflow. First call review_used_topics and read the complete "
            "history, then choose a meaningfully different topic, research and draft it, and publish "
            "it with publish_post including the exact topic you selected."
        ))]
    })
    return response["messages"][-1].content






