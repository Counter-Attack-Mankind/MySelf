import json
from pathlib import Path

import requests

from config import INTERVIEW_DIMENSIONS
from core.database import (
    create_interview_session,
    finish_interview_session,
    get_interview_dimension_counts,
    save_interview_turn,
)
from core.ollama_client import generate_interview_question


USER_CONTEXT_PATH = Path(__file__).resolve().parent.parent / "data" / "user_context.json"


def load_user_context() -> dict:
    if not USER_CONTEXT_PATH.exists():
        return {}
    with USER_CONTEXT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def choose_dimension() -> str:
    """优先选择目前 Interview 数据最少的人格维度。"""
    counts = get_interview_dimension_counts()
    min_count = min(counts.get(dimension, 0) for dimension in INTERVIEW_DIMENSIONS)
    candidates = [
        dimension
        for dimension in INTERVIEW_DIMENSIONS
        if counts.get(dimension, 0) == min_count
    ]
    return candidates[0]


def run_interview():
    """生成一道问题，保存用户回答，然后结束本次 Interview session。"""
    session_id = create_interview_session()
    dimension = choose_dimension()

    print("\n======== Interview Mode ========\n")
    print(f"[当前观察维度：{dimension}]\n")

    try:
        question = generate_interview_question(dimension, load_user_context())
    except requests.RequestException as error:
        finish_interview_session(session_id, "cancelled")
        print(f"[生成采访问题失败] {error}")
        return

    print(f"MyselfLM > {question}\n")
    answer = input("You > ").strip()

    if not answer or answer == "/cancel":
        finish_interview_session(session_id, "cancelled")
        print("\n[本次 Interview 已取消]\n")
        return

    save_interview_turn(
        session_id=session_id,
        turn_index=1,
        question_text=question,
        answer_text=answer,
        question_strategy="single_question",
        communication_goal=dimension,
    )
    finish_interview_session(session_id, "completed")
    print("\n[已保存人格采访样本]\n")
