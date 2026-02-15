# Task: Code Review

Perform a thorough code review of the provided code or changes.

## Review Areas

1. **Correctness**
   - Does it meet the requirements?
   - Are there logical errors?
   - Will it work in all cases?

2. **Code Quality**
   - Is it readable and maintainable?
   - Does it follow project conventions?
   - Are names clear and descriptive?

3. **Edge Cases**
   - How does it handle errors?
   - What about invalid inputs?
   - Are there race conditions or timing issues?

4. **Security**
   - SQL injection, XSS, CSRF risks?
   - Proper input validation?
   - Sensitive data exposure?
   - Authentication/authorization issues?

5. **Performance**
   - Any obvious bottlenecks?
   - Unnecessary computations?
   - Database query efficiency?

6. **Testing**
   - Are tests adequate?
   - Do they cover edge cases?
   - Are they easy to understand?

## Output Format

Provide feedback as:
- ✅ **Strengths**: What's done well
- ⚠️ **Issues**: Problems that must be fixed
- 💡 **Suggestions**: Improvements to consider
- 🔍 **Questions**: Areas needing clarification

Be constructive and specific with examples.
