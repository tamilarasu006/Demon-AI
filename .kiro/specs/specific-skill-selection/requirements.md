# Requirements Document

## Introduction

OpenDemon currently loads and exposes all discovered skills to the agent automatically. Users have no way to target a specific skill when invoking the system via the CLI (`DEMON ask`, `DEMON chat`) or the REST/WebSocket API. This feature adds a skill selection mechanism so that a user can explicitly request one or more named skills — scoping the agent's available capabilities to precisely those skills — instead of the full catalog.

The feature spans three layers:
1. **CLI** — new `--skill` option on `DEMON ask` and `DEMON chat`.
2. **SkillManager** — a filtered view that returns only the requested skills as tools.
3. **REST API** — the `/v1/chat` and WebSocket endpoints accept an optional `skills` field to apply the same filtering server-side.

## Glossary

- **Skill**: A reusable, named pipeline of tool steps described by a `SkillManifest`. Skills are stored as `skill.toml` or `SKILL.md` files and discovered at runtime by `SkillManager`.
- **Skill_Selector**: The component (a new helper within `SkillManager`) responsible for resolving a list of requested skill names into validated `SkillManifest` objects.
- **Skill_Catalog**: The full set of skills discovered from all configured paths and registered in `SkillManager`.
- **Active_Skill_Set**: The subset of skills made available to an agent for a single invocation, derived by filtering the Skill_Catalog with the user-provided skill names.
- **CLI**: The OpenDemon command-line interface (`DEMON ask`, `DEMON chat`, `DEMON skill`).
- **Agent**: A running instance of an OpenDemon agent (e.g. `orchestrator`, `native_react`) that receives tools and a system prompt.
- **System_Prompt_Builder**: The `SystemPromptBuilder` class in `OpenDEMON.prompt.builder` that assembles the agent's system prompt including the available-skills catalog.

## Requirements

### Requirement 1: CLI Skill Selection for `DEMON ask`

**User Story:** As a developer, I want to pass `--skill <name>` when running `DEMON ask`, so that only the specified skill(s) are loaded into the agent instead of the full catalog.

#### Acceptance Criteria

1. THE `DEMON ask` CLI SHALL accept a repeatable `--skill` option that takes a single skill name (a lowercase kebab-case string of at most 64 characters) per use, accepting between 1 and 50 skill names per invocation.
2. WHEN the user provides one or more `--skill` options, THE CLI SHALL pass the deduplicated list of skill names to the agent runtime, loading only those skills into the Active_Skill_Set and excluding all other discovered skills from the set available to the agent for that session.
3. IF one or more skill names provided via `--skill` do not match any skill in the Skill_Catalog, THEN THE CLI SHALL print an error message of the form `"Unknown skill: '<name>'. Run 'DEMON skill list' to see installed skills."` for all unrecognized names together in a single output, and exit with a non-zero status code without launching the agent.
4. WHEN no `--skill` option is provided, THE CLI SHALL load all discovered skills from the configured skill paths, preserving existing default behavior.
5. WHEN the user provides one or more `--skill` options, THE CLI SHALL print the names of all skills in the Active_Skill_Set to stderr in the startup output before the first query is submitted to the agent.

---

### Requirement 2: CLI Skill Selection for `DEMON chat`

**User Story:** As a developer, I want to pass `--skill <name>` when starting `DEMON chat`, so that the interactive session uses only the specified skill(s).

#### Acceptance Criteria

1. THE `DEMON chat` CLI SHALL accept a repeatable `--skill` option that takes a single skill name (a lowercase kebab-case string of at most 64 characters) per use.
2. WHEN the user provides one or more `--skill` options, THE CLI SHALL restrict the Active_Skill_Set for that session to the named skills, deduplicating any repeated names so that each skill appears at most once in the Active_Skill_Set.
3. IF a skill name provided via `--skill` does not match any skill in the Skill_Catalog, THEN THE CLI SHALL print an error message of the form `"Unknown skill: '<name>'. Run 'DEMON skill list' to see installed skills."` for each unrecognized name, and exit with a non-zero status code before the REPL starts.
4. WHEN no `--skill` option is provided, THE `DEMON chat` CLI SHALL load all skills in the Skill_Catalog into the Active_Skill_Set, preserving the existing default behavior.
5. WHEN the user provides one or more `--skill` options, THE `DEMON chat` CLI SHALL display the names of all skills in the Active_Skill_Set in the startup output before the REPL prompt appears.

---

### Requirement 3: SkillManager Filtered Tool Resolution

**User Story:** As a developer integrating with the skills subsystem, I want `SkillManager` to expose a method that returns only the requested skills as `BaseTool` objects, so that any caller can scope the skill set without reimplementing name-based filtering.

#### Acceptance Criteria

1. THE `Skill_Selector` SHALL expose a method `get_filtered_skill_tools(names)` that accepts a list of zero or more skill name strings and returns only the `SkillTool` instances whose manifest name appears in that list.
2. WHEN `get_filtered_skill_tools` is called with a name that does not exist in the Skill_Catalog, THEN THE `Skill_Selector` SHALL raise a `KeyError` identifying the missing skill name.
3. WHEN `get_filtered_skill_tools` is called with an empty list, THEN THE `Skill_Selector` SHALL return an empty list of tools without error.
4. THE `Skill_Selector` SHALL preserve the existing `get_skill_tools()` method with unmodified behavior to maintain backward compatibility.
5. WHEN `get_filtered_skill_tools` is called, THE `Skill_Selector` SHALL apply overlay metadata (description, few_shot) and run dependency validation against the full Skill_Catalog to the selected subset, in the same way that `get_skill_tools()` does for the full catalog.
6. WHEN `get_filtered_skill_tools` is called with a list containing duplicate skill names, THE `Skill_Selector` SHALL deduplicate the names and return each matching `SkillTool` at most once.

---

### Requirement 4: API Skill Selection

**User Story:** As a developer using the REST API, I want to specify a list of skills in my request payload, so that the agent activated for that request uses only the specified skills.

#### Acceptance Criteria

1. THE REST API chat endpoint SHALL accept an optional `skills` field in the request body, accepting a list of skill name strings.
2. WHEN the `skills` field is present and non-empty, THE API SHALL restrict the Active_Skill_Set to the named skills for that request only, without mutating the global Skill_Catalog.
3. IF a skill name in the `skills` field does not exist in the Skill_Catalog, THEN THE API SHALL return an HTTP 422 response with a body containing the field `"unknown_skills"` as a list of all unrecognized names.
4. IF the `skills` field is absent or is an empty list, THEN THE API SHALL load all skills from the Skill_Catalog into the Active_Skill_Set for that request, preserving current behavior.
5. WHEN the `skills` field is present and non-empty in a WebSocket chat message, THE WebSocket endpoint SHALL restrict the Active_Skill_Set to the named skills for that message, applying the same validation and filtering as the REST endpoint.
6. IF a skill name in a WebSocket chat message's `"skills"` key does not exist in the Skill_Catalog, THEN THE WebSocket endpoint SHALL send an error message containing the field `"unknown_skills"` as a list of all unrecognized names and SHALL NOT process the request.

---

### Requirement 5: System Prompt Reflects Active Skill Set

**User Story:** As a user, I want the agent's system prompt to list only the skills it has access to in the current session, so that the model does not hallucinate skill invocations for unavailable skills.

#### Acceptance Criteria

1. WHEN an Active_Skill_Set containing one or more skills is passed to the `System_Prompt_Builder` (derived from CLI `--skill` or API `skills` field), THE `System_Prompt_Builder` SHALL include only those skills in the `## Available Skills` section of the system prompt, omitting all skills not present in the Active_Skill_Set.
2. WHEN no Active_Skill_Set is provided and one or more skills are discovered from the Skill_Catalog, THE `System_Prompt_Builder` SHALL include all discovered skills in the `## Available Skills` section, preserving existing behavior.
3. WHEN the Active_Skill_Set resolves to zero entries, THE `System_Prompt_Builder` SHALL omit the `## Available Skills` section from the system prompt entirely.
4. IF an Active_Skill_Set is passed to the `System_Prompt_Builder`, THEN THE `System_Prompt_Builder` SHALL derive the `## Available Skills` section content exclusively from that Active_Skill_Set, with no entries drawn from the broader Skill_Catalog.

---

### Requirement 6: Skill Name Validation and Error Reporting

**User Story:** As a user, I want clear error messages when I specify a skill name that does not exist, so that I can quickly identify and correct typos or installation gaps.

#### Acceptance Criteria

1. WHEN an invalid skill name is specified via CLI, THEN THE CLI SHALL display an error message of the form: `"Unknown skill: '<name>'. Run 'DEMON skill list' to see installed skills."` before exiting.
2. WHEN an invalid skill name is specified via the API, THEN THE API SHALL return an HTTP 422 response body containing the field `"unknown_skills"` as a list of the unrecognized names.
3. WHEN multiple invalid skill names are provided via CLI or API, THE error report SHALL list all invalid names together in a single error message or response, rather than reporting only the first.
4. IF the Skill_Catalog is empty (no skills installed) and an invalid skill name is specified via CLI, THEN THE CLI SHALL append a note to the error message directing the user to install skills using `DEMON skill install`.
5. IF the Skill_Catalog is empty (no skills installed) and a non-empty `skills` field is provided via the API, THEN THE API SHALL return an HTTP 422 response body containing the field `"unknown_skills"` listing all requested names, plus a `"detail"` field noting that no skills are installed.

---

### Requirement 7: Skill Selection via `DEMON ask --skills` Shorthand

**User Story:** As a power user, I want to be able to pass a comma-separated list of skill names in a single `--skills` option for `DEMON ask`, so that I can specify multiple skills concisely on one line.

#### Acceptance Criteria

1. THE `DEMON ask` CLI SHALL accept a `--skills` option (plural) that takes a single comma-separated string of skill names as its value.
2. WHEN both `--skill` (repeatable) and `--skills` (comma-separated) are provided, THE CLI SHALL merge the two lists, deduplicating any repeated names, and use the combined set as the Active_Skill_Set.
3. WHEN the `--skills` value contains whitespace around commas (e.g. `"arxiv, summarize"`), THE CLI SHALL trim whitespace from each name before validation.
4. WHEN the `--skills` option is provided with an empty string, THE CLI SHALL treat it as if `--skills` was not provided and load the full Skill_Catalog.
