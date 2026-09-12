# Blind Judge Prompt (pairwise preference)

<!-- prompt_version: 2.0.0 -->
<!-- Version 1.0 of this file combined per-dimension scoring and pairwise preference in one
     call. From 2.0.0 the two are separated: per-response scoring lives in
     evals/judge-prompt-blind.md, and this file is pairwise only. Version 1.0 was never used
     to produce a result and remains recoverable in git history. -->

You are comparing two AI responses to the same task.

Evaluate only task performance. Do not reward stylistic flourish, enthusiasm, or length
unless the task asked for them. A longer response is not automatically a better response.

The two responses are labelled only as Response A and Response B. The labels carry no
meaning and were assigned at random. You are not told anything about how either response was
produced, and there is nothing to infer. Do not speculate.

## Task

{{TASK}}

## Response A

{{RESPONSE_A}}

## Response B

{{RESPONSE_B}}

## Decision

Choose the response you would actually use if you had to complete this task successfully.
Prefer correctness and usefulness over verbosity. Answer "Tie" only when you genuinely
cannot separate them on task performance.

Return valid JSON only, with no surrounding prose and no code fence:

{
  "preference": "A",
  "reason": "One or two sentences focused strictly on task performance."
}

"preference" must be exactly one of: "A", "B", "Tie".

Do not mention motivation, effort, encouragement, films, experiments, conditions, treatments
or controls. There is no hypothesis for you to discover.
