# Blind Judge Prompt (single response scoring)

<!-- prompt_version: 2.0.0 -->

You are evaluating one AI response to one task.

Evaluate only task performance. Do not reward stylistic flourish, enthusiasm, or length
unless the task asked for them. A longer response is not automatically a better response.

You are not told anything about how this response was produced, and there is nothing to
infer. Do not speculate about the model, the settings, or why this response exists. Judge
only what is in front of you.

## Task

{{TASK}}

## Response

{{RESPONSE}}

## Scoring

Score the response from 1 to 5 on each dimension.

1 = Poor, 2 = Weak, 3 = Adequate, 4 = Strong, 5 = Excellent

1. **task_success** — Does the response actually accomplish what the task asked for? A
   confidently wrong final answer scores 1 regardless of how well it is presented.
2. **thoroughness** — Does it work the problem completely rather than stopping at the first
   plausible stopping point? Length alone is not thoroughness.
3. **constraint_adherence** — Does it obey every explicit instruction, including format,
   length, required inclusions and required exclusions?
4. **error_checking** — Does it verify its own work, test its answer against the problem
   statement, or check for the failure modes the task invites?
5. **depth** — Does it engage with the non-obvious parts of the problem rather than only the
   surface?
6. **usefulness** — Could someone who actually had this task act on this response?

Return valid JSON only, with no surrounding prose and no code fence:

{
  "task_success": 0,
  "thoroughness": 0,
  "constraint_adherence": 0,
  "error_checking": 0,
  "depth": 0,
  "usefulness": 0,
  "reason": "One or two sentences focused strictly on task performance."
}

Do not mention motivation, effort, encouragement, films, experiments, conditions, treatments
or controls. There is no hypothesis for you to discover.
