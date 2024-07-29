from typing import Any, Optional, Tuple, Union, List
from dotenv import load_dotenv
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish
from langchain.tools.render import render_text_description
from langchain_openai import ChatOpenAI
from loguru import logger

# from langchain_core.tools import Tool, tool
# from langchain.tools import Tool, tool
from langchain.agents import tool
from langchain.agents.format_scratchpad import format_log_to_str
from langchain_core.tools import Tool

from langchain.prompts import PromptTemplate

from react.callbacks import AgentCallbackHandler

load_dotenv()


@tool
def get_text_length(text: str) -> int:
    """Returns the length of a text by characters"""
    logger.info(f"get_text_length enter with {text=}")
    text = text.strip("'\n").strip(
        '"'
    )  # stripping away non alphabetic characters just in case
    return len(text)


def find_tool_by_name(tools: List[Tool], tool_name: str) -> Tool:
    for tool in tools:
        if tool.name == tool_name:
            return tool
    raise ValueError(f"Tool wtih name {tool_name} not found")


if __name__ == "__main__":
    logger.info("Hello ReAct LangChain!")
    tools: List[Any] = [get_text_length]

    template = """
    Answer the following questions as best you can. You have access to the following tools:

    {tools}
    
    Use the following format:
    
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    
    Begin!
    
    Question: {input}
    Thought: {agent_scratchpad}
    """

    prompt = PromptTemplate.from_template(template=template).partial(
        tools=render_text_description(tools),
        tool_names=", ".join([t.name for t in tools]),
    )

    llm = ChatOpenAI(
        temperature=0,
        stop_sequences=["\nObservation", "Observation"],
        callbacks=[AgentCallbackHandler()],
    )
    intermediate_steps: List[Tuple[AgentAction, str]] = []
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(x["agent_scratchpad"]),
        }
        | prompt
        | llm
        | ReActSingleInputOutputParser()
    )

    agent_step: Optional[Union[AgentAction, AgentFinish]] = None

    while not isinstance(agent_step, AgentFinish):
        agent_step = agent.invoke(
            {
                "input": "What is the length of 'DOG' in characters?",
                "agent_scratchpad": intermediate_steps,
            }
        )

        logger.info(agent_step)

        if isinstance(agent_step, AgentAction):
            tool_name = agent_step.tool
            tool_to_use = find_tool_by_name(tools, tool_name)

            if tool_to_use is None:
                raise ValueError

            tool_input = agent_step.tool_input
            if not hasattr(tool_to_use, "func"):
                raise AttributeError(f"Tool {tool_name} does not have a 'func' method")

            abc = str(tool_input)
            observation = tool_to_use.func(str(tool_input))  # pyright: ignore
            logger.info(f"{observation}")
            intermediate_steps.append((agent_step, str(observation)))

    if isinstance(agent_step, AgentFinish):
        logger.success(agent_step.return_values)
