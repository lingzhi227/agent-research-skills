# Paper Assembly Orchestration Patterns

Extracted from AI-Scientist (launch_scientist.py), AI-Researcher (main_ai_researcher.py), and AgentLaboratory (ai_lab_repo.py).

## Pattern 1: Sequential Pipeline (AI-Scientist)

```python
# launch_scientist.py main loop:

# Phase 1: Idea Generation
ideas = generate_ideas(
    base_dir=base_dir,
    client=client,
    model=model,
    max_num_generations=MAX_NUM_GENERATIONS,
    num_reflections=NUM_REFLECTIONS,
)

# Phase 2: Novelty Check
for idea in ideas:
    novel = check_idea_novelty(
        idea=idea,
        max_num_iterations=10,
    )
    if not novel:
        continue

    # Phase 3: Experiments
    success = perform_experiments(idea, base_dir)
    if not success:
        continue

    # Phase 4: Writeup
    perform_writeup(idea, base_dir, client, model)

    # Phase 5: Review
    review = perform_review(
        paper_path=f"{base_dir}/latex/paper.pdf",
        model=model,
        num_reflections=5,
        num_reviews_ensemble=5,
    )
```

## Pattern 2: Multi-Agent State Broadcasting (AgentLaboratory)

```python
# ai_lab_repo.py — propagate results to all agents

def set_agent_attr(self, attr_name, value):
    """Broadcast an attribute to all agents in the lab."""
    for agent in self.agents:
        setattr(agent, attr_name, value)

# Usage during pipeline:
lab.set_agent_attr("literature_review", lit_review_text)
lab.set_agent_attr("research_plan", plan_json)
lab.set_agent_attr("dataset_code", code_str)
lab.set_agent_attr("experiment_results", results_dict)
lab.set_agent_attr("paper_sections", sections_dict)

# Each agent can access shared state:
class PhdAgent:
    def write_section(self, section_name):
        # Can reference self.experiment_results, self.literature_review, etc.
        pass
```

## Pattern 3: FlowModule Caching (AI-Researcher)

```python
# main_ai_researcher.py — cache each agent's output

class FlowModule:
    """Base class for cacheable pipeline stages."""

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir

    def run(self, input_data):
        cache_key = self._compute_cache_key(input_data)
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        result = self._execute(input_data)
        self._save_cache(cache_key, result)
        return result

    def _execute(self, input_data):
        raise NotImplementedError

# Pipeline with caching:
modules = [
    PlanAgent(cache_dir="cache/plan"),
    SurveyAgent(cache_dir="cache/survey"),
    CodeAgent(cache_dir="cache/code"),
    ExperimentAgent(cache_dir="cache/experiment"),
    WriteupAgent(cache_dir="cache/writeup"),
]

state = initial_input
for module in modules:
    state = module.run(state)  # Cached if previously computed
```

## Pattern 4: Copilot Mode Checkpoints (AgentLaboratory)

```python
# Human intervention at phase boundaries

PHASES = [
    "literature_review",
    "plan_formulation",
    "data_preparation",
    "running_experiments",
    "results_interpretation",
    "report_writing",
    "report_refinement",
]

for phase in PHASES:
    print(f"\n{'='*50}")
    print(f"Phase: {phase}")
    print(f"{'='*50}\n")

    result = execute_phase(phase, state)

    if copilot_mode:
        print(f"\nPhase '{phase}' complete.")
        print(f"Result preview: {result[:500]}...")

        action = input("Continue / Edit / Redo / Skip? ")
        if action == "Edit":
            result = get_human_edits(result)
        elif action == "Redo":
            result = execute_phase(phase, state)
        elif action == "Skip":
            continue

    state[phase] = result
    save_checkpoint(state, f"checkpoint_{phase}.json")
```

## Checkpoint File Format

```json
{
  "project_name": "my-paper",
  "created_at": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T14:30:00Z",
  "current_phase": "report_writing",
  "phases": {
    "literature_review": {
      "status": "completed",
      "output_file": "literature_review.json",
      "completed_at": "2024-01-15T10:30:00Z"
    },
    "plan_formulation": {
      "status": "completed",
      "output_file": "research_plan.json",
      "completed_at": "2024-01-15T11:00:00Z"
    },
    "data_preparation": {
      "status": "completed",
      "output_file": "data_prep.py",
      "completed_at": "2024-01-15T12:00:00Z"
    },
    "running_experiments": {
      "status": "completed",
      "output_file": "results.json",
      "completed_at": "2024-01-15T13:30:00Z"
    },
    "results_interpretation": {
      "status": "completed",
      "output_file": "analysis.json",
      "completed_at": "2024-01-15T14:00:00Z"
    },
    "report_writing": {
      "status": "in_progress",
      "output_file": null,
      "started_at": "2024-01-15T14:00:00Z"
    },
    "report_refinement": {
      "status": "pending"
    }
  },
  "artifacts": {
    "bib_file": "references.bib",
    "figures": ["Figure_1.png", "Figure_2.png"],
    "tables": ["table_comparison.tex"],
    "main_tex": "main.tex"
  }
}
```

## Phase Dependency Graph

```
literature_review
    ↓
plan_formulation
    ↓
data_preparation ──→ running_experiments
                          ↓
                    results_interpretation
                          ↓
                    report_writing ──→ report_refinement
                         ↑                    ↓
                    figure_generation    self_review
                    table_generation         ↓
                    citation_management  final_compilation
```

## Error Recovery

```python
# If a phase fails, recover from last checkpoint:
def recover_from_checkpoint(checkpoint_path):
    state = load_checkpoint(checkpoint_path)

    # Find the last completed phase
    last_completed = None
    for phase in PHASES:
        if state["phases"][phase]["status"] == "completed":
            last_completed = phase
        else:
            break

    # Resume from next phase
    resume_idx = PHASES.index(last_completed) + 1 if last_completed else 0

    for phase in PHASES[resume_idx:]:
        state = execute_phase(phase, state)
        save_checkpoint(state)

    return state
```
