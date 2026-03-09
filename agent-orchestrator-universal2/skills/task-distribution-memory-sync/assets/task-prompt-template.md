Task T-XXX: <one-line summary>

What: <precise description — what to create, fix, or change>
Files: <exact file paths to create or modify>
Acceptance: <test command + expected output, or manual verification step>
Time budget: <15-30 min max>

Context (only if needed): <brief relevant info the worker needs>
Constraints: <conventions, limits, dependencies>

Load agent: @agents_library/<agent-name>.md

When done:
1) Update CLAUDE.md Task Assignment Queue: T-XXX -> COMPLETED
2) Add a Task Completion Log entry with:
   - Timestamp
   - Files touched (created, modified, deleted)
   - Test result (command run + output)
   - Notes (blockers encountered, decisions made)

---

## Examples

### Good: precise, testable, self-contained

```
Task T-012: Fix FlashcardBase schema missing matiere_id field

What: Add `matiere_id: Optional[int] = None` to FlashcardBase in the Pydantic schema.
Files: backend/app/schemas/flashcard.py
Acceptance: POST /api/flashcards/ with {"question":"test","reponse":"test","matiere_id":1} returns HTTP 201
Time budget: 15 min

Load agent: @agents_library/backend-architect.md

When done:
1) Update CLAUDE.md Task Assignment Queue: T-012 -> COMPLETED
2) Add a Task Completion Log entry with timestamp, files touched, test result, notes
```

### Good: build/compile verification task

```
Task T-020: Verify frontend compilation after proxy fix

What: Run TypeScript check and Next.js build in frontend/
Files: none (read-only verification)
Acceptance: `cd frontend && npx tsc --noEmit && npx next build` both exit code 0
Time budget: 15 min

Load agent: @agents_library/frontend-developer.md

When done:
1) Update CLAUDE.md Task Assignment Queue: T-020 -> COMPLETED
2) Add a Task Completion Log entry with build output summary
```

### Bad: too vague

```
Task T-099: Fix the backend
```
Why bad: which file? which bug? what's the expected behavior? Worker will waste time asking questions.

### Bad: too large

```
Task T-100: Implement the entire authentication system with JWT, password hashing, login/register routes, middleware, and frontend integration
```
Why bad: this is 5+ tasks in one. Split into atomic pieces: schema, route, middleware, frontend page, integration test.
