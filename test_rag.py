"""Run the RAG pipeline without the UI and print scores to help choose THRESHOLD.
Run:  python test_rag.py
"""
import rag

CITY = "Long Xuyen"

# (type, question, expected ID or None if the answer is not in the guide)
TESTS = [
    ("answerable", "What time is the Long Xuyen floating market busiest?", "G01"),
    ("answerable", "When is the walking street closed to vehicles?", "G08"),
    ("answerable", "How much does a bowl of bun ca Hieu Thuan cost?", "G11"),
    ("paraphrase", "Where can I eat fermented fish hotpot for dinner?", "G14"),
    ("not in guide", "What are the opening hours of An Giang Museum?", None),
    ("not in guide", "What is the phone number of the city hospital?", None),
    ("two entries", "How do I get to the island where President Ton Duc Thang was born?", "G02 + G03"),
    # Extra hard questions to look for real failures
    # Extra hard questions to look for real failures
    ("Hard", "How much is the ferry to Ong Ho Islet?", "none"),
    ("Hard", "Which place is open at 6 am for breakfast?", "G12"),
    ("Hard", "What is the cheapest meal in Long Xuyen?", "G11 + G13"),
    ("Hard", "Cho noi Long Xuyen may gio dong nhat?", "G01"),
]

client = rag.get_client()
entries = rag.load_kb()
vectors = rag.build_index(client, entries)
print(f"Loaded {len(entries)} entries. THRESHOLD = {rag.THRESHOLD}\n")

for kind, question, expected in TESTS:
    answer, hits = rag.ask(client, question, entries, vectors, CITY)
    retrieved = ", ".join(f"{h['entry']['id']} ({h['score']:.3f})" for h in hits)
    print(f"[{kind}] {question}")
    print(f"  expected : {expected or 'none'}")
    print(f"  retrieved: {retrieved}")
    print(f"  answer   : {answer}\n")