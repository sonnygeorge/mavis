# MAVIS – Agent conventions

## Layout

- **Package**: `src/mavis/` (Python 3.11).
- **Prompts**: Jinja2 `.txt` templates in `src/mavis/prompts/`; loaded via `constants.PROMPTS_DIR_PATH`.
- **Data**: `data/` (e.g. `data/objaverse/` for Blender shapes).
- **Tests**: `tests/mavis/` mirrors `src/mavis/`; run with `pytest` (pythonpath: `src`).

## Conventions

- **Readable strings**: Models used in prompts implement `as_readable_string()` and return a single string for LLM/prompt use.
- **Prompt rendering**: One `render_*_prompt(...)` per task; each returns a `PromptPair(system=..., user=...)` and passes only simple types (e.g. strings, list of strings) into Jinja `render()`.
- **Paths / config**: Centralized in `constants.py`; paths derived from `Path(__file__).resolve().parent` under the package.
- **Tests**: pytest; shared data via fixtures (e.g. `action_scene`, `action_scene_specs`); test modules named `test_<module>.py`.

## Tooling

- Dependency and lockfile: `pyproject.toml` + `uv.lock` (use `uv` for install/sync).
