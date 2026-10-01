import requests

from config import (
    OLLAMA_URL,
    MODEL_NAME,
    PERSONALITY_PROMPT,
)


def request_ollama(messages: list[dict]) -> str:
    """
    最底层 Ollama API 调用。
    """

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,

        # MyselfLM 目前重点是自然聊天，
        # 普通交流不需要开启 Qwen3 Thinking。
        "think": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"].strip()


def chat(history: list[dict]) -> str:
    """
    普通多轮聊天。

    history 格式：

    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    """

    messages = [
        {
            "role": "system",
            "content": PERSONALITY_PROMPT,
        },
        *history,
    ]

    return request_ollama(messages)


def generate_interview_question(dimension: str) -> str:
    """
    根据当前需要采集的人格维度，
    让模型主动设计一个自然情境并采访用户。
    """

    prompt = f"""
你正在帮助构建一个人格模仿模型。

现在需要观察用户在下面这种人格/交流维度中的真实表达：

【{dimension}】

你的任务不是分析用户，也不是告诉用户应该怎么说。

请像一个自然的采访者一样，构造一个具体、真实、生活化的情境，
然后问用户：

“如果现实中遇到这种情况，你一般会怎么回？”

要求：

1. 只提出一个情境。
2. 情境要具体，而不是抽象问题。
3. 不要给示范答案。
4. 不要暗示应该使用什么语气。
5. 不要重复解释采访目的。
6. 控制在 120 字以内。
7. 尽量像正常聊天，而不是心理测试题。
"""

    messages = [
        {
            "role": "system",
            "content": "你负责生成自然的人格采访问题。",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    return request_ollama(messages)