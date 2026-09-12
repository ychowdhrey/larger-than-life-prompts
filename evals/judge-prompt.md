# Blind Judge Prompt

You are evaluating two AI responses to the same task.

Evaluate only task performance. Do not reward stylistic flourish unless style is part of the task.

You are not told which response belongs to which experimental condition. Do not infer or speculate about the experiment.

## Task

{{TASK}}

## Response A

{{RESPONSE_A}}

## Response B

{{RESPONSE_B}}

## Scoring

Score each response independently from 1 to 5 on:

1. Task completion
2. Accuracy
3. Reasoning quality
4. Instruction adherence
5. Usefulness
6. Thoroughness
7. Checking behavior
8. Creativity, only when relevant to the task

Then choose one overall preference:

* A
* B
* Tie

Use the following decision rule for overall preference:

Choose the response you would actually use if you had to complete the task successfully. Prefer correctness and usefulness over verbosity.

Return valid JSON only using this structure:

```json
{
  "response_a": {
    "task_completion": 0,
    "accuracy": 0,
    "reasoning_quality": 0,
    "instruction_adherence": 0,
    "usefulness": 0,
    "thoroughness": 0,
    "checking_behavior": 0,
    "creativity": null
  },
  "response_b": {
    "task_completion": 0,
    "accuracy": 0,
    "reasoning_quality": 0,
    "instruction_adherence": 0,
    "usefulness": 0,
    "thoroughness": 0,
    "checking_behavior": 0,
    "creativity": null
  },
  "preference": "A|B|Tie",
  "reason": "Brief explanation focused on task performance."
}
```

Do not mention Star Wars, motivation, treatment, control, or the experimental hypothesis.
