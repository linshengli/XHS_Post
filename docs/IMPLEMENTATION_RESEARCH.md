# Implementation Research

## Goal

把项目从“脚本集合”推进到“module + workflow”的可维护结构，同时避免一次性重写造成回归。

## Sources Reviewed

- Python `dataclasses` 官方文档：<https://docs.python.org/3/library/dataclasses.html>
- Python `argparse` 官方文档：<https://docs.python.org/3/library/argparse.html>
- Pydantic Models 官方文档：<https://docs.pydantic.dev/latest/concepts/models/>
- Typer 官方文档：<https://typer.tiangolo.com/>

## Option Comparison

### Option A: Keep Standard Library First

Use:
- `dataclasses` for workflow request/response objects
- `argparse` for CLI entrypoints
- internal modules for topic parsing, storage, and paths

Pros:
- zero new runtime dependency
- fits current offline/restricted environment
- easy to layer on top of existing scripts
- lowest migration risk

Cons:
- weaker schema validation
- CLI ergonomics remain basic

### Option B: Add Pydantic for Config and Artifact Schemas

Use:
- `BaseModel` for persona schema, analysis snapshots, generation artifacts

Pros:
- stronger validation and clearer contracts
- better error surfacing for inconsistent YAML/JSON

Cons:
- new dependency
- migration work is larger because current persona schemas are not uniform

### Option C: Add Typer for Unified CLI

Use:
- `Typer()` app with subcommands for analyze, generate, validate, optimize

Pros:
- cleaner command tree
- built-in help and better UX for multiple workflows

Cons:
- new dependency
- not strictly necessary before domain modules are stabilized

## Recommendation

### Near-term

Adopt Option A now.

Reason:
- the current repo’s main problem is duplicated domain logic and blurry boundaries, not CLI cosmetics
- standard library is enough to establish module and workflow layers
- this keeps the first refactor slice small and safe

### Mid-term

Add Pydantic after persona schema normalization.

Reason:
- schema validation only pays off once the config model is made consistent

### Later

Add Typer after the workflow set is stable.

Reason:
- Typer helps when commands and subcommands multiply
- it is best introduced after domain responsibilities are already settled

## Implementation Strategy

1. Extract shared modules:
   - paths
   - topic parsing/filtering
   - storage helpers
2. Add workflow layer that orchestrates existing scripts without rewriting all business logic at once.
3. Migrate high-value scripts to the shared modules incrementally.
4. Normalize schema before introducing heavier validation or CLI frameworks.
