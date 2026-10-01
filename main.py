from core.ollama_client import chat

from core.database import (
    init_database,
    save_sample,
)

from core.interview import run_interview


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

    # 当前会话上下文
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

        # =========================
        # command
        # =========================

        if message == "/exit":
            break

        if message == "/clear":
            history.clear()

            print()
            print("[当前聊天上下文已清空]")
            print()

            continue

        if message == "/interview":

            run_interview()

            # Interview 不进入当前聊天 history。
            #
            # 因为它属于数据采集模式，
            # 而不是当前自然会话的一部分。
            continue

        # =========================
        # normal chat
        # =========================

        history.append(
            {
                "role": "user",
                "content": message,
            }
        )

        try:

            response = chat(history)

        except Exception as e:

            print()
            print(f"[ERROR] {e}")
            print()

            # API 失败的话，把刚才加入的 user 消息撤销。
            history.pop()

            continue

        history.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        print()
        print(f"Myself > {response}")

        # =========================
        # feedback
        # =========================

        rating = get_rating()

        if rating == "":
            print()
            continue

        if rating == "1":

            save_sample(
                user_message=message,
                model_response=response,
                rating="good",
                source="chat",
            )

        elif rating == "2":

            save_sample(
                user_message=message,
                model_response=response,
                rating="normal",
                source="chat",
            )

        elif rating == "3":

            save_sample(
                user_message=message,
                model_response=response,
                rating="bad",
                source="chat",
            )

        elif rating == "4":

            corrected = input(
                "\n你的回答 > "
            ).strip()

            if corrected:

                save_sample(
                    user_message=message,
                    model_response=response,
                    rating="corrected",
                    corrected_response=corrected,
                    source="chat",
                )

                # =========================
                # 核心设计
                # =========================
                #
                # 原本 history[-1] 是模型回答。
                #
                # 既然用户已经明确说：
                # “我不会这么回答，我会说 corrected”
                #
                # 那么后续上下文也应该认为
                # assistant 当时说的是 corrected。
                #
                # 这样下一轮不会继续沿着错误人格发展。

                history[-1] = {
                    "role": "assistant",
                    "content": corrected,
                }

                print()
                print(
                    "[已使用你的真实回答替换当前会话中的模型回答]"
                )

        else:

            print()
            print("[无效选项，本轮不保存]")

        print()


if __name__ == "__main__":
    main()