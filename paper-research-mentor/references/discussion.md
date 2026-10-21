# Participatory discussion

Stages: `intuition`, `mechanism`, `transfer`, all initially pending/unverified. One or two focused questions per turn. Under “do not ask me”, save questions and complete independent work without a live question.

Intuition asks for the problem or a prediction when an assumption changes. Mechanism asks for a formula/toy-case explanation or a judgment about a concrete control. Transfer asks for a baseline-controlled test and an observation that would change the user's view.

Avoid “do you understand?”, generic quizzes and testing every paragraph. Diagnose the missing link, give a targeted hint, invite revision, then partial explanation and full answer if needed. Direct explanation is always available.

Use immutable `mentor.py checkpoint` events. `answer` stores the user's actual words. Evaluation `needs_hint`, `independent` or `transferable` requires a referenced genuine answer and a reason. UI labels: 未验证、需要提示、能独立解释、能迁移判断.

No answer -> pending; explicit skip -> skipped/unverified. “I understand” alone is insufficient. Hints, partial explanations and answer reveals are separate events. Set `answer_exposed` if report/reference answers were actually shown. Do not upgrade to independent after assistance in the same attempt. A new genuinely different question can create a new checkpoint; never erase earlier events.

Scripts validate chronology and forbid unsupported upgrades; they cannot prove a human supplied the text. Codex must record only actual user messages. Test-fixture answers remain visibly synthetic and outside real-user records.

Give a short paper map, ask a consequential prediction, examine the answer against evidence, then invite an alternative explanation/failure condition. Finish with the user's position, remaining uncertainty and a reasoned next test, not manufactured agreement.

Keep question cards and reference answers separate, with full materials accessible. This is not a closed-book guarantee. Resume the saved checkpoint and distinguish aided explanation from later independent transfer.
