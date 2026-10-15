import sys

from src.generate import Assistant

if len(sys.argv) < 2:
    raise SystemExit('Usage: python -m src.debug_prompt "your question"')
q = " ".join(sys.argv[1:])
hits, prompt = Assistant().prompt_for(q)
print("Sections sent:", [u["section_id"] for u, _ in hits])
print("Prompt length:", len(prompt), "characters")
for word in ("fourteen days", "eighteen days", "twenty-two days", "sixty days"):
    print(f"contains '{word}':", word in prompt)