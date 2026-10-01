import requests

from config import MODEL_NAME, OLLAMA_URL, PERSONALITY_PROMPT


def request_ollama(messages: list[dict]) -> str:
    """调用本地 Ollama Chat API。"""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "think": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def chat(history: list[dict]) -> str:
    """根据当前普通聊天 history 生成下一条回复。"""
    messages = [
        {"role": "system", "content": PERSONALITY_PROMPT},
        *history,
    ]
    return request_ollama(messages)


def generate_interview_question(dimension: str, user_context: dict | None = None) -> str:
    """根据指定维度和本地用户背景生成采访情境。"""
    context = user_context or {}
    context_text = "\n".join(
        f"- {key}: {value}" for key, value in context.items() if key != "common_domains"
    )
    common_domains = "、".join(context.get("common_domains", []))

    prompt = f"""
我们正在采集一个真实用户的语言表达风格。

采访对象的本地背景（只用于生成合理场景）：
{context_text or "- 未提供"}
常见生活领域：{common_domains or "未提供"}

不要虚构背景中没有出现的身份。优先使用上述常见生活领域。

当前需要观察的交流维度是：

【{dimension}】

请构造一个具体、自然、生活化的聊天情境，
让用户直接回答：

“如果现实中对方这样跟你说，你会怎么回？”

核心目标：
采集用户实际会说出口的话，而不是用户对事情的分析、观点或原则。

必须遵守：

1. 必须存在一个明确的“对方”。
2. 必须给出对方具体说的一句话，最好使用引号。
3. 用户的任务必须是“回复对方”。
4. 不要问“你怎么看”“你会怎么处理”“你觉得应该怎么办”。
5. 不要让用户分析自己的性格。
6. 不要询问用户会如何安慰自己，除非当前维度明确属于自我情绪。
7. 不要提供示范答案。
8. 不要暗示应该使用什么语气或态度。
9. 只生成一个情境。
10. 控制在 120 字以内。

好的形式类似：

你的一个朋友突然对你说：
“我最近什么都做不好，感觉自己特别没用。”

如果现实里他这样跟你说，你一般会怎么回？

注意：
不要复制这个例子，请根据【{dimension}】创造新的情境。
"""

    messages = [
        {"role": "system", "content": "你负责设计用于采集真实聊天语言的人格采访情境。"},
        {"role": "user", "content": prompt},
    ]
    return request_ollama(messages)
