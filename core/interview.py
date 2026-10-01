import json
from pathlib import Path

import requests

from core.database import create_interview_session, finish_interview_session, save_interview_turn
from core.interview_policy import choose_next_sampling
from core.ollama_client import generate_interview_question


USER_CONTEXT_PATH = Path(__file__).resolve().parent.parent / "data" / "user_context.json"
INTERVIEW_HISTORY_LIMIT = 4


def load_user_context() -> dict:
    if not USER_CONTEXT_PATH.exists():
        return {}
    with USER_CONTEXT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_interview():
    session_id = create_interview_session()
    user_context = load_user_context()
    interview_history = []
    previous_turns = []
    attempt_index = 0

    print("\n======== Interview Mode ========")
    print("输入 /done 完成采访，/cancel 取消采访，/skip 跳过当前问题。\n")

    while True:
        sampling = choose_next_sampling(
            interview_history,
            previous_turns,
            user_context,
            attempt_index,
        )
        attempt_index += 1
        reference_turn = next(
            (turn for turn in previous_turns if turn["id"] == sampling["reference_turn_id"]),
            None,
        )

        try:
            question = generate_interview_question(
                sampling,
                interview_history[-INTERVIEW_HISTORY_LIMIT:],
                user_context,
                reference_turn,
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

        turn_index = len(previous_turns) + 1
        turn_id = save_interview_turn(
            session_id=session_id,
            turn_index=turn_index,
            question_text=question,
            answer_text=answer,
            parent_turn_id=sampling["reference_turn_id"],
            question_strategy=sampling["strategy"],
            relationship=sampling["relationship"],
            life_domain=sampling["life_domain"],
            task_type=sampling["task_type"],
            communication_goal=sampling["communication_goal"],
            emotion_tone=sampling["emotion_tone"],
        )
        interview_history.append({"question": question, "answer": answer})
        previous_turns.append(
            {
                "id": turn_id,
                "strategy": sampling["strategy"],
                "question": question,
                "answer": answer,
                "relationship": sampling["relationship"],
                "life_domain": sampling["life_domain"],
                "task_type": sampling["task_type"],
                "communication_goal": sampling["communication_goal"],
                "emotion_tone": sampling["emotion_tone"],
            }
        )
        print("\n[已保存本轮回答]\n")
