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


def generate_interview_question(
    sampling_condition: dict,
    interview_history: list[dict],
    user_context: dict | None = None,
) -> str:
    """根据采样条件、本次 Interview 上下文和本地背景生成下一题。"""
    context = user_context or {}
    context_text = "\n".join(
        f"- {key}: {value}" for key, value in context.items() if key != "common_domains"
    )
    common_domains = "、".join(context.get("common_domains", []))
    condition_text = "\n".join(
        f"- {key}: {value}" for key, value in sampling_condition.items()
    )
    history_text = "\n\n".join(
        f"Q{index}: {turn['question']}\nA{index}: {turn['answer']}"
        for index, turn in enumerate(interview_history, start=1)
    )

    prompt = f"""
我们正在采集一个真实用户的语言表达风格。

采访对象的本地背景（只用于生成合理场景）：
{context_text or "- 未提供"}
常见生活领域：{common_domains or "未提供"}

不要虚构背景中没有出现的身份。优先使用上述常见生活领域。

本轮采样条件：
{condition_text}

本次 Interview 最近的问答：
{history_text or "暂无，这是第一轮。"}

请参考最近问答保持对话自然连续，但不要分析、总结或判断用户的人格。
根据本轮采样条件生成一个新的采访问题：

1. 目标是采集用户现实中自然的语言表达，不是做心理测试。
2. 问题必须具体、生动，并有符合用户背景的现实上下文。
3. relationship 决定交流对象，life_domain 决定生活场景。
4. task_type 决定任务形式，communication_goal 决定表达目的。
5. emotion_tone 决定场景情绪，但不要要求用户扮演夸张情绪。
6. task_type=reply 时让用户直接回复；narrate 时让用户讲一件事；describe 时让用户描述；explain 时让用户自然解释；choose 时让用户选择并说明；complain 时让用户自然吐槽；persuade 时让用户尝试说服；advise 时让用户给建议；write_message 时让用户写现实中会发出的消息；joke 时使用轻松场景。
7. 不要默认使用公司、同事、老板、办公室或公司项目等场景。
8. 不要让用户分析“自己是什么性格”，不要要求正式作答。
9. 每次只提出一个主要任务，不要提供示范答案。
10. 不要重复解释 Interview 的目的。
11. 问题末尾可以提醒：“不用组织得很正式，按现实里你真的会怎么说就行。”
12. 控制在 160 字以内。

只输出采访问题本身。
"""

    messages = [
        {"role": "system", "content": "你负责设计用于采集真实聊天语言的人格采访情境。"},
        {"role": "user", "content": prompt},
    ]
    return request_ollama(messages)
