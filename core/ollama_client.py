import requests

from config import MODEL_NAME, OLLAMA_URL, PERSONALITY_PROMPT


RELATIONSHIP_LABELS = {
    "self": "用户自己，不设置对话对象",
    "close_friend": "关系很好的朋友",
    "normal_friend": "关系一般的朋友",
    "classmate": "同学",
    "labmate": "同门或实验室伙伴",
    "teacher": "老师",
    "advisor": "导师",
    "parent": "父母",
    "lover": "恋人",
    "stranger": "陌生人",
}

TASK_RULES = {
    "reply": "给出对方说的一句具体话，最后让用户直接说会怎么回",
    "narrate": "设置一个向人讲述的场景，让用户像聊天一样讲一件具体事情",
    "describe": "指定一个人、场景或状态，让用户用自己的话描述出来",
    "explain": "设置一件需要向指定对象解释的具体事情，问用户会怎么解释",
    "choose": "给出两个具体选项，让用户选择并像聊天一样说明",
    "complain": "给出一个具体触发点，明确让用户按现实语气吐槽",
    "persuade": "设置一个具体分歧，让用户直接尝试说服指定对象",
    "advise": "给出对方的具体处境，让用户直接劝一劝或给建议",
    "write_message": "设置明确发信原因，让用户写一段现实里真的会发出的消息",
    "joke": "设置轻松具体的对话，让用户自然开玩笑或接话",
}

STRATEGY_RULES = {
    "explore": "写一个与最近题目不同的新场景。",
    "follow_up": "利用参考回答中的具体细节，换成新的表达任务；不能只问喜不喜欢或为什么。",
    "contrast": "沿用参考题的基本结构，只体现给定条件的变化。",
    "validate": "保持表达任务和目的，换一个不同的现实场景，不能复刻参考题。",
}

TONE_LABELS = {
    "positive": "正面轻松",
    "neutral": "中性日常",
    "mild_negative": "轻微负面，只能有点烦、有点失落或不顺",
    "high_pressure": "压力较高，但不得使用崩溃、喘不过气或特别痛苦",
    "angry": "生气，但不要极端化",
    "embarrassed": "有点尴尬",
    "excited": "兴奋开心",
}

RELATIONSHIP_MARKERS = {
    "close_friend": ("朋友",),
    "normal_friend": ("朋友",),
    "classmate": ("同学",),
    "labmate": ("同门", "实验室"),
    "teacher": ("老师",),
    "advisor": ("导师",),
    "parent": ("父母", "妈妈", "爸爸", "家里"),
    "lover": ("恋人", "对象", "男朋友", "女朋友"),
    "stranger": ("陌生人",),
}

DOMAIN_MARKERS = {
    "research": ("科研", "论文", "实验", "研究", "进度"),
    "campus": ("校园", "学校", "上课", "宿舍", "食堂"),
    "family": ("家里", "家庭", "父母", "妈妈", "爸爸"),
    "relationship": ("恋人", "对象", "约会", "感情"),
    "entertainment": ("电影", "音乐", "娱乐", "出去玩"),
    "gaming": ("游戏", "开黑", "队友"),
    "fitness": ("健身", "训练", "运动"),
    "future": ("未来", "以后", "毕业"),
    "personal_interest": ("兴趣", "爱好", "喜欢做的事"),
}

TASK_MARKERS = {
    "reply": ("怎么回", "回复"),
    "narrate": ("怎么讲", "讲给", "把它讲"),
    "describe": ("描述", "讲讲", "说说"),
    "explain": ("怎么解释", "会怎么说", "准备怎么解释"),
    "choose": ("选", "选择"),
    "complain": ("吐槽",),
    "persuade": ("说服", "劝"),
    "advise": ("建议", "劝"),
    "write_message": ("写一段", "会发什么", "怎么发消息"),
    "joke": ("开玩笑", "接话"),
}

GOAL_MARKERS = {
    "comfort": ("安慰", "失落", "难过", "没发挥好", "不顺"),
    "refuse": ("拒绝", "不想", "没法"),
    "congratulate": ("恭喜", "好消息", "成功"),
    "disagree": ("不同意", "分歧", "反对"),
    "apologize": ("道歉", "不好意思", "对不起"),
    "express_dissatisfaction": ("不满", "吐槽", "有点烦"),
    "encourage": ("鼓励", "没信心", "打气"),
    "share_happiness": ("开心", "高兴", "好玩的事"),
    "ask_for_help": ("帮忙", "请教", "求助"),
    "casual_chat": ("聊天", "随口", "日常"),
}

DOMAIN_SCENES = {
    "daily_life": "日常生活里",
    "campus": "校园里",
    "family": "家里",
    "relationship": "一段感情相处中",
    "entertainment": "看电影或出去玩时",
    "gaming": "一起打游戏时",
    "fitness": "健身或运动时",
    "future": "聊到毕业和未来时",
    "personal_interest": "聊自己的兴趣爱好时",
    "research": "做科研、实验或论文时",
}

GOAL_PURPOSES = {
    "comfort": "安慰",
    "refuse": "拒绝",
    "congratulate": "表示恭喜",
    "disagree": "表达不同意",
    "apologize": "道歉",
    "express_dissatisfaction": "表达不满并吐槽",
    "encourage": "鼓励",
    "share_happiness": "分享一件开心的事",
    "ask_for_help": "请求帮忙",
    "casual_chat": "日常聊天",
}

GOAL_QUOTES = {
    "comfort": "这次没弄好，我有点失落。",
    "refuse": "你能不能现在陪我一起处理这件事？",
    "congratulate": "我刚把这件事顺利做成了！",
    "disagree": "我觉得就应该按我的办法来。",
    "apologize": "你刚才那样做让我有点不舒服。",
    "express_dissatisfaction": "这件事这样安排应该没问题吧？",
    "encourage": "我有点没信心，不知道还要不要继续。",
    "share_happiness": "今天这件事也太开心了。",
    "ask_for_help": "这件事我一个人有点弄不明白。",
    "casual_chat": "今天发生了件挺有意思的小事。",
}


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
    messages = [{"role": "system", "content": PERSONALITY_PROMPT}, *history]
    return request_ollama(messages)


def generate_interview_question(
    sampling: dict,
    interview_history: list[dict],
    user_context: dict | None = None,
    reference_turn: dict | None = None,
) -> str:
    """把 policy 选定的策略和采样条件写成自然、具体的表达任务。"""
    draft = _draft_question(sampling, reference_turn)
    prompt = _build_interview_prompt(
        sampling,
        interview_history,
        user_context or {},
        reference_turn,
        draft,
    )
    system_prompt = (
        "你是中文采访题改写器，只输出一道具体题目。题目必须让用户直接产出真实会说的话，"
        "不能调查最近的事实，不能输出分析、标签、Q:或示范答案。"
    )

    last_question = ""
    for _ in range(3):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        last_question = request_ollama(messages)
        issues = _question_issues(last_question, sampling)
        if not issues:
            return last_question
        prompt += (
            f"\n\n上一版不合格：{last_question}\n"
            f"必须修正：{'；'.join(issues)}。\n只重写最终题目。"
        )
    return draft


def _build_interview_prompt(sampling, interview_history, user_context, reference_turn, draft):
    recent = "\n".join(
        f"- 问：{turn['question']} 答：{turn['answer']}" for turn in interview_history
    ) or "无"
    reference = "无"
    changed_axes = []
    if reference_turn:
        reference = f"参考题：{reference_turn['question']}\n参考回答：{reference_turn['answer']}"
        changed_axes = [
            axis
            for axis in ("relationship", "life_domain", "task_type", "communication_goal", "emotion_tone")
            if reference_turn[axis] != sampling[axis]
        ]

    domains = "、".join(user_context.get("common_domains", [])) or "未提供"
    return f"""
把下面的合规题目骨架改写得自然一些，但不能删除人物关系、领域、任务或交流目的：
{draft}

每项条件都必须在题目中看得出来：
- 策略：{sampling['strategy']}。{STRATEGY_RULES[sampling['strategy']]}
- 对象：{RELATIONSHIP_LABELS[sampling['relationship']]}
- 领域：{sampling['life_domain']}，用户常见领域为：{domains}
- 任务：{sampling['task_type']}。{TASK_RULES[sampling['task_type']]}
- 目的：{sampling['communication_goal']}
- 情绪：{sampling['emotion_tone']}。{TONE_LABELS[sampling['emotion_tone']]}

{reference}
相对参考 turn 只变化这些轴：{changed_axes or '无'}
最近已经问过：
{recent}

硬性要求：
1. 给出一个具体人物、触发事件或对方原话，让用户直接表达；每题只做一个任务。
2. 禁止“你最近有没有……”“你最近开心吗”“你最近压力大吗”“你喜欢什么”这类事实调查。
3. 不复述最近回答，不重复最近题型，不擅自加强情绪，不反复追问私人事实。
4. 不默认公司、同事、老板；不要求用户分析性格；不提供示范答案。
5. relationship=self 时不设置对话对象；其他关系必须在题目中明确出现。
6. 题目不超过140字，只输出题目本身，不要输出Q:、条件或解释。
"""


def _draft_question(sampling, reference_turn):
    relationship = RELATIONSHIP_LABELS[sampling["relationship"]]
    scene = DOMAIN_SCENES[sampling["life_domain"]]
    purpose = GOAL_PURPOSES[sampling["communication_goal"]]
    quote = GOAL_QUOTES[sampling["communication_goal"]]
    task = sampling["task_type"]
    has_other_person = sampling["relationship"] != "self"
    detail_prefix = ""
    if sampling["strategy"] == "follow_up" and reference_turn:
        detail = _follow_up_detail(reference_turn["answer"])
        detail_prefix = f"接着你刚才提到的{detail}，"

    if task == "reply":
        return f"{detail_prefix}{scene}，{relationship}对你说：“{quote}”你想{purpose}，现实里会怎么回复？"
    if task == "narrate":
        audience = f"{relationship}问起这件事。" if has_other_person else ""
        return f"{detail_prefix}{scene}发生了一件和“{purpose}”有关的小事。{audience}按平时聊天的语气把它讲出来，你会怎么讲？"
    if task == "describe":
        audience = f"{relationship}想听你说说。" if has_other_person else ""
        return f"{detail_prefix}{scene}，请围绕“{purpose}”描述一个具体场景。{audience}不要总结，按平时说话的方式说说。"
    if task == "explain":
        if not has_other_person:
            return f"{detail_prefix}{scene}，把一件和“{purpose}”有关的具体事情按来龙去脉讲清楚。按平时说法，你会怎么解释？"
        return f"{detail_prefix}{scene}，你需要向{relationship}{purpose}并说明具体情况。按现实中的说法，你会怎么解释？"
    if task == "choose":
        audience = f"{relationship}正在等你的答复。" if has_other_person else ""
        return f"{detail_prefix}{scene}，为了{purpose}，你要在立刻处理和晚点再做之间选择。{audience}你会选哪个，又会怎么说？"
    if task == "complain":
        cause = f"{relationship}反复做同一件小事" if has_other_person else "一件小事反复发生"
        return f"{detail_prefix}{scene}，{cause}让你有点烦。请按现实语气表达不满并吐槽几句。"
    if task == "persuade":
        return f"{detail_prefix}{scene}，{relationship}和你意见不同。你想{purpose}，会怎么劝或说服对方？"
    if task == "advise":
        return f"{detail_prefix}{scene}，{relationship}遇到一件不顺的事。你想{purpose}，会怎么劝他或给建议？"
    if task == "write_message":
        return f"{detail_prefix}{scene}，你需要给{relationship}发消息来{purpose}。请写一段现实里真的会发出去的消息。"
    return f"{detail_prefix}{scene}，{relationship}说：“{quote}”你想{purpose}，会怎么开玩笑或接话？"


def _follow_up_detail(answer):
    topics = ("烤肉", "吃饭", "游戏", "电影", "健身", "运动", "论文", "实验", "导师", "老师", "朋友", "父母", "旅行", "校园")
    found = [topic for topic in topics if topic in answer][:2]
    return "和".join(found) if found else "那件具体的事"


def _question_issues(question, sampling):
    issues = []
    banned = (
        "你最近有没有", "最近有没有", "你最近开心吗", "你最近压力大吗",
        "你遇到什么", "能告诉我你最近", "想和我聊聊吗", "让我感到", "我的回答是",
        "喘不过气", "崩溃", "特别痛苦",
    )
    if any(term in question for term in banned):
        issues.append("不能使用宽泛事实调查或擅自加强情绪")
    if question.lstrip().startswith(("Q:", "Q：", "问题：")):
        issues.append("不能输出Q:或问题标签")
    labels = (
        "触发事件：", "人物：", "领域：", "任务：", "目的：", "情绪：", "条件：",
        "触发事件是", "对象是", "人物是", "领域是", "任务是", "目的是", "情绪是",
    )
    if any(label in question for label in labels):
        issues.append("不能附带人物、领域、任务或情绪标签")
    if len(question) > 180:
        issues.append("题目过长")

    relationship = sampling["relationship"]
    if relationship != "self" and not any(marker in question for marker in RELATIONSHIP_MARKERS[relationship]):
        issues.append(f"必须明确体现对象{RELATIONSHIP_LABELS[relationship]}")

    domain = sampling["life_domain"]
    if domain in DOMAIN_MARKERS and not any(marker in question for marker in DOMAIN_MARKERS[domain]):
        issues.append(f"必须明确体现领域{domain}")

    task = sampling["task_type"]
    if not any(marker in question for marker in TASK_MARKERS[task]):
        issues.append(f"必须让用户实际完成{task}任务")

    goal = sampling["communication_goal"]
    if not any(marker in question for marker in GOAL_MARKERS[goal]):
        issues.append(f"必须明确体现交流目的{goal}")
    return issues
