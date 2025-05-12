import os
from typing import Type

import backoff
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

_openai_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
)
async def call_openai_parsed(
    system_content: str,
    user_content: str,
    response_pydantic_model: Type[BaseModel],
    openai_client: AsyncOpenAI,
):
    # OpenAI's Pydantic powered Structured Output API
    response = await openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,  # Low temperature for more deterministic output
        response_format=response_pydantic_model,
    )
    parsed_response = response.choices[0].message.parsed

    if not isinstance(parsed_response, response_pydantic_model):
        raise TypeError("OpenAI Structured Output failed")
    return parsed_response


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
)
async def get_openai_embedding(text: str, openai_client: AsyncOpenAI) -> list[float]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding
