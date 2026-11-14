# Lumen Travel: Long Xuyen Travel Assistant with RAG Chat

A sign-in travel assistant for Long Xuyen, An Giang. It answers questions only from a small travel guide using Retrieval-Augmented Generation (RAG), and always shows which guide entries it used. Developed as part of the Computational Thinking (Assignment 03 - Sign-in Travel Assistant with RAG Chat) coursework at the Faculty of Information Technology, VNUHCM - University of Science.

## 1. Student Information
- **Full Name:** Doan Khanh Hung
- **Student ID (MSSV):** 25127195
- **Class:** 25C09
- **Institution:** Faculty of Information Technology, University of Science, VNU-HCM
- **Selected City:** Long Xuyen, An Giang, Vietnam

## 2. Models and Services
- **Embedding model:** `embeddinggemma` (served by Ollama)
- **Chat model:** `qwen3:4b` (served by Ollama)
- **Authentication:** Firebase Authentication, Email/Password, called through the REST API
- **User interface:** Streamlit
- **LLM server:** Ollama on Google Colab (Lab 4), exposed through a Pinggy tunnel

## 3. System Overview & Functionality
Key features include:
- **Firebase sign-up / sign-in / sign-out:** the chat page is visible only after sign-in; wrong passwords and invalid emails show clear messages.
- **Travel guide:** `knowledge_base.json` has 18 entries (G01-G18) written in my own words from public sources, each with an id, title, text and source.
- **RAG chat:** the question is embedded with `embeddinggemma`, the guide entries are ranked by cosine similarity, and the top-3 entries above a threshold are sent to `qwen3:4b`, which answers only from them and cites IDs like [G01].
- **Retrieved entries panel:** an expandable panel shows every retrieved entry with its score and whether it was used.
- **I don't know:** when no entry passes the threshold, or the entries do not contain the answer, the assistant says it does not know.
- **Session-only history:** chat history lives in `st.session_state` and is cleared at sign-out (no database).
- **Error handling:** wrong sign-in, empty question, and an unreachable Ollama server each show a readable message instead of a traceback.

## 4. Project Structure
```text
lumen-travel/
├── app.py                # Streamlit UI: sign-in page and chat page
├── rag.py                # Embedding, retrieval (filter, score, top-k) and answer generation
├── firebase_client.py    # Firebase Authentication REST calls
├── knowledge_base.json   # Travel guide: 18 entries about Long Xuyen
├── test_rag.py           # Runs the test questions without the UI
├── requirements.txt      # Required Python dependencies
├── .env.example          # Template for secrets (empty values)
├── .gitignore            # Ignores .env, .venv and cache files
└── README.md             # Project documentation
```

## 5. Installation Instructions
Ensure Python 3.10+ is installed.

```powershell
# 1. Clone the repository
git clone https://github.com/KhanhHung2530/ct-assignment03-25127195
cd lumen-travel

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Create your own .env file
copy .env.example .env
```

Fill in `.env`:
```text
FIREBASE_API_KEY=your Firebase Web API key (project with Email/Password sign-in enabled)
OLLAMA_URL=https://your-pinggy-url   (no trailing slash)
```
The `.env` file is never committed.

## 6. Running the Application (Ollama Server + App)
The app needs the Ollama server from Lab 4 to be running:

1. In the Colab notebook, install and start Ollama, then pull the models `embeddinggemma` and `qwen3:4b`.
2. Start the Pinggy tunnel and copy the `https://...` URL into `OLLAMA_URL` in `.env`. Free tunnels expire after about 60 minutes.
3. Optional check: `curl.exe https://your-pinggy-url/api/tags` should list both models.
4. Start the app:

```powershell
streamlit run app.py
```

The app opens at `http://localhost:8501`. To run only the retrieval and answer tests without the UI: `python test_rag.py`.

## 7. Usage Examples

**Answerable question**
- Question: What time is the Long Xuyen floating market busiest?
- Answer: The Long Xuyen floating market is busiest from 6 am to 8 am [G01].
- Retrieved: G01 (0.757), G08 (0.611), G16 (0.601)

**Question not in the guide**
- Question: What is the phone number of the city hospital?
- Answer: I don't know. The travel guide does not contain this information.
- Retrieved: G18 (0.194), G11 (0.178), G17 (0.161), all below the threshold, so the LLM is not called.

## 8. Test Results
Settings: k = 3, threshold = 0.40.

| # | Type | Question | Expected ID | Retrieved IDs (score) | Correct? | If wrong, where it failed |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Answerable | What time is the Long Xuyen floating market busiest? | G01 | G01 (0.757), G08 (0.611), G16 (0.601) | Yes | - |
| 2 | Answerable | When is the walking street closed to vehicles? | G08 | G08 (0.625), G16 (0.265), G07 (0.263) | Yes | - |
| 3 | Answerable | How much does a bowl of bun ca Hieu Thuan cost? | G11 | G11 (0.694), G12 (0.653), G15 (0.498) | Yes | - |
| 4 | Paraphrase | Where can I eat fermented fish hotpot for dinner? | G14 | G14 (0.569), G11 (0.416), G12 (0.392) | Yes | - |
| 5 | Not in guide | What are the opening hours of An Giang Museum? | none | G04 (0.753), G06 (0.371), G08 (0.359) | Yes (IDK) | - |
| 6 | Not in guide | What is the phone number of the city hospital? | none | G18 (0.194), G11 (0.178), G17 (0.161) | Yes (IDK) | - |
| 7 | Two entries | How do I get to the island where President Ton Duc Thang was born? | G02 + G03 | G02 (0.598), G03 (0.450), G17 (0.381) | Yes | - (answer cites only G03) |
| 8 | Not in guide | How much is the ferry to Ong Ho Islet? | none | G03 (0.634), G01 (0.343), G02 (0.283) | Yes (IDK) | - |
| 9 | Reasoning | Which place is open at 6 am for breakfast? | G12 | G12 (0.413), G01 (0.336), G15 (0.319) | Yes | - (G12 barely above the threshold) |
| 10 | Comparison | What is the cheapest meal in Long Xuyen? | G11 + G13 | G18 (0.742), G10 (0.701), G13 (0.571) | Partial | Retrieval: G11 was missed by top-3 |
| 11 | Non-English | Cho noi Long Xuyen may gio dong nhat? | G01 | G06 (0.556), G17 (0.524), G08 (0.506) | No | Retrieval: G01 not in top-3, wrong entries passed the threshold |

**Summary:** 9 of 11 correct, 1 partially correct, 1 wrong.

**Failure analysis:**
- Question 11 (unaccented Vietnamese against an English guide) fails at **retrieval**: the right entry G01 is not in the top-3, and all three retrieved entries score above 0.40, so the threshold cannot filter them. The model then answers from G08, which is about a different topic.
- Question 10 needs a comparison across entries. The 15,000 VND figure is right, but top-3 missed G11, so the answer does not name the dish.
- During development, the first version leaked the model's reasoning text (`</think>`) into answers. This was a **generation** failure, fixed by sending `think=False` and keeping only the text after the last `</think>`.

## 9. Design Decisions
- **k = 3:** the guide is small (18 entries); k = 3 covers questions that need two entries (question 7) without adding much noise.
- **Threshold = 0.40:** the lowest top-1 score of an answerable question was 0.569 and the off-topic question scored 0.194. 0.40 keeps G03 (0.450) in question 7. A higher value would break question 9 (0.413).
- **Two layers for I don't know:** the threshold removes unrelated entries, but question 5 scored 0.753 because the guide covers the museum without its opening hours. Only the prompt rule (answer only from the entries, otherwise say I don't know) catches this case.
- **Embedding once:** the guide is embedded once with `@st.cache_resource` and reused for every question.

## 10. Known Limitations
- The guide has only 18 entries; many real questions are outside it, and prices, hours and addresses may become outdated (some administrative names changed after the 2025 mergers).
- Questions in Vietnamese without accents retrieve poorly because the guide is in English.
- Comparison questions can miss entries because only the top-3 are used.
- The threshold was tuned on a few questions; borderline cases (such as question 9) may break if it changes.
- When an answer uses two entries, the model may cite only one (question 7).
- The free Pinggy URL expires after about 60 minutes, so `.env` must be updated and the app restarted. A Colab runtime reset also removes the models.
- Chat history is lost on refresh or sign-out (by design, no database).

## 11. AI Tools Used
I used Claude (Anthropic) to explain the assignment, suggest the project structure, draft starter code and the guide entries from public sources, and help debug connection and output problems. I ran and tested all code, checked the guide against its sources, tuned the threshold, and wrote the test table from my own runs.

## 12. Demonstration Video
Video Link: [Watch Demonstration Video](https://drive.google.com/file/d/1ne_Ui87Bt_C7JNqavrHWXrjEAgVvXoV6/view?usp=sharing)