from collections import Counter


STRATEGIES = ("explore", "follow_up", "contrast", "validate")
NEGATIVE_TONES = {"mild_negative", "high_pressure", "angry"}
HEAVY_CONTEXTS = {"research", "advisor", "teacher"}

RELATIONSHIPS = (
    "close_friend", "normal_friend", "classmate", "labmate", "parent",
    "lover", "stranger", "self", "teacher", "advisor",
)
LIFE_DOMAINS = (
    "daily_life", "campus", "family", "relationship", "entertainment",
    "gaming", "fitness", "future", "personal_interest", "research",
)
TASK_TYPES = (
    "reply", "narrate", "describe", "explain", "choose",
    "complain", "persuade", "advise", "write_message", "joke",
)

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

RELATIONSHIPS_BY_DOMAIN = {
    "daily_life": ("close_friend", "normal_friend", "classmate", "parent", "lover", "stranger", "self"),
    "campus": ("classmate", "normal_friend", "labmate", "teacher", "stranger", "self"),
    "family": ("parent", "self", "lover", "close_friend"),
    "relationship": ("lover", "close_friend", "self", "normal_friend"),
    "entertainment": ("close_friend", "normal_friend", "classmate", "lover", "self"),
    "gaming": ("close_friend", "normal_friend", "classmate", "self"),
    "fitness": ("self", "close_friend", "normal_friend", "stranger"),
    "future": ("self", "parent", "advisor", "teacher", "close_friend"),
    "personal_interest": ("self", "close_friend", "normal_friend", "classmate"),
    "research": ("labmate", "advisor", "teacher", "classmate", "self"),
}

TASKS_BY_RELATIONSHIP = {
    "self": ("narrate", "describe", "explain", "choose", "complain"),
}

GOALS_BY_TASK = {
    "reply": ("comfort", "refuse", "congratulate", "disagree", "apologize", "encourage", "ask_for_help", "casual_chat"),
    "narrate": ("share_happiness", "express_dissatisfaction", "casual_chat"),
    "describe": ("share_happiness", "express_dissatisfaction", "casual_chat"),
    "explain": ("apologize", "disagree", "ask_for_help", "casual_chat"),
    "choose": ("ask_for_help", "casual_chat"),
    "complain": ("express_dissatisfaction", "casual_chat"),
    "persuade": ("disagree", "encourage", "ask_for_help"),
    "advise": ("comfort", "encourage"),
    "write_message": ("comfort", "refuse", "congratulate", "apologize", "encourage", "ask_for_help", "casual_chat"),
    "joke": ("share_happiness", "casual_chat"),
}

SELF_GOALS_BY_TASK = {
    "narrate": ("share_happiness", "express_dissatisfaction", "casual_chat"),
    "describe": ("share_happiness", "express_dissatisfaction", "casual_chat"),
    "explain": ("express_dissatisfaction", "casual_chat"),
    "choose": ("casual_chat",),
    "complain": ("express_dissatisfaction", "casual_chat"),
}

TONES_BY_GOAL = {
    "comfort": ("neutral", "mild_negative"),
    "refuse": ("neutral", "mild_negative", "high_pressure"),
    "congratulate": ("positive", "excited"),
    "disagree": ("neutral", "mild_negative", "angry"),
    "apologize": ("embarrassed", "mild_negative"),
    "express_dissatisfaction": ("mild_negative", "angry"),
    "encourage": ("neutral", "positive"),
    "share_happiness": ("positive", "excited"),
    "ask_for_help": ("neutral", "embarrassed", "high_pressure"),
    "casual_chat": ("neutral", "positive", "excited"),
}

RELATIONSHIP_CONTRASTS = {
    "close_friend": "classmate",
    "classmate": "close_friend",
    "normal_friend": "close_friend",
    "labmate": "classmate",
    "teacher": "classmate",
    "advisor": "labmate",
    "parent": "close_friend",
    "lover": "close_friend",
    "stranger": "normal_friend",
    "self": "close_friend",
}


def choose_next_sampling(interview_history, previous_turns, user_context, attempt_index=0):
    coverage = _coverage(previous_turns)
    if not previous_turns:
        return _explore(previous_turns, user_context, coverage, attempt_index)

    strategy_counts = Counter(turn["strategy"] for turn in previous_turns)
    least_used = min(strategy_counts.get(strategy, 0) for strategy in STRATEGIES)

    if strategy_counts.get("follow_up", 0) == least_used:
        follow_up = _follow_up(interview_history, previous_turns)
        if follow_up:
            return follow_up

    if strategy_counts.get("contrast", 0) == least_used:
        contrast = _contrast(previous_turns, coverage, attempt_index)
        if contrast:
            return contrast

    if strategy_counts.get("validate", 0) == least_used:
        validate = _validate(previous_turns, coverage, attempt_index)
        if validate:
            return validate

    return _explore(previous_turns, user_context, coverage, attempt_index)


def _coverage(turns):
    axes = ("relationship", "life_domain", "task_type", "communication_goal", "emotion_tone")
    return {axis: Counter(turn[axis] for turn in turns) for axis in axes}


def _pick_least(options, counts, attempt_index=0):
    minimum = min(counts.get(option, 0) for option in options)
    candidates = [option for option in options if counts.get(option, 0) == minimum]
    return candidates[attempt_index % len(candidates)]


def _preferred_domains(user_context):
    mapped = [DOMAIN_ALIASES.get(domain, domain) for domain in user_context.get("common_domains", [])]
    preferred = [domain for domain in LIFE_DOMAINS if domain in mapped]
    return preferred or list(LIFE_DOMAINS)


def _recently_repeated(turns, axis, value):
    return len(turns) >= 2 and all(turn[axis] == value for turn in turns[-2:])


def _is_allowed(condition, turns):
    for axis in ("life_domain", "relationship", "task_type"):
        if _recently_repeated(turns, axis, condition[axis]):
            return False

    if turns and turns[-1]["emotion_tone"] in NEGATIVE_TONES and condition["emotion_tone"] in NEGATIVE_TONES:
        return False

    if turns:
        previous = turns[-1]
        previous_heavy = previous["life_domain"] == "research" or previous["relationship"] in {"advisor", "teacher"}
        current_heavy = condition["life_domain"] == "research" or condition["relationship"] in {"advisor", "teacher"}
        if previous_heavy and current_heavy:
            return False
    return True


def _explore(turns, user_context, coverage, attempt_index):
    domains = _preferred_domains(user_context)
    if turns and (turns[-1]["life_domain"] == "research" or turns[-1]["relationship"] in {"advisor", "teacher"}):
        domains = [domain for domain in domains if domain != "research"] or domains
    domains = [domain for domain in domains if not _recently_repeated(turns, "life_domain", domain)] or domains
    domain = _pick_least(domains, coverage["life_domain"], attempt_index)

    relationships = list(RELATIONSHIPS_BY_DOMAIN[domain])
    if turns and turns[-1]["relationship"] in {"advisor", "teacher"}:
        relationships = [relationship for relationship in relationships if relationship not in {"advisor", "teacher"}] or relationships
    relationships = [relationship for relationship in relationships if not _recently_repeated(turns, "relationship", relationship)] or relationships
    relationship = _pick_least(relationships, coverage["relationship"], attempt_index)

    tasks = list(TASKS_BY_RELATIONSHIP.get(relationship, TASK_TYPES))
    tasks = [task for task in tasks if not _recently_repeated(turns, "task_type", task)] or tasks
    task = _pick_least(tasks, coverage["task_type"], attempt_index)
    goal = _pick_least(_goals_for(task, relationship), coverage["communication_goal"], attempt_index)

    tones = list(TONES_BY_GOAL[goal])
    if turns and turns[-1]["emotion_tone"] in NEGATIVE_TONES:
        tones = [tone for tone in tones if tone not in NEGATIVE_TONES] or ["neutral"]
    tone = _pick_least(tones, coverage["emotion_tone"], attempt_index)
    return _plan("explore", relationship, domain, task, goal, tone)


def _follow_up(interview_history, turns):
    last_turn = turns[-1]
    answer = interview_history[-1]["answer"].strip()
    if last_turn["strategy"] == "follow_up" or not _has_specific_content(answer):
        return None
    if last_turn["emotion_tone"] in NEGATIVE_TONES:
        return None

    condition = _condition_from_turn(last_turn)
    if not _is_allowed(condition, turns):
        return None
    return {"strategy": "follow_up", **condition, "reference_turn_id": last_turn["id"]}


def _has_specific_content(answer):
    if len(answer) < 8 or answer in {"不知道", "没有", "还好", "随便", "没什么"}:
        return False
    markers = ("朋友", "老师", "导师", "父母", "同学", "游戏", "吃", "去", "说", "发", "因为", "然后", "但是", "如果")
    return len(answer) >= 16 or any(marker in answer for marker in markers)


def _contrast(turns, coverage, attempt_index):
    axis_order = ("relationship", "emotion_tone", "communication_goal", "task_type")
    contrast_count = sum(turn["strategy"] == "contrast" for turn in turns)
    axes = axis_order[contrast_count % len(axis_order):] + axis_order[:contrast_count % len(axis_order)]

    for reference in reversed(turns):
        for axis in axes:
            candidate = _contrast_condition(reference, axis, coverage, attempt_index)
            if candidate and _is_allowed(candidate, turns):
                return {"strategy": "contrast", **candidate, "reference_turn_id": reference["id"]}
    return None


def _contrast_condition(reference, axis, coverage, attempt_index):
    condition = _condition_from_turn(reference)
    if axis == "relationship":
        replacement = RELATIONSHIP_CONTRASTS[condition["relationship"]]
        if replacement not in RELATIONSHIPS_BY_DOMAIN[condition["life_domain"]]:
            return None
        condition[axis] = replacement
    elif axis == "emotion_tone":
        options = [tone for tone in TONES_BY_GOAL[condition["communication_goal"]] if tone != condition[axis]]
        if not options:
            return None
        condition[axis] = _pick_least(options, coverage[axis], attempt_index)
    elif axis == "communication_goal":
        options = [goal for goal in _goals_for(condition["task_type"], condition["relationship"]) if goal != condition[axis]]
        if not options:
            return None
        condition[axis] = _pick_least(options, coverage[axis], attempt_index)
        compatible_tones = TONES_BY_GOAL[condition[axis]]
        if condition["emotion_tone"] not in compatible_tones:
            return None
    else:
        tasks = TASKS_BY_RELATIONSHIP.get(condition["relationship"], TASK_TYPES)
        options = [
            task
            for task in tasks
            if task != condition[axis]
            and condition["communication_goal"] in _goals_for(task, condition["relationship"])
        ]
        if not options:
            return None
        condition[axis] = _pick_least(options, coverage[axis], attempt_index)
    return condition


def _validate(turns, coverage, attempt_index):
    for reference in turns:
        condition = _condition_from_turn(reference)
        domains = [
            domain
            for domain in LIFE_DOMAINS
            if domain != condition["life_domain"] and condition["relationship"] in RELATIONSHIPS_BY_DOMAIN[domain]
        ]
        if not domains:
            continue
        condition["life_domain"] = _pick_least(domains, coverage["life_domain"], attempt_index)
        if _is_allowed(condition, turns):
            return {"strategy": "validate", **condition, "reference_turn_id": reference["id"]}
    return None


def _condition_from_turn(turn):
    return {
        "relationship": turn["relationship"],
        "life_domain": turn["life_domain"],
        "task_type": turn["task_type"],
        "communication_goal": turn["communication_goal"],
        "emotion_tone": turn["emotion_tone"],
    }


def _goals_for(task, relationship):
    if relationship == "self":
        return SELF_GOALS_BY_TASK[task]
    return GOALS_BY_TASK[task]


def _plan(strategy, relationship, life_domain, task_type, communication_goal, emotion_tone):
    return {
        "strategy": strategy,
        "relationship": relationship,
        "life_domain": life_domain,
        "task_type": task_type,
        "communication_goal": communication_goal,
        "emotion_tone": emotion_tone,
        "reference_turn_id": None,
    }
