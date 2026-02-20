# Experiment Code Patterns Reference

## Pattern 1: Experiment Execution Loop (AI-Scientist)

```python
MAX_ITERS = 4      # Max fix attempts per run
MAX_RUNS = 5       # Max experiment runs
MAX_STDERR_OUTPUT = 1500  # Truncate stderr

def perform_experiments(idea, folder_name, coder, baseline_results):
    current_iter = 0
    run = 1
    next_prompt = initial_prompt.format(...)

    while run < MAX_RUNS + 1:
        if current_iter >= MAX_ITERS:
            break
        coder_out = coder.run(next_prompt)
        if "ALL_COMPLETED" in coder_out:
            break
        return_code, next_prompt = run_experiment(folder_name, run)
        if return_code == 0:
            run += 1
            current_iter = 0
        current_iter += 1

def run_experiment(folder_name, run_num, timeout=7200):
    command = ["python", "experiment.py", f"--out_dir=run_{run_num}"]
    result = subprocess.run(command, cwd=cwd, stderr=subprocess.PIPE,
                           text=True, timeout=timeout)
    if result.returncode != 0:
        stderr_output = result.stderr[-MAX_STDERR_OUTPUT:]
        next_prompt = f"Run failed with the following error {stderr_output}"
    else:
        results = json.load(open(f"run_{run_num}/final_info.json"))
        results = {k: v["means"] for k, v in results.items()}
        next_prompt = f"Run {run_num} completed. Results: {results}"
    return result.returncode, next_prompt
```

## Pattern 2: Hill-Climbing Code Optimization (AgentLaboratory)

```python
def solve(self):
    num_attempts = 0
    best_pkg = None
    top_score = None

    while True:
        model_resp = query_model(
            system_prompt=self.system_prompt(),
            prompt=f"History: {self.history_str()}\nEnter a command: ",
            temp=1.0
        )
        cmd_str, code_lines, prev_code_ret, should_execute_code, score = \
            self.process_command(model_resp)

        if score is not None:
            if top_score is None or score > top_score:
                best_pkg = copy(code_lines), copy(prev_code_ret), ...
                top_score = score

        if num_attempts >= self.min_gen_trials and top_score is not None:
            break
        num_attempts += 1

    # Keep best code variant
    if top_score > self.best_codes[-1][1]:
        self.best_codes.append((copy(self.code_lines), copy(top_score), ...))
        self.best_codes.sort(key=lambda x: x[1], reverse=True)
        if len(self.best_codes) >= self.max_codes:
            self.best_codes.pop(-1)
            self.code_reflect = self.reflect_code()
```

## Pattern 3: Initial Code Generation with Error History (AgentLaboratory)

```python
def gen_initial_code(self):
    num_attempts = 0
    error_hist = []

    while True:
        if num_attempts == 0:
            err_hist = ""
        else:
            err = f"Previous command: {model_resp}. Error: {cmd_str}. " \
                  f"Do not repeat this error."
            error_hist.append(err)
            if len(error_hist) == 5:
                error_hist.pop(0)
            err_hist = "Error history:\n" + "\n".join(error_hist) + \
                      "\nDO NOT REPEAT THESE."

        model_resp = query_model(
            system_prompt=self.system_prompt(),
            prompt=f"{err_hist}\nUse ```REPLACE to create initial code: ",
            temp=1.0
        )
        cmd_str, code_lines, prev_code_ret, should_execute_code, score = \
            self.process_command(model_resp)
        if score is not None:
            break
        num_attempts += 1

    return code_lines, prev_code_ret, score
```

## Pattern 4: Code Reflection for Improvement (AgentLaboratory)

```python
def reflect_code(self):
    code_strs = "\n\n".join([
        f"Code variant:\n{code}\nScore: {score}"
        for code, score, _ in self.best_codes
    ])

    prompt = f"""Please reflect on ideas for how to improve your current code.
Examine the provided code and think very specifically (with precise ideas)
on how to improve performance, which methods to use, how to improve
generalization on the test set with line-by-line examples."""

    return query_model(prompt=prompt, system_prompt=system + code_strs)
```

## Pattern 5: Self-Contained Project Structure (AI-Researcher)

```
project/
├── data/
│   └── data_loader.py
├── model/
│   └── model.py
├── training/
│   └── trainer.py
├── testing/
│   └── evaluator.py
├── run_training_testing.py   # Entry point
├── config.yaml
└── requirements.txt
```

## Common Error Prevention Checklist

```
- Import everything you use
- Reflect on code before writing to catch bugs
- Use actual command names (EDIT, REPLACE), not the word COMMAND
- Under no circumstances use tensorflow or keras (use pytorch/sklearn)
- Make sure not to produce placeholder code
- Use seeds for reproducibility
- Include proper logging (print statements before results)
- Save results to JSON for downstream use
```
