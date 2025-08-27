from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from stores.s3_vector import S3VectorStore
from utils.logger import setup_logger

logger = setup_logger(__name__)

app = BedrockAgentCoreApp()



@tool()
def search_a3_wiki(query: str):
    """Search A3 Data Wiki for relevant information"""
    logger.info(f"Searching A3 Data Wiki for query: {query}")
    store = S3VectorStore(bucket_name="a3wiki", index_name="github2")
    logger.info("Vector store initialized")
    results = store.search(query, limit=5)

    markdown_response = "\n".join([doc.to_md() for doc in results])

    logger.info(f"Search completed with {len(results)} results found")
    return markdown_response


model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(
    model_id=model_id,
)
agent = Agent(
    model=model,
    tools=[calculator, search_a3_wiki],
    
    system_prompt="You are a helpful document retriever agent, you excel at answering questions about A3Data Frameworks and internal information using tools available."
)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke the agent with a payload
    """
    user_input = payload.get("prompt")
    print("User input:", user_input)
    response = agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
