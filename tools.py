from langchain.tools import tool
from tavily import TavilyClient
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO
)


tavily=TavilyClient()



@tool
def web_search(query:str):
    """
    allows to search the web for knowledge or info!
    """
    return tavily.search(query)






