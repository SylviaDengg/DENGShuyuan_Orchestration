# Mini-Assignment 4 Orchestration Pipeline

This project implements a three-crew sequential CrewAI pipeline to evaluate the credibility of a topic, claim, or short article and produce a concise executive report.

## Orchestration
Orchestration in this project refers to coordinating multiple crews into a single workflow. The pipeline runs three crews sequentially (intake → evaluation → reporting), where each stage’s output is passed as input to the next. The orchestrator in `pipeline.py` manages execution order, handles failures with retry logic (up to 3 attempts with backoff), saves intermediate results to `checkpoint.json`, and supports resume by skipping completed stages on rerun. This ensures the pipeline is reliable, stateful, and efficient.

## Pipeline Stages
- `intake`: turns the raw topic, article, or claim text into a structured intake package
- `evaluation`: reviews the intake package and produces a credibility assessment
- `reporting`: turns the evaluation into a short executive-facing report

## How to Run
1. Create a `.env` file with:
   ```env
   DEEPSEEK_API_KEY=your_key_here
   DEEPSEEK_API_BASE=https://api.deepseek.com
   DEEPSEEK_MODEL=deepseek-chat
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the pipeline:
   ```bash
   python pipeline.py "Paste a topic, claim, or short article here"
   ```
Accepted input:
- claim example: "Coffee cures cancer"
- topic example: "AI regulation in US tech companies"
- short article/paragraph (1–5 sentences recommended)

## Checkpoint and Resume
- Completed stage outputs are saved to `checkpoint.json`
- On rerun, completed stages are skipped only when the saved checkpoint claim matches the current input claim
- If a stage fails, earlier successful stages remain saved
- Retry logic uses up to 3 attempts with delays of 1, 2, and 4 seconds

## Deliverable Notes
- `output.txt` should be created from a real end-to-end run of the pipeline
- `prompt-log.md` should stay empty until the full unedited AI chat history is ready to paste

## Challenges and Handling
- Crew tasks explicitly reference their input keys so each stage is grounded in the right upstream data
- The orchestrator keeps the logic simple by handling retries, checkpointing, and resume in one file
