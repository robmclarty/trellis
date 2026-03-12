# Git Usage Rules

Git is used ONLY for:
1. **Reading the current branch name** (`git branch --show-current`)
2. **Creating a new branch** (`git checkout -b <name>`)
3. **Switching branches** (`git checkout <name>`)
4. **Summarizing changes for the judge** (`git diff --stat`)

Git is NOT used for:
- Committing (the user decides when to commit)
- Stashing
- Pushing
- Any other git operation that modifies history or remote state

Do not make commits without explicit user acceptance. The user owns the git
history.
