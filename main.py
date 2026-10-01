import requests

from core.database import init_database, save_training_sample
from core.interview import run_interview
from core.ollama_client import chat


def get_rating():
    print()
    print("[1] 很像我")
    print("[2] 一般")
    print("[3] 不像我")
    print("[4] 我自己回答")
    print("[Enter] 不评价")
    return input("> ").strip()


def main():
    init_database()
    history = []

    print()
    print("MyselfLM v0.2")
    print()
    print("/exit       退出")
    print("/clear      清空当前聊天上下文")
    print("/interview  进入一次人格采访")
    print()

    while True:
        message = input("You > ").strip()
        if not message:
            continue

        if message == "/exit":
            break

        if message == "/clear":
            history.clear()
            print("\n[当前聊天上下文已清空]\n")
            continue

        if message == "/interview":
            run_interview()
            # Interview 是独立的数据采集模式，不进入普通聊天 history。
            continue

        history.append({"role": "user", "content": message})
        try:
            response = chat(history)
        except requests.RequestException as error:
            print(f"\n[ERROR] {error}\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": response})
        print(f"\nMyself > {response}")
        rating = get_rating()

        if rating == "":
            print()
            continue

        if rating == "1":
            save_training_sample(message, response, "good")
        elif rating == "2":
            save_training_sample(message, response, "normal")
        elif rating == "3":
            save_training_sample(message, response, "bad")
        elif rating == "4":
            corrected = input("\n你的回答 > ").strip()
            if corrected:
                save_training_sample(message, response, "corrected", corrected)
                # 后续上下文应使用用户的真实回答，而不是已被否定的模型回答。
                history[-1] = {"role": "assistant", "content": corrected}
                print("\n[已使用你的真实回答替换当前会话中的模型回答]")
        else:
            print("\n[无效选项，本轮不保存]")

        print()


if __name__ == "__main__":
    main()
