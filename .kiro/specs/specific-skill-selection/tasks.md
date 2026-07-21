# Implementation Tasks

## Task 1: Add `get_filtered_skill_tools()` to SkillManager

**File:** `src/OpenDEMON/skills/manager.py`

Add the `get_filtered_skill_tools(names, *, tool_executor=None)` method to `SkillManager`. It must:
- Accept a list of zero or more skill name strings
- Deduplicate names preserving insertion order (`dict.fromkeys`)
- Return `[]` immediately for an empty input list
- Call `self.resolve(name)` for each unique name (raises `KeyError` on missing)
- Construct `SkillTool` objects with the same executor/resolver wiring as `get_skill_tools()`
- Leave `get_skill_tools()` entirely unchanged for backward compatibility

### Sub-tasks
- [x] 1.1 Implement `get_filtered_skill_tools()` in `manager.py`
- [x] 1.2 Verify `get_skill_tools()` is unmodified (backward compat)

**Requirement refs:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

---

## Task 2: Create `src/OpenDEMON/skills/validation.py`

New file containing `UnknownSkillsError` and `resolve_skill_names()`.

`UnknownSkillsError(ValueError)`:
- `unknown_names: list[str]` — all unresolved names
- `catalog_empty: bool = False`
- `__str__` emits one line per unknown name: `"Unknown skill: '<name>'. Run 'DEMON skill list' to see installed skills."` plus, if `catalog_empty`, an extra line: `"No skills are installed. Run 'DEMON skill install' to add skills."`

`resolve_skill_names(names, skill_manager, *, catalog_is_empty=False) -> list[str]`:
- Deduplicates `names` preserving order
- Collects **all** names not in `skill_manager.skill_names()` into `unknown`
- If `unknown` is non-empty, raises `UnknownSkillsError(unknown, catalog_empty=catalog_is_empty)`
- Returns the deduplicated validated list on success

### Sub-tasks
- [x] 2.1 Implement `UnknownSkillsError` class
- [x] 2.2 Implement `resolve_skill_names()` function
- [x] 2.3 Export both from `__all__`

**Requirement refs:** 6.1, 6.2, 6.3, 6.4, 6.5

---

## Task 3: Add `--skill` / `--skills` options to `DEMON ask`

**File:** `src/OpenDEMON/cli/ask.py`

Add two new Click options to the `ask` command:
- `--skill` (repeatable, `multiple=True`, stored as `skill_names: tuple[str, ...]`)
- `--skills` (single comma-separated string, stored as `skills_shorthand: str | None`)

After config load and before the agent/engine is constructed, insert the merge + validate block:
1. Build `combined` from `skill_names` + split/trim `skills_shorthand`
2. Deduplicate with `dict.fromkeys`
3. If `combined` is non-empty, call `resolve_skill_names()` — on `UnknownSkillsError` print `[red]{exc}[/red]` to stderr and `sys.exit(1)`
4. Print `"[dim]Active skills: <names>[/dim]"` to stderr before the query runs
5. Call `skill_manager.get_filtered_skill_tools(active_skill_names)` and build filtered `catalog_xml` / `few_shot` using the helper functions defined in this task
6. If no skill options provided, fall back to existing full-catalog behavior

Add two private helpers to `ask.py`:
- `_build_catalog_xml_for_subset(skill_manager, names) -> str`
- `_build_few_shot_for_subset(skill_manager, names) -> list[str]`

Pass filtered `skill_catalog_xml` and `skill_few_shot_examples` to `SystemPromptBuilder`.

### Sub-tasks
- [x] 3.1 Add `--skill` and `--skills` Click options to `ask` command
- [x] 3.2 Implement merge/dedup/trim logic
- [x] 3.3 Integrate `resolve_skill_names()` validation with error output and `sys.exit(1)`
- [x] 3.4 Print active skill set to stderr before query
- [x] 3.5 Add `_build_catalog_xml_for_subset()` and `_build_few_shot_for_subset()` helpers
- [x] 3.6 Pass filtered data to `SystemPromptBuilder` and agent tool list

**Requirement refs:** 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4

---

## Task 4: Add `--skill` option to `DEMON chat`

**File:** `src/OpenDEMON/cli/chat_cmd.py`

Add the same `--skill` (repeatable) Click option to the `chat` command (no `--skills` shorthand needed for chat — singular `--skill` only per design).

Apply the same merge/dedup/validate pattern as `ask.py`:
1. Build `combined` from `skill_names` tuple
2. Deduplicate
3. If non-empty, call `resolve_skill_names()` — on error print and `sys.exit(1)` **before the REPL starts**
4. Display active skill names in the startup banner (before the REPL prompt)
5. Pass filtered `catalog_xml` / `few_shot` to `SystemPromptBuilder`
6. Pass filtered `SkillTool` list into `kwargs["tools"]` in the agent-wiring block

### Sub-tasks
- [x] 4.1 Add `--skill` Click option to `chat` command
- [x] 4.2 Implement merge/dedup/validate with pre-REPL error exit
- [x] 4.3 Display active skill names in startup banner
- [x] 4.4 Wire filtered tools and system prompt into agent construction

**Requirement refs:** 2.1, 2.2, 2.3, 2.4, 2.5

---

## Task 5: Add `skills` field to `ChatCompletionRequest`

**File:** `src/OpenDEMON/server/models.py`

Add one optional field to `ChatCompletionRequest`:

```python
skills: Optional[List[str]] = None
```

`None` and `[]` both mean "use full catalog". Non-empty list triggers filtering.

### Sub-tasks
- [x] 5.1 Add `skills: Optional[List[str]] = None` to `ChatCompletionRequest`

**Requirement refs:** 4.1

---

## Task 6: Skill filtering in the REST route handler

**File:** `src/OpenDEMON/server/routes.py`

In `chat_completions()`, after the existing memory/complexity blocks, add skill-selection logic:

1. Read `skill_manager = getattr(request.app.state, "skill_manager", None)`
2. If `skill_manager is not None` and `request_body.skills` is non-empty (after stripping empty strings):
   - Call `resolve_skill_names()` — on `UnknownSkillsError` raise `HTTPException(status_code=422, detail={"unknown_skills": exc.unknown_names, ...})`
   - Build `active_skill_tools`, `active_catalog_xml`, `active_few_shot` from the validated names
3. Thread these into the relevant `_handle_agent` / `_handle_direct` / streaming call paths **for this request only** — never mutate `skill_manager._skills`
4. If `skill_manager` is absent or `skills` is absent/empty, use existing full-catalog behavior unchanged

### Sub-tasks
- [x] 6.1 Add per-request skill validation block to `chat_completions()`
- [x] 6.2 Return HTTP 422 with `{"unknown_skills": [...]}` on unknown names
- [x] 6.3 Return HTTP 422 with `{"unknown_skills": [...], "detail": "No skills are installed."}` when catalog is empty
- [x] 6.4 Thread filtered skill data into agent/direct/stream call paths without mutating global state

**Requirement refs:** 4.1, 4.2, 4.3, 4.4, 6.2, 6.3, 6.5

---

## Task 7: Skill filtering in the WebSocket bridge

**File:** `src/OpenDEMON/server/ws_bridge.py`

Wherever an incoming WebSocket JSON message triggers an agent run, read the optional `"skills"` key:

1. If `"skills"` key is present and non-empty, call `resolve_skill_names()` on the value
2. On `UnknownSkillsError`, send back `{"type": "error", "unknown_skills": [...]}` and **do not** process the request
3. On success, apply `get_filtered_skill_tools()` before dispatching the agent run

### Sub-tasks
- [x] 7.1 Read `"skills"` key from incoming WebSocket JSON messages
- [x] 7.2 Send error JSON on unknown skill names without processing the request
- [x] 7.3 Apply `get_filtered_skill_tools()` on valid skill names before dispatch

**Requirement refs:** 4.5, 4.6

---

## Task 8: Property-based tests (Hypothesis)

**File:** `tests/test_skill_selection_properties.py` (new)

Implement all 8 Hypothesis property tests defined in the design document. Each test must:
- Be tagged with `# Feature: specific-skill-selection, Property N: <text>`
- Use `@settings(max_examples=100)`
- Use in-memory `SkillManifest` objects (no disk I/O)

Tests:
1. Filtered tools exactly match requested names
2. Unknown name always raises `KeyError`
3. All unknown names reported together via `UnknownSkillsError`
4. Overlay metadata preserved in filtered results
5. Deduplication — each tool appears at most once
6. CLI `--skill`/`--skills` merge and deduplication (test the pure merge function)
7. System prompt contains exactly the active skill set
8. API error reports all missing names (using FastAPI `TestClient`)

Include `_build_manager()`, `_build_manager_with_overlay()`, and `_build_xml_from_tuples()` fixtures/helpers.

### Sub-tasks
- [ ] 8.1 Create test file with shared helpers (`_build_manager`, etc.)
- [ ] 8.2 Implement Properties 1–5 (SkillManager layer)
- [ ] 8.3 Implement Property 6 (CLI merge/dedup pure function)
- [ ] 8.4 Implement Property 7 (SystemPromptBuilder)
- [ ] 8.5 Implement Property 8 (API via TestClient)
- [ ] 8.6 Run all property tests and confirm they pass

**Requirement refs:** All (validation coverage)

---

## Task 9: Unit and integration tests

**File:** `tests/test_skill_selection_unit.py` (new)

Example-based tests covering edge cases:

- `test_get_filtered_skill_tools_empty_list` — `[]` → `[]`
- `test_get_filtered_skill_tools_backward_compat` — `get_skill_tools()` unchanged
- `test_resolve_skill_names_all_valid` — returns deduplicated list
- `test_resolve_skill_names_empty_catalog_error` — empty catalog + any name → error with install note
- `test_cli_ask_no_skill_option` — omitting `--skill` loads full catalog
- `test_cli_ask_skills_shorthand_empty_string` — `--skills ""` treated as absent
- `test_cli_ask_unknown_skill_exits_nonzero` — bad skill name → non-zero exit
- `test_api_skills_null` — `skills: null` → full catalog, no 422
- `test_api_skills_empty_list` — `skills: []` → full catalog, no 422
- `test_api_skills_no_skill_manager` — missing `app.state.skill_manager` → field silently ignored

### Sub-tasks
- [ ] 9.1 Implement SkillManager unit tests
- [ ] 9.2 Implement CLI unit tests (using Click `CliRunner`)
- [ ] 9.3 Implement API unit tests (using FastAPI `TestClient`)
- [ ] 9.4 Run all unit tests and confirm they pass

**Requirement refs:** All
