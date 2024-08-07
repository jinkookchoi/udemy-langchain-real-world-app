from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts.prompt import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from loguru import logger

from ice_breaker.tools.tools import get_profile_url_tavily

load_dotenv()


def lookup(name: str) -> str:
    logger.info(name)
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    template = """
       given the name {name_of_person} I want you to find a link to their Twitter profile page, and extract from it their username
       In Your Final answer only the person's username"""
    tools_for_agent_twitter = [
        Tool(
            name="Crawl Google 4 Twitter profile page",
            # func=get_profile_url_tavily,
            func=lambda name: get_profile_url_tavily(name=name, include="twitter.com"),
            description="useful for when you need get the Twitter Page URL",
        ),
    ]

    prompt_template = PromptTemplate(
        input_variables=["name_of_person"], template=template
    )

    react_prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(
        llm=llm, tools=tools_for_agent_twitter, prompt=react_prompt
    )
    agent_executor = AgentExecutor(
        agent=agent, tools=tools_for_agent_twitter, verbose=True
    )  # pyright: ignore

    result = agent_executor.invoke(
        input={"input": prompt_template.format_prompt(name_of_person=name)}
    )

    twitter_username: str = result["output"]
    logger.info(twitter_username)

    return twitter_username


if __name__ == "__main__":
    # lookup(name="Boston Dynamics")
    # lookup(name="NewJeans")
    # lookup(name="Eden Marco")
    # lookup(name="Soojung Shin")
    # lookup("Bill Gates")
    # lookup("Jinkook Choi")
    pass
