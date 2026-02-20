# LLM-SR Patterns

Extracted from LLM-SR codebase (llmsr/pipeline.py, sampler.py, buffer.py, evaluator.py, config.py).

## LLM Instruction Prompt

```
You are a helpful assistant tasked with discovering mathematical function structures for scientific systems. Complete the 'equation' function below, considering the physical meaning and relationships of inputs.
```

## Multi-Island Evolutionary Algorithm

### Architecture Overview
```
Pipeline:
  ├── ExperienceBuffer (multi-island)
  │   ├── Island 0 → Clusters → Programs
  │   ├── Island 1 → Clusters → Programs
  │   ├── ...
  │   └── Island N → Clusters → Programs
  ├── Samplers (parallel LLM callers)
  │   └── get_prompt() → LLM → draw_samples()
  └── Evaluators (parallel execution)
      └── analyse(sample) → score → register()
```

### Main Loop (sampler.py)
```python
def sample(self):
    """Continuously gets prompts, samples programs, sends them for analysis."""
    while True:
        if self._max_sample_nums and self._global_samples_nums >= self._max_sample_nums:
            break

        prompt = self._database.get_prompt()
        samples = self._llm.draw_samples(prompt.code, self.config)

        for sample in samples:
            chosen_evaluator = np.random.choice(self._evaluators)
            chosen_evaluator.analyse(
                sample, prompt.island_id, prompt.version_generated)
```

## Prompt Construction (buffer.py)

### Versioned Function Sequence
Programs from an island are formatted as an improving sequence:

```python
def equation_v0(x, v, params):
    """Describe the acceleration of a damped oscillator."""
    return params[0] * x

def equation_v1(x, v, params):
    """Improved version of equation_v0."""
    return params[0] * x + params[1] * v

def equation_v2(x, v, params):
    """Improved version of equation_v1."""
    return params[0] * x + params[1] * v + params[2] * x**2

def equation_v3(x, v, params):
    """Improved version of equation_v2."""
    # LLM completes this
```

### Cluster-Based Selection
```python
def get_prompt(self):
    """Constructs prompt from island clusters."""
    signatures = list(self._clusters.keys())
    cluster_scores = np.array(
        [self._clusters[sig].score for sig in signatures])

    # Temperature-scheduled softmax
    period = self._cluster_sampling_temperature_period
    temperature = self._cluster_sampling_temperature_init * (
        1 - (self._num_programs % period) / period)
    probabilities = _softmax(cluster_scores, temperature)

    # Sample clusters weighted by score
    functions_per_prompt = min(len(self._clusters), self._functions_per_prompt)
    idx = np.random.choice(len(signatures), size=functions_per_prompt, p=probabilities)

    # Sort by score ascending (worst to best)
    implementations = [self._clusters[signatures[i]].sample_program() for i in idx]
    indices = np.argsort([self._clusters[signatures[i]].score for i in idx])
    sorted_implementations = [implementations[i] for i in indices]

    return self._generate_prompt(sorted_implementations)
```

## Softmax Sampling (buffer.py)

```python
def _softmax(logits, temperature):
    """Returns tempered softmax of 1D finite logits."""
    if not np.all(np.isfinite(logits)):
        raise ValueError(f'logits contains non-finite values')
    result = scipy.special.softmax(logits / temperature, axis=-1)
    # Fix numerical precision: ensure probabilities sum to 1
    index = np.argmax(result)
    result[index] = 1 - np.sum(result[0:index]) - np.sum(result[index + 1:])
    return result
```

### Within-Cluster Sampling (Shorter Programs Preferred)
```python
def sample_program(self):
    """Samples a program, giving higher probability to shorter programs."""
    normalized_lengths = (np.array(self._lengths) - min(self._lengths)) / (
        max(self._lengths) + 1e-6)
    probabilities = _softmax(-normalized_lengths, temperature=1.0)
    return np.random.choice(self._programs, p=probabilities)
```

## Island Reset Mechanism (buffer.py)

```python
def reset_islands(self):
    """Resets the weaker half of islands."""
    # Sort by best score (with noise to break ties)
    indices_sorted = np.argsort(
        self._best_score_per_island +
        np.random.randn(len(self._best_score_per_island)) * 1e-6)

    num_to_reset = self._config.num_islands // 2
    reset_ids = indices_sorted[:num_to_reset]
    keep_ids = indices_sorted[num_to_reset:]

    for island_id in reset_ids:
        # Create fresh island
        self._islands[island_id] = Island(...)
        self._best_score_per_island[island_id] = -float('inf')

        # Seed with best program from a surviving island
        founder_id = np.random.choice(keep_ids)
        founder = self._best_program_per_island[founder_id]
        self._register_program_in_island(founder, island_id, founder_scores)
```

**Reset trigger**: Every `reset_period` seconds (default: 4 hours).

## Fitness Evaluation (evaluator.py)

```python
def analyse(self, sample, island_id, version_generated):
    """Compile and execute the hypothesis sample."""
    new_function, program = _sample_to_program(
        sample, version_generated, self._template, self._function_to_evolve)

    scores_per_test = {}
    for current_input in self._inputs:
        test_output, runs_ok = self._sandbox.run(
            program, self._function_to_run, self._function_to_evolve,
            self._inputs, current_input, self._timeout_seconds)

        if runs_ok and test_output is not None:
            scores_per_test[current_input] = test_output

    if scores_per_test:
        self._database.register_program(new_function, island_id, scores_per_test)
```

### Score Reduction
```python
def _reduce_score(scores_per_test):
    """Average score across all test inputs."""
    return sum(scores_per_test.values()) / len(scores_per_test)
```

## Problem Specification Template

```python
"""Specification for [PROBLEM NAME]."""

import numpy as np
from scipy.optimize import minimize

@evaluate.run
def evaluate(data: dict) -> float:
    """Evaluate equation fitness on the dataset."""
    # Load data
    inputs = data['inputs']   # dict of input arrays
    targets = data['targets']  # target array

    # Optimize parameters using BFGS
    def loss(params):
        pred = equation(**inputs, params=params)
        return np.mean((pred - targets) ** 2)

    n_params = 10  # max parameters
    x0 = np.zeros(n_params)
    result = minimize(loss, x0, method='L-BFGS-B')

    # Return negative MSE (higher = better)
    return -result.fun

@equation.evolve
def equation(x: np.ndarray, v: np.ndarray,
             params: np.ndarray) -> np.ndarray:
    """Describe the acceleration of a damped nonlinear oscillator
    with a driving force.

    Args:
        x: position (N,)
        v: velocity (N,)
        params: learnable parameters (K,)

    Returns:
        acceleration (N,)
    """
    return params[0] * x
```

## Configuration Defaults (config.py)

```python
@dataclass
class ExperienceBufferConfig:
    functions_per_prompt: int = 2       # Previous equations in prompt
    num_islands: int = 10               # Population diversity
    reset_period: int = 4 * 60 * 60     # 4 hours between resets
    cluster_sampling_temperature_init: float = 0.1
    cluster_sampling_temperature_period: int = 30_000

@dataclass
class Config:
    experience_buffer: ExperienceBufferConfig
    num_samplers: int = 4               # Parallel LLM callers
    num_evaluators: int = 4             # Parallel evaluators
    samples_per_prompt: int = 4         # Samples per LLM call
    evaluate_timeout_seconds: int = 30  # Per-evaluation timeout
```

## Example Domains

| Domain | Inputs | Output | Paper |
|--------|--------|--------|-------|
| Damped oscillator | x, v | acceleration | Physics |
| Bacterial growth | density, substrate, temp, pH | growth rate | Biology |
| Stress-strain | strain, temperature | stress | Materials |
| Oscillator + time | t, x, v | acceleration | Physics |
