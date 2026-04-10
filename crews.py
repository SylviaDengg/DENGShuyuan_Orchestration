import os
from typing import Any, Tuple


def _load_environment() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "python-dotenv is not installed. Run `pip install -r requirements.txt` first."
        ) from exc

    load_dotenv()


def _import_crewai() -> Tuple[Any, Any, Any, Any, Any]:
    try:
        from crewai import Agent, Crew, LLM, Process, Task
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "CrewAI is not installed. Run `pip install -r requirements.txt` first."
        ) from exc

    return Agent, Crew, LLM, Process, Task


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _normalize_model_name(model_name: str) -> str:
    if "/" in model_name:
        return model_name
    return f"deepseek/{model_name}"


def build_llm() -> Any:
    _load_environment()
    _, _, LLM, _, _ = _import_crewai()

    api_key = _require_env("DEEPSEEK_API_KEY")
    base_url = _require_env("DEEPSEEK_API_BASE")
    model_name = _normalize_model_name(_require_env("DEEPSEEK_MODEL"))

    return LLM(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,
    )


def get_intake_crew() -> Any:
    Agent, Crew, _, Process, Task = _import_crewai()
    llm = build_llm()

    topic_researcher = Agent(
        role="Topic Researcher",
        goal="Understand the main topic, background, and context in the user input.",
        backstory=(
            "You are a careful research assistant who turns messy article snippets, claims, "
            "and topic notes into clear business-ready background context."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    claim_extractor = Agent(
        role="Claim Extractor",
        goal="Extract the main claims from the input and package them clearly for evaluation.",
        backstory=(
            "You specialize in spotting the central claims, statements, and implied assertions "
            "inside short news items or topic summaries."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    topic_context_task = Task(
        description=(
            "Review the raw input provided in {raw_input}. Use only the information found in "
            "{raw_input} to identify the main topic, the surrounding context, and why the "
            "content matters. Write a short research note that is grounded directly in "
            "{raw_input}."
        ),
        expected_output=(
            "A concise research note that summarizes the topic, context, and notable discussion "
            "points contained in {raw_input}."
        ),
        agent=topic_researcher,
    )

    intake_package_task = Task(
        description=(
            "Using the same raw input {raw_input} and the research note from the previous task, "
            "extract the key claims and convert the result into a valid JSON string. Base every "
            "field on {raw_input}. The JSON must contain exactly these keys: topic, "
            "input_summary, key_claims, context_notes."
        ),
        expected_output=(
            'A valid JSON string with exactly these keys: "topic", "input_summary", '
            '"key_claims", and "context_notes". The "key_claims" value must be a JSON array '
            "of short claim strings."
        ),
        agent=claim_extractor,
    )

    return Crew(
        agents=[topic_researcher, claim_extractor],
        tasks=[topic_context_task, intake_package_task],
        process=Process.sequential,
        verbose=True,
    )


def get_evaluation_crew() -> Any:
    Agent, Crew, _, Process, Task = _import_crewai()
    llm = build_llm()

    credibility_analyst = Agent(
        role="Credibility Analyst",
        goal="Assess the overall credibility of the claims in the intake package.",
        backstory=(
            "You are a business-focused credibility reviewer who looks for balance, certainty, "
            "and the overall trustworthiness of a topic package."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    evidence_reviewer = Agent(
        role="Evidence Reviewer",
        goal="Highlight missing support, weak reasoning, and risk signals in the claims.",
        backstory=(
            "You specialize in finding unsupported statements, overconfident claims, and other "
            "signals that suggest caution."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    credibility_review_task = Task(
        description=(
            "Analyze the structured intake package provided in {intake_result}. Your review must "
            "be derived directly from {intake_result}. Identify the overall credibility picture, "
            "the strongest signs of support, and the biggest uncertainty areas."
        ),
        expected_output=(
            "A concise evaluation note describing the credibility of the material in "
            "{intake_result}, including the major strengths and uncertainties."
        ),
        agent=credibility_analyst,
    )

    evaluation_package_task = Task(
        description=(
            "Using the same intake package {intake_result} and the previous credibility review, "
            "produce a valid JSON string that summarizes the credibility assessment. The JSON "
            "must contain exactly these keys: credibility_assessment, red_flags, "
            "unsupported_claims, confidence_level, credibility_label. Base every field on "
            "{intake_result}."
        ),
        expected_output=(
            'A valid JSON string with exactly these keys: "credibility_assessment", '
            '"red_flags", "unsupported_claims", "confidence_level", and '
            '"credibility_label". The "red_flags" and "unsupported_claims" values must be '
            "JSON arrays."
        ),
        agent=evidence_reviewer,
    )

    return Crew(
        agents=[credibility_analyst, evidence_reviewer],
        tasks=[credibility_review_task, evaluation_package_task],
        process=Process.sequential,
        verbose=True,
    )


def get_reporting_crew() -> Any:
    Agent, Crew, _, Process, Task = _import_crewai()
    llm = build_llm()

    executive_brief_writer = Agent(
        role="Executive Brief Writer",
        goal="Turn the analysis into a concise and practical business-facing report.",
        backstory=(
            "You write short executive updates that explain the situation, the risk level, "
            "and the recommended next step in plain language."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    reporting_task = Task(
        description=(
            "Create the final report using the evaluation package {evaluation_result}. Also use "
            "the intake package {intake_result} to keep the report grounded in the original "
            "topic and claims. The report must clearly reflect both {evaluation_result} and "
            "{intake_result}."
        ),
        expected_output=(
            'A valid JSON string with exactly these keys: "executive_summary", "verdict", '
            '"recommended_action", and "business_explanation".'
        ),
        agent=executive_brief_writer,
    )

    return Crew(
        agents=[executive_brief_writer],
        tasks=[reporting_task],
        process=Process.sequential,
        verbose=True,
    )
