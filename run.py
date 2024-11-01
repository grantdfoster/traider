import json
from swarm import Swarm, Agent
from openai import OpenAI
import os
from cdp import Cdp
from dotenv import load_dotenv
from wallet import Wallet
from twitter import TwitterBot

# Load environment variables from .env file
load_dotenv()

CDP_API_KEY_NAME = os.getenv("CDP_API_KEY_NAME")
CDP_PRIVATE_KEY = os.getenv("CDP_PRIVATE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

Cdp.configure(CDP_API_KEY_NAME, CDP_PRIVATE_KEY)
print("CDP SDK has been successfully configured with CDP API key.")

wallet = Wallet()
print(f"Agent wallet: {wallet.address()}")

# # TODO Initialize TwitterBot with credentials
# twitter_bot = TwitterBot(
#     api_key=TWITTER_API_KEY,
#     api_secret=TWITTER_API_SECRET,
#     access_token=TWITTER_ACCESS_TOKEN,
#     access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
# )

# Create the Traider Agent with all available functions
traider_agent = Agent(
    name="Traider",
    instructions="You are a helpful agent that can interact onchain on the Base Layer 2 using the Coinbase Developer Platform SDK. You can create tokens, transfer assets, generate art, deploy NFTs, mint NFTs, register basenames, and swap assets (on mainnet only). If you ever need to know your address, it is {agent_wallet.default_address.address_id}. If you ever need funds, you can request them from the faucet. You can also deploy your own ERC-20 tokens, NFTs, and interact with them. If someone asks you to do something you can't do, you can say so, and encourage them to implement it themselves using the CDP SDK, recommend they go to docs.cdp.coinbase.com for more informaton. You can also offer to help them implement it by writing the function and telling them to add it to the agents.py file and within your list of callable functions.",
    functions=[
        wallet.create_token,
        wallet.transfer_asset,
        wallet.deploy_nft,
        wallet.mint_nft,
        wallet.swap_assets,
        wallet.address,
        wallet.balance,
    ],
)


# this is the main loop that runs the agent in two-agent mode
# you can modify this to change the behavior of the agent
def run_openai_conversation_loop(agent):
    """Facilitates a conversation between an OpenAI-powered agent and the Based Agent."""
    client = Swarm()
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    messages = []

    print("Starting OpenAI-Based Agent conversation loop...")

    # Initial prompt to start the conversation
    openai_messages = [
        {
            "role": "system",
            "content": "You are the leader of a company, aiming to create an innovative token on the Base blockchain. You are guiding a blockchain agent, whose role is 'assistant', through various tasks on the Base blockchain. Engage in a conversation, suggesting actions and responding to the agent's outputs. Be creative and explore different blockchain capabilities. Options include creating tokens, transferring assets, minting NFTs, and getting balances. You will soon also be able to use a Twitter agent to promote the token on socials.  You're not simulating a conversation, but you will be in one yourself. Make sure you follow the rules of improv and always ask for some sort of function to occur. Be unique and interesting.",
        },
        {
            "role": "user",
            "content": "Start a conversation with the blockchain agent and guide it through some blockchain tasks, keeping the original goal in mind.",
        },
    ]

    while True:
        # Generate OpenAI response
        openai_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=openai_messages
        )

        openai_message = openai_response.choices[0].message.content
        print(f"\n\033[92mOpenAI Guide:\033[0m {openai_message}")

        # Send OpenAI's message to Based Agent
        messages.append({"role": "system", "content": openai_message})
        response = client.run(agent=agent, messages=messages, stream=True)
        response_obj = process_and_print_streaming_response(response)
        # Update messages with Based Agent's response
        messages.extend(response_obj.messages)

        # Add Based Agent's response to OpenAI conversation
        blockchain_agent_response = (
            response_obj.messages[-1]["content"]
            if response_obj.messages
            else "No response from blockchain agent."
        )
        openai_messages.append(
            {
                "role": "user",
                "content": f"Blockchain agent response: {blockchain_agent_response}",
            }
        )

        # Check if user wants to continue
        user_input = input(
            "\nPress Enter to continue the conversation, or type 'exit' to end: "
        )
        if user_input.lower() == "exit":
            break


# Boring stuff to make the logs pretty
def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


if __name__ == "__main__":
    run_openai_conversation_loop(traider_agent)
