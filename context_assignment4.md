# Codex Context: Mini-Assignment 4 Orchestration Pipeline

## Project Goal

Build a **three-crew sequential pipeline** in Python using **CrewAI** for Mini-Assignment 4.

This project should implement a **stage-level multi-crew orchestration design**, not a shallow one-agent-per-crew relabeling. The pipeline should feel like a real workflow with meaningful separation of stages, clean data flow, retry logic, checkpointing, and resume support.

The overall pipeline theme is:

**News / Topic Credibility Pipeline**

Input can be:
- a topic string, or
- a short article / article summary / claim text

The pipeline should transform the input through three distinct crews:

1. **Intake Crew**
2. **Evaluation Crew**
3. **Reporting Crew**

---

## Assignment Requirements to Satisfy

The final solution must satisfy all of these:

### 1) Pipeline Design
- Use **at least 2 CrewAI crews** that run **in sequence**
- In this project, use **3 crews**
- Each crew must have:
  - at least **1 agent**
  - at least **1 task**
- Each crew should perform a **distinct stage**
- The output of one crew must feed into the next through:
  - `crew.kickoff(inputs={...})`

### 2) Orchestration Implementation
Implement a Python orchestrator in `pipeline.py` that:
- executes crews in sequence
- passes data from crew N to crew N+1
- logs each stage status:
  - started
  - completed
  - failed

### 3) Reliability Features
Implement:
- retry logic for transient failures
  - use **3 retries**
  - use delay / exponential backoff
- checkpointing
  - save completed stage outputs to `checkpoint.json`
  - save after each successful stage
- resume logic
  - on rerun, skip stages already present in the checkpoint
  - continue from the next incomplete stage

### 4) Prompt Log
The assignment requires a complete unedited prompt log, but Codex should only generate code and documentation scaffolding. The actual prompt log content will be added manually by the user.

### 5) Technical Constraints
- Use **only Python scripts** (`.py`)
- **No Jupyter notebooks**
- Load API credentials from `.env` using `python-dotenv`
- Never hard-code or expose API keys
- Keep implementation **clear, beginner-friendly, and simple**
- Prefer straightforward code over clever abstractions
- Avoid unnecessary complexity

---

## Assessment Criteria to Optimize For

The code and structure should be designed to score well on the following criteria:

### Pipeline Design (30%)
The pipeline should show:
- clear stage separation
- logical multi-crew structure
- clean data flow across stages

### Orchestration Implementation (35%)
The orchestrator should clearly demonstrate:
- correct crew sequencing
- correct data passing between crews
- visible status logging

### Reliability Features (25%)
The solution must clearly show:
- retries
- checkpoint saving
- resume / skip completed stages

### Prompt Log (10%)
A placeholder file / note is fine, but the user will fill in the final full prompt log manually.

---

## Recommended Project Design

Do **not** simply rename old individual agents into separate crews.

Instead, organize the project around **stage-level crews**.

### Crew 1: Intake Crew
Purpose:
- understand the input
- extract key claims and context
- prepare structured input for downstream evaluation

Suggested agents:
- **Topic Researcher**
- **Claim Extractor**

Suggested outputs:
- main topic
- summary of input
- key claims
- source / context notes
- a clean structured JSON-like string or dictionary for next stage

### Crew 2: Evaluation Crew
Purpose:
- assess credibility and evidence quality
- identify red flags, uncertainty, or missing support

Suggested agents:
- **Credibility Analyst**
- **Evidence Reviewer**

Suggested outputs:
- credibility assessment
- risk signals / red flags
- unsupported or weak claims
- confidence level
- recommended credibility label such as:
  - trustworthy
  - caution
  - suspicious

### Crew 3: Reporting Crew
Purpose:
- convert evaluation into a concise executive-friendly report

Suggested agents:
- **Executive Brief Writer**

Suggested outputs:
- short executive summary
- final credibility verdict
- recommended next action
- business-facing explanation

---

## Required Pipeline Flow

The pipeline should run in this order:

### Stage 1: Intake Crew
Input:
- user topic / article / claim

Output:
- structured research package

### Stage 2: Evaluation Crew
Input:
- stage 1 output

Output:
- structured credibility assessment

### Stage 3: Reporting Crew
Input:
- stage 2 output
- optionally also stage 1 output if helpful

Output:
- final executive report

---

## Data Passing Expectations

Keep data passing simple and explicit.

Recommended pattern:
- store each stage result as a string in the checkpoint
- pass the previous stage result into the next stage using:
  - `inputs={"previous_result": result}`
or clearer named keys like:
  - `inputs={"intake_result": ...}`
  - `inputs={"evaluation_result": ...}`

Prefer readable explicit names over overly generic naming when practical.

---

## File Deliverables to Generate

Generate the following files:

### 1. `pipeline.py`
Must contain:
- pipeline/orchestrator logic
- sequential execution of 3 crews
- retry logic
- checkpoint saving
- resume support
- clear stage status logging

### 2. `crews.py`
Must contain:
- CrewAI LLM setup using environment variables
- all agent definitions
- all task definitions
- all 3 crew definitions

### 3. `checkpoint.json`
Provide:
- an example checkpoint file from a successful run
- stage outputs can be sample placeholder outputs if needed

### 4. `output.txt`
Provide:
- sample full execution log
- should show stages starting, completing, or being skipped on resume

### 5. `README.md`
Keep to about one page max.
Must include:
- pipeline stages and what each crew does
- how to run the pipeline
- how checkpoint/resume works
- challenges encountered and how they were handled

### 6. `prompt-log.md`
Create as a placeholder with a note telling the user to paste the **complete, unedited AI chat history** manually.

### 7. `requirements.txt`
Include required dependencies only.

Recommended minimum:
- `crewai`
- `python-dotenv`

Add others only if truly needed.

---

## Expected Project Structure

Use a simple structure like this:

```text
assignment04/
├── .env
├── .gitignore
├── crews.py
├── pipeline.py
├── checkpoint.json
├── output.txt
├── README.md
├── prompt-log.md
└── requirements.txt
```

Do not add unnecessary folders or extra files unless needed.

---

## Environment Variable Requirements

Use `.env` and load it with `python-dotenv`.

Expected variables:

```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

The code should initialize CrewAI's native `LLM` using environment variables.

Do not expose the API key anywhere in generated files.

---

## Implementation Guidance

### In `crews.py`
Implement:
- `load_dotenv()`
- CrewAI `LLM(...)`
- agents, tasks, and crews

Use clear roles, goals, and backstories.

Suggested tone:
- professional
- business-oriented
- concise

### In `pipeline.py`
Implement a simple orchestrator class or function.

Suggested behavior:
1. load checkpoint if it exists
2. define ordered stages:
   - intake
   - evaluation
   - reporting
3. for each stage:
   - if already in checkpoint, print skip message and reuse stored result
   - otherwise:
     - log stage started
     - run crew with retries
     - save result to checkpoint immediately
     - log stage completed
4. return final state

### Retry Logic
Use:
- up to 3 attempts
- increasing delay, for example:
  - 1 second
  - 2 seconds
  - 4 seconds

If a stage fails after all retries:
- raise a clear error
- preserve existing checkpoint data

### Checkpoint Format
Use a simple JSON object such as:

```json
{
  "intake": "...stage 1 result...",
  "evaluation": "...stage 2 result...",
  "reporting": "...stage 3 result..."
}
```

Keep it simple and readable.

### Logging
Use plain `print()` logging only.
Do not introduce logging libraries.

Expected visible messages:
- `[START] intake`
- `[DONE] intake`
- `[FAIL] intake attempt 1: ...`
- `[SKIP] intake already completed`

Keep logs readable because `output.txt` must show full execution.

---

## Design Priorities

Prioritize the following:

1. **Correctness over sophistication**
2. **Clear stage separation**
3. **Simple, readable code**
4. **Reliable checkpoint and resume behavior**
5. **Easy-to-understand README**
6. **Business relevance**
7. **Minimal dependencies**

Avoid:
- overengineering
- async unless necessary
- unnecessary decorators / abstractions
- unnecessary helper modules
- overly fancy schemas

---

## Reuse Guidance from Previous Source Credibility Project

The previous project had a flow like:
- research
- credibility analysis
- executive brief

That logic can be reused **conceptually**, but in this assignment it should be redesigned as **three stage-level crews** rather than treating each old agent as a standalone crew with no internal collaboration.

That means:
- each crew should represent a meaningful workflow stage
- at least some crews should contain more than one agent when reasonable
- the orchestration should happen across crews, not just across individual agents

---

## Recommended Simplicity Level

This assignment is small. Keep scope controlled.

Good:
- 3 crews
- 1 orchestrator
- 1 checkpoint file
- 1 sample input flow
- readable outputs

Not necessary:
- external search APIs
- scraping
- Streamlit
- databases
- memory systems
- parallel orchestration

Use a fixed sample input in `pipeline.py` or a simple `main` block unless a better lightweight interface is clearly useful.

---

## Output Quality Expectations

Crew outputs do not need to be perfect, but they should be:
- structured enough for downstream stages
- consistent enough to demonstrate data flow
- realistic enough to show business use

The final report should feel like something a manager could read quickly.

---

## README Requirements

The `README.md` should include these sections:

1. **Project Overview**
2. **Pipeline Stages**
3. **Files**
4. **How to Run**
5. **Resume from Checkpoint**
6. **Challenges and Solutions**

Keep it concise.

---

## Output Log Requirements

The `output.txt` example should show something like:

- first full successful run
- or a resume run where earlier stages are skipped

It should clearly demonstrate:
- sequencing
- retries if any
- checkpoint/resume behavior

---

## Final Instruction to Codex

Build a complete, clean, beginner-friendly implementation of this assignment in Python.

Focus on:
- meeting the rubric exactly
- making the orchestration logic obvious
- making the checkpoint/resume behavior easy to test
- keeping the code small, readable, and practical

Do not overcomplicate the project.
