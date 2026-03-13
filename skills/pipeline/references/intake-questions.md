# Pipeline intake questions

## Interactive mode: upfront questions

Ask:

1. What problem are you solving? (This seeds the pitch.)
2. What's the feature name? (kebab-case, becomes the folder name under `.specs/`)
3. Does this feature have compliance requirements? (If yes, which regulations? If unsure, the pipeline will try to detect this from the spec's data model.)
4. Are there any known ambiguities or open questions I should be aware of? (Data ownership, permissions, privacy concerns, integration points — this context helps the clarify and compliance stages resolve issues without needing to ask you mid-run, since they run in isolated contexts.)

## Auto mode: extended upfront questions

Ask all of the above, plus:

1. Walk me through the user experience. What does someone do with this feature, step by step?
2. What's the appetite? (Timeframe, team size, complexity budget)
3. Are there any specific technical decisions you've already made?
4. Does this integrate with an existing system? If so, describe the integration points.
5. Are there any known no-gos I should encode?
6. Any rabbit holes I should flag?
7. Anything else I should know that might affect the spec, plan, or compliance review?

Be thorough in this intake. Every question you skip here becomes a guess later. If the user's answers are thin in any area, push for more detail before proceeding. Once you start the auto run, you're committed to making all decisions yourself.
