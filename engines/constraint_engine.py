#!/usr/bin/env python3
"""兼容层：旧人设约束引擎，内部委托到 xhs_post.validation.persona_constraints。"""

from __future__ import annotations

from xhs_post.validation.persona_constraints import PersonaConstraintService


class PersonaConstraintEngine(PersonaConstraintService):
    """保留旧类名，内部直接复用新的 validation 实现。"""


def main() -> None:
    engine = PersonaConstraintEngine()
    print("PersonaConstraintEngine 已迁移到 xhs_post.validation.persona_constraints")


if __name__ == "__main__":
    main()
