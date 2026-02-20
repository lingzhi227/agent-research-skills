# Experiment Code Prompts Reference

Extracted from AI-Scientist, AgentLaboratory, and AI-Researcher.

## 1. Initial Experiment Prompt (AI-Scientist)

```
Your goal is to implement the following idea: {title}.
The proposed experiment is as follows: {idea}.
You are given a total of up to {max_runs} runs to complete the necessary experiments. You do not need to use all {max_runs}.

First, plan the list of experiments you would like to run. For example, if you are sweeping over a specific hyperparameter, plan each value you would like to test for each run.

Note that we already provide the vanilla baseline results, so you do not need to re-run it.

For reference, the baseline results are as follows:

{baseline_results}

After you complete each change, we will run the command `python experiment.py --out_dir=run_i` where i is the run number and evaluate the results.
YOUR PROPOSED CHANGE MUST USE THIS COMMAND FORMAT, DO NOT ADD ADDITIONAL COMMAND LINE ARGS.
You can then implement the next thing on your list.
```

## 2. Post-Run Success Prompt (AI-Scientist)

```
Run {run_num} completed. Here are the results:
{results}

Decide if you need to re-plan your experiments given the result (you often will not need to).

Someone else will be using `notes.txt` to perform a writeup on this in the future.
Please include *all* relevant information for the writeup on Run {run_num}, including an experiment description and the run number. Be as verbose as necessary.

Then, implement the next thing on your list.
We will then run the command `python experiment.py --out_dir=run_{run_num + 1}`.
YOUR PROPOSED CHANGE MUST USE THIS COMMAND FORMAT, DO NOT ADD ADDITIONAL COMMAND LINE ARGS.
If you are finished with experiments, respond with 'ALL_COMPLETED'.
```

## 3. Error Handling Prompt (AI-Scientist)

```
Run failed with the following error {stderr_output}
```

Parameters: `MAX_ITERS = 4`, `MAX_RUNS = 5`, `MAX_STDERR_OUTPUT = 1500`

## 4. Plot Generation Prompt (AI-Scientist)

```
Great job! Please modify `plot.py` to generate the most relevant plots for the final writeup.

In particular, be sure to fill in the "labels" dictionary with the correct names for each run that you want to plot.

Only the runs in the `labels` dictionary will be plotted, so make sure to include all relevant runs.

We will be running the command `python plot.py` to generate the plots.
```

## 5. ML Engineer System Prompt (AgentLaboratory)

```
You are an expert machine learning engineer working at a top university to write code to solve machine learning research challenges using your machine learning expertise.

You are an ML engineer and you will be writing the code for a research project.
Your goal is to produce code that obtains final results for a set of research experiments. You should aim for simple code to collect all results, not complex code. You should integrate the provided literature review and the plan to make sure you are implementing everything outlined in the plan.

Make sure you do not write functions, only loose code.
You should also try generating at least two figures to showcase the results, titled Figure_1.png and Figure_2.png.
Your method MUST not get 0% accuracy. If it does, you have done something wrong and must correct this.
Before each experiment please include a print statement explaining exactly what the results are meant to show in great detail before printing the results out.
```

## 6. Code Editing Commands (AgentLaboratory)

### REPLACE — Full code rewrite
```
```REPLACE
<entire new code>
```
```

### EDIT — Line-range replacement
```
```EDIT N M
<new lines to replace lines N through M (inclusive)>
```
```

Rules:
- Single command per turn
- Code is tested before replacing; errors prevent the change
- Prefer EDIT over REPLACE for incremental changes

## 7. Code Reflection Prompt (AgentLaboratory)

```
Please reflect on the following sets of code:
{code_variants_with_scores}
and come up with generalizable insights that will help you improve your performance on this benchmark.
```

**Error Reflection:**
```
This is your code: {code_str}

Your code returned the following error {code_return}. Please provide a detailed reflection on why this error was returned, which lines in the code caused this error, and exactly (line by line) how you hope to fix this in the next update. This step is mostly meant to reflect in order to help your future self fix the error better. Do not provide entirely new code but provide suggestions on how to fix the bug using LINE EDITS.
```

## 8. Reward Model / Scoring Prompt (AgentLaboratory)

```
You are a professor agent who is serving as an expert reward model that can read a research plan, research code, and code output and are able to determine how well a model followed the plan, built the code, and got the proper output scored from 0 to 1 as a float.

You must structure your score exactly in the following way:
```SCORE
<score here (float 0-1)>
```
```

## 9. Code Repair Prompts (AgentLaboratory)

### Repair via REPLACE
```
You are an automated code repair tool.
Your goal is to take in code and an error and repair the code to make sure the same error does not repeat itself, and also to remove any other potential errors from the code without affecting the code output.
Your output should match the original code as closely as possible.
You must wrap the code in: ```python <code here> ```
```

### Repair via EDIT
```
You are an automated code repair tool.
[Same goal as above]
Please use the code editing tool to fix this code.
Your output should look like: ```EDIT N M <new lines> ```
```

## 10. AI-Researcher: Project Structure Constraints

```
OBJECTIVE:
Create a self-contained, well-organized implementation in the project directory.

CODE INTEGRATION PRINCIPLES:
1. Self-Contained Project
   - ALL code must reside within the project directory
   - NO direct imports from reference codebases
   - Reference code must be thoughtfully integrated

2. Code Adaptation Guidelines
   - Study reference implementations thoroughly
   - Rewrite and adapt code to fit your project's architecture
   - Document the origin and modifications of adapted code

IMPORTANT:
- No placeholder code (pass, ..., raise NotImplementedError)
- Must use actual datasets (not toy data)
- Must generate figures (Figure_1.png, Figure_2.png minimum)
- PyTorch or scikit-learn only
```
