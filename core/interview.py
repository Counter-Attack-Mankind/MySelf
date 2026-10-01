from config import INTERVIEW_DIMENSIONS

from core.database import (
    get_interview_dimension_counts,
    save_sample,
)

from core.ollama_client import (
    generate_interview_question,
)


def choose_dimension() -> str:
    """
    优先选择目前 Interview 数据最少的人格维度。
    """

    counts = get_interview_dimension_counts()

    min_count = min(
        counts.get(dimension, 0)
        for dimension in INTERVIEW_DIMENSIONS
    )

    candidates = [
        dimension
        for dimension in INTERVIEW_DIMENSIONS
        if counts.get(dimension, 0) == min_count
    ]

    # 第一版先直接选择第一个。
    #
    # 后续可以增加随机性和更复杂的主动学习策略。
    return candidates[0]


def run_interview():
    """
    完成一次 Interview：
    选择数据缺口 -> 生成情境 -> 用户回答 -> 保存。
    """

    dimension = choose_dimension()

    print()
    print("======== Interview Mode ========")
    print()
    print(f"[当前观察维度：{dimension}]")
    print()

    try:
        question = generate_interview_question(
            dimension
        )

    except Exception as e:
        print(f"[生成采访问题失败] {e}")
        return

    print(f"MyselfLM > {question}")
    print()

    answer = input("You > ").strip()

    if not answer:
        print("\n[本次 Interview 已取消]\n")
        return

    if answer == "/cancel":
        print("\n[本次 Interview 已取消]\n")
        return

    save_sample(
        user_message=question,
        model_response=None,

        # Interview 本身就是用户真实回答，
        # 因此属于高质量人工样本。
        rating="interview",

        corrected_response=answer,

        source="interview",
        scene=dimension,
    )

    print()
    print("[已保存人格采访样本]")
    print()