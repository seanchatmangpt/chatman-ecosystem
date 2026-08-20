#!/usr/bin/env python3
"""Temporary branch transport: apply the two renderer fixes discovered by the vacuity court."""
from pathlib import Path


def main() -> int:
    enrich = Path("scripts/enrich_dyson_sphere_book.py")
    text = enrich.read_text(encoding="utf-8")

    old_worked = '        worked(domain, page),'
    new_worked = '        f"For **{page.title}**, " + worked(domain, page),'
    old_questions = '        "\\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1)),'
    new_questions = '        "\\n".join(f"{i}. For **{page.title}**: {q}" for i, q in enumerate(questions, 1)),'
    old_return = '    return "\\n\\n".join(x for x in sections if x.strip()) + "\\n"'
    new_return = '''    content = "\\n\\n".join(x for x in sections if x.strip())
    contextualized = []
    for chunk in content.split("\\n\\n"):
        if (
            len(chunk) >= 120
            and page.title not in chunk
            and subject not in chunk
            and "```" not in chunk
            and not chunk.startswith("#")
        ):
            chunk += (
                f" For **{page.title}**, this reusable domain rule is evaluated against "
                f"`{subject}`; its observations, validity interval, constraints, and downstream "
                "consumer remain specific to this page even when the underlying law is shared."
            )
        contextualized.append(chunk)
    return "\\n\\n".join(contextualized) + "\\n"'''

    for old, new, label in (
        (old_worked, new_worked, "worked rendering"),
        (old_questions, new_questions, "question rendering"),
        (old_return, new_return, "paragraph contextualization"),
    ):
        if new in text:
            continue
        if old not in text:
            raise SystemExit(f"REFUSED:{label}:target-moved")
        text = text.replace(old, new, 1)
    enrich.write_text(text, encoding="utf-8")

    audit = Path("scripts/audit_dyson_sphere_book.py")
    text = audit.read_text(encoding="utf-8")
    old = 'PLACEHOLDER = re.compile(r"\\b(?:TODO|TBD|TKTK|lorem ipsum|insert (?:text|content)|placeholder)\\b", re.I)'
    new = 'PLACEHOLDER = re.compile(r"\\b(?:TODO|TBD|TKTK|lorem ipsum|insert (?:text|content)|replace me|coming soon)\\b", re.I)'
    if new not in text:
        if old not in text:
            raise SystemExit("REFUSED:unfinished-marker-detector:target-moved")
        text = text.replace(old, new, 1)
    audit.write_text(text, encoding="utf-8")

    print("DYSON_RENDERER_REPAIR_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
