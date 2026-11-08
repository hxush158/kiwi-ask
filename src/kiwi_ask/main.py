import os

from dotenv import load_dotenv
from kiwi_ask.common.llm import get_chat_client

load_dotenv()

def main():
    client = get_chat_client()
    response = client.chat.completions.create(
        model=os.environ["CHAT_DEPLOYMENT"],
        messages=[
            {"role": "user", "content": "用一句话解释什么是 embedding。"},
        ],
    )
    print(response.choices[0].message.content)
    
if __name__ == "__main__": 
    main()