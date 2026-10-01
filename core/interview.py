import json
from pathlib import Path

import requests

from core.database import create_interview_session, finish_interview_session, save_interview_turn
from core.ollama_client import generate_interview_question


USER_CONTEXT_PATH = Path(__file__).resolve().parent.parent / "data" / "user_context.json"
INTERVIEW_HISTORY_LIMIT = 4

DOMAIN_ALIASES = {
    "科研": "research",
    "校园": "campus",
    "日常生活": "daily_life",
    "家庭": "family",
    "恋爱": "relationship",
    "娱乐": "entertainment",
    "游戏": "gaming",
    "健身": "fitness",
    "未来": "future",
    "兴趣": "personal_interest",
    "哲学": "personal_interest",
    "朋友": "daily_life",
}

SAMPLING_CONDITIONS = (
    {
        "relationship": "close_friend",
        "life_domain": "daily_life",
        "task_type": "reply",
        "communication_goal": "casual_chat",
        "emotion_tone": "neutral",
    },
    {
        "relationship": "parent",
        "life_domain": "family",
        "task_type": "explain",
        "communication_goal": "ask_for_help",
        "emotion_tone": "neutral",
    },
    {
        "relationship": "self",
        "life_domain": "personal_interest",
        "task_type": "describe",
        "communication_goal": "share_happiness",
        "emotion_tone": "positive",
    },
    {
        "relationship": "labmate",
        "life_domain": "research",
        "task_type": "complain",
        "communication_goal": "express_dissatisfaction",
        "emotion_tone": "mild_negative",
    },
    {
        "relationship": "classmate",
        "life_domain": "campus",
        "task_type": "write_message",
        "communication_goal": "ask_for_help",
        "emotion_tone": "embarrassed",
    },
    {
        "relationship": "lover",
        "life_domain": "relationship",
        "task_type": "persuade",
        "communication_goal": "disagree",
        "emotion_tone": "mild_negative",
    },
    {
        "relationship": "normal_friend",
        "life_domain": "gaming",
        "task_type": "joke",
        "communication_goal": "casual_chat",
        "emotion_tone": "excited",
    },
    {
        "relationship": "stranger",
        "life_domain": "daily_life",
        "task_type": "reply",
        "communication_goal": "refuse",
        "emotion_tone": "high_pressure",
    },
    {
        "relationship": "advisor",
        "life_domain": "research",
        "task_type": "explain",
        "communication_goal": "ask_for_help",
        "emotion_tone": "high_pressure",
    },
    {
        "relationship": "self",
        "life_domain": "future",
        "task_type": "choose",
        "communication_goal": "casual_chat",
        "emotion_tone": "neutral",
    },
    {
        "relationship": "close_friend",
        "life_domain": "entertainment",
        "task_type": "narrate",
        "communication_goal": "share_happiness",
        "emotion_tone": "excited",
    },
    {
        "relationship": "normal_friend",
        "life_domain": "fitness",
        "task_type": "advise",
        "communication_goal": "encourage",
        "emotion_tone": "positive",
    },
    {
        "relationship": "teacher",
        "life_domain": "campus",
        "task_type": "explain",
        "communication_goal": "apologize",
        "emotion_tone": "embarrassed",
    },
)


def load_user_context() -> dict:
    if not USER_CONTEXT_PATH.exists():
        return {}
    with USER_CONTEXT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def choose_sampling_condition(question_index: int, user_context: dict) -> dict:
    common_domains = user_context.get("common_domains", [])
    preferred_domains = {
        DOMAIN_ALIASES.get(domain, domain)
        for domain in common_domains
        if DOMAIN_ALIASES.get(domain, domain)
    }
    candidates = [
        condition
        for condition in SAMPLING_CONDITIONS
        if not preferred_domains or condition["life_domain"] in preferred_domains
    ]
    if not candidates:
        candidates = list(SAMPLING_CONDITIONS)
    return dict(candidates[question_index % len(candidates)])


def run_interview():
    session_id = create_interview_session()
    user_context = load_user_context()
    interview_history = []
    question_index = 0

    print("\n======== Interview Mode ========")
    print("输入 /done 完成采访，/cancel 取消采访，/skip 跳过当前问题。\n")

    while True:
        sampling_condition = choose_sampling_condition(question_index, user_context)
        question_index += 1

        try:
            question = generate_interview_question(
                sampling_condition,
                interview_history[-INTERVIEW_HISTORY_LIMIT:],
                user_context,
            )
        except requests.RequestException as error:
            finish_interview_session(session_id, "cancelled")
            print(f"\n[生成采访问题失败，本次 Interview 已取消] {error}\n")
            return

        print(f"MyselfLM > {question}\n")
        answer = input("You > ").strip()

        if answer == "/done":
            finish_interview_session(session_id, "completed")
            print("\n[本次 Interview 已完成]\n")
            return

        if answer == "/cancel":
            finish_interview_session(session_id, "cancelled")
            print("\n[本次 Interview 已取消，已保存的回答仍会保留]\n")
            return

        if not answer or answer == "/skip":
            print("\n[已跳过当前问题]\n")
            continue

        turn_index = len(interview_history) + 1
        save_interview_turn(
            session_id=session_id,
            turn_index=turn_index,
            question_text=question,
            answer_text=answer,
            question_strategy="continuous",
            relationship=sampling_condition["relationship"],
            life_domain=sampling_condition["life_domain"],
            task_type=sampling_condition["task_type"],
            communication_goal=sampling_condition["communication_goal"],
            emotion_tone=sampling_condition["emotion_tone"],
        )
        interview_history.append({"question": question, "answer": answer})
        print("\n[已保存本轮回答]\n")
