# Error Recovery

If a context reset occurs mid-implementation:

1. Read `{specsDir}/.state/implement-state.md`
2. Read the artifacts from the recorded paths
3. Check which criteria are done vs. pending
4. Verify the working branch matches expectations
5. Re-run the oracle pipeline to validate current state
6. Resume from the next pending criterion

The filesystem is memory, not the conversation.
