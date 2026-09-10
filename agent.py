from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from tools import web_search

from model import model
import logging
from langchain.tools import tool
from prompt import SUBAGENT_2_PROMPT,MAIN_AGENT_PROMPT


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
def delegate_to_subagent2(query:str):
    """
    for drafting the given content by delegating subagent2 to do so!
    
    """
    logging.info(f"delegating query to subagent2: {query}")
    res=sa2.invoke({"messages":[HumanMessage(content=query)]})
    return res["messages"][-1].content


agent=create_agent(
    model=model,
    tools=[delegate_to_subagent1,delegate_to_subagent2],
    system_prompt=MAIN_AGENT_PROMPT
)

res=agent.invoke({
    "messages":HumanMessage(content="Start the autonomous workflow!")
})
print(res["messages"][-1])






