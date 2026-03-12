# Test Writer Sub-Agent

This file defines the sub-agent that writes targeted tests for tricky logic
while the main agent implements. Spawn this agent when acceptance criteria
involve edge cases, state transitions, permission logic, date/time math,
parsing, or any behavior where the type-checker alone won't catch errors.

## When to spawn this agent

During Phase 2, before or alongside writing implementation code, evaluate each
acceptance criterion (whether from tasks.md "Verify" sections, spec.md §8, or
sketch hypotheses). Spawn this agent for criteria that are:

- **Behavioral:** The criterion describes what should happen given specific
  inputs or conditions, not just what shape the output takes.
- **Edge-heavy:** The criterion involves boundaries, limits, or special cases
  (empty inputs, max values, concurrent access, timezone differences).
- **Stateful:** The criterion depends on prior state or transitions between
  states (e.g., a pass that expires, a user that gets deactivated mid-session).
- **Permission-dependent:** The criterion involves different behavior for
  different roles or scopes.
- **Non-obvious:** You can't tell whether the implementation is correct just by
  reading it. You need to run it.

Do NOT spawn this agent for:
- CRUD operations where the type system and schema validation cover correctness
- UI/formatting concerns
- Criteria that the LLM judge can assess from a file review

## What the test writer receives

Compose a message containing:

```markdown
## Spec Excerpt
<paste only the relevant acceptance criteria and any related constraints,
not the full spec. If working from tasks.md, paste the task's "Do" and
"Verify" sections plus any referenced spec sections.>

## Module Under Test
<the file path and a brief description of what it will do, even if it
doesn't exist yet. The test writer works from the spec, not from existing
implementation.>

## Project Context
<test framework and runner (from user's config, e.g., vitest, jest, pytest,
go test), import conventions, any test utilities or fixtures already in the
project, the path where tests should be written, any project-specific
patterns from guidelines.md>

## Existing Types (if available)
<paste relevant type definitions, validation schemas, or model definitions
that the tests should reference>
```

## Test writer system prompt

Use this as the system prompt when spawning the sub-agent:

```
You are a test writer. You write focused, minimal tests for specific
behaviors described in a specification. You are not writing tests for
coverage metrics. You are writing tests that serve as oracle signals —
each test encodes a single behavioral expectation that the implementation
must satisfy.

Rules:

1. Write tests BEFORE the implementation exists. Import from the expected
   module path. The tests will fail initially. That's the point.

2. Each test targets one specific behavior or edge case. Name it so that
   a failing test message tells you exactly what's wrong:
   - Good: "rejects pass request when pass type is expired"
   - Bad: "handles edge cases"

3. Use the types and schemas provided. Don't invent your own test types.
   If a validation schema exists for the input, use it or construct
   conforming objects directly.

4. Prefer procedural test style. No test classes. Use describe/it blocks
   (or the equivalent in the project's test framework). Keep setup inline
   unless three or more tests share identical setup, in which case use a
   factory function, not beforeEach.

5. Test the boundary, not the middle. If a value must be > 0, test 0 and
   -1, not 5. If a string has a max length, test at the limit and one
   past it.

6. For async operations, always test both the success path and at least
   one failure path. Use realistic error conditions, not contrived ones.

7. Mock external dependencies (database calls, HTTP requests, clock) but
   do not mock the module under test. If you're mocking the thing you're
   testing, the test is worthless.

8. For time-dependent logic, use fake timers or inject a clock function.
   Never depend on real wall-clock time.

9. Keep the test file self-contained. A reader should understand what
   behavior is being verified without reading the implementation.

10. Output ONLY the test file contents. No explanation, no preamble, no
    suggestions for the implementor. Just the code.

Respond with the complete test file, ready to write to disk.
```

## What the main agent does with the output

1. Write the test file to the appropriate path (following the project's
   test file conventions from the user's config).
2. Enable the test stage in the oracle pipeline if it wasn't already.
3. Scope the test command to run only the new test file during this iteration
   (e.g., `vitest run src/services/__tests__/passExpiration.test.ts` or
   `pytest tests/test_pass_expiration.py -v`).
4. The tests will fail initially because the implementation doesn't exist
   yet. This is expected. The main agent implements until they pass.
5. After all targeted tests pass, run the full test suite once as a
   regression check before proceeding to the judge.

## Parallel execution

This agent runs in an isolated context window. It does not see the main
agent's conversation history. It receives only what you pass to it.

The ideal workflow is:

```
Main agent (Phase 2, Step 1: Plan)
  ├── Identifies AC-3 and AC-7 as tricky/behavioral
  ├── Spawns test writer for AC-3 → receives test file → writes to disk
  ├── Spawns test writer for AC-7 → receives test file → writes to disk
  └── Begins implementing AC-3
      └── Runs oracle pipeline including the new tests
```

If the spec is small enough that only one or two criteria need tests,
spawn sequentially. Parallel spawning is for specs where three or more
criteria need targeted tests.

## Adapting to the project

Before spawning the test writer, collect relevant test setup info from:

1. The user's config answers (test framework, test command)
2. The project's guidelines.md (testing philosophy, conventions)
3. Existing test files in the project (if any) for patterns

Include what you find in the "Project Context" section of the message to
the test writer. If existing tests follow a specific pattern (factory
functions, custom matchers, shared fixtures), mention that so new tests
are consistent.

## Example: spawning for a pass expiration criterion

Acceptance criterion from tasks.md:
> Task 2.3 — Implement pass type expiration check
> **Verify:** Request with expired pass type returns 422 with expiration
> date and human-readable message.

Message to test writer:

```markdown
## Spec Excerpt
A hall pass request is rejected if the pass type's expiration date is in
the past. The response includes the expiration date and a human-readable
message.

## Module Under Test
src/services/passRequests.ts — will export a function
`createPassRequest(input: CreatePassRequestInput): Promise<PassRequest>`
that validates the pass type before creating.

## Project Context
- Test framework: vitest (configured via user)
- Tests go in: src/services/__tests__/
- Naming convention: <module>.test.ts
- No shared fixtures yet
- Use vi.useFakeTimers() for time-dependent tests
- Functional style preferred (from guidelines.md)

## Existing Types
import { z } from 'zod';

const createPassRequestInput = z.object({
  studentId: z.string().uuid(),
  passTypeId: z.string().uuid(),
  requestedBy: z.string().uuid(),
  notes: z.string().max(500).optional(),
});

type CreatePassRequestInput = z.infer<typeof createPassRequestInput>;

// PassType has an expiresAt field:
// expiresAt: Date | null (null means never expires)
```
