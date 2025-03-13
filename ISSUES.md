# Issue: Session Management and History Awareness Bugs in Context-Extended AI Software Development Agent

## Problem Description
Multiple issues have been identified with the session management and history awareness functionality, as well as project deletion:

1. The AI Development Agent fails to correctly utilize session history when asked to summarize a conversation. Instead of referencing the actual interaction history, it retrieves and presents unrelated content from the vector database.

2. The `generate` command does not verify or automatically create a session when executed, leading to a disjoint user experience.

3. Commands executed before session creation appear in the session history after a session is created, causing confusion and duplicate entries.

4. Project deletion fails to properly clean up associated tags, leading to unique constraint violations when trying to recreate projects with the same name and tags.

## Reproduction Steps

### Issue 1: Session History Awareness Bug
1. Create a project:
   ```bash
   devagent project create "a first human hello world test" --tags flask python
   ```

2. Generate a simple hello world example:
   ```bash
   devagent generate "create a simple hello world example" --project-id a-first-human-hello-world-test --output result.py
   ```

3. Create a session linked to the project:
   ```bash
   devagent session create "test" --project-id a-first-human-hello-world-test
   ```

4. Generate another hello world example within the session:
   ```bash
   devagent generate "create a simple hello world example" --project-id a-first-human-hello-world-test
   ```

5. Verify session history is captured:
   ```bash
   devagent session history
   ```

6. Ask to extend the code to a web application:
   ```bash
   devagent generate "now change that file and make it a web application using bootstrap for a very nice output" --project-id a-first-human-hello-world-test
   ```

7. Request a conversation summary:
   ```bash
   devagent generate "can you summarize our conversation so far? can you give me a file structure of our project?" --project-id a-first-human-hello-world-test
   ```

### Issue 2: Missing Session Auto-Creation
1. Create a project:
   ```bash
   devagent project create "test project" --tags test
   ```

2. Generate code without creating a session first:
   ```bash
   devagent generate "write a simple function" --project-id test-project
   ```
   
3. Note there's no warning or automatic session creation.

### Issue 3: Pre-Session Commands in History
1. Create a project:
   ```bash
   devagent project create "test project" --tags test
   ```

2. Generate code without a session:
   ```bash
   devagent generate "write a function" --project-id test-project
   ```

3. Create a session:
   ```bash
   devagent session create "test session" --project-id test-project
   ```

4. Check session history:
   ```bash
   devagent session history
   ```

5. Note that the command from step 2 appears in history, despite being executed before the session was created.

### Issue 4: Project Deletion Tag Cleanup
1. Create a project with tags:
   ```bash
   devagent project create "test-conversation-summary" --tags test
   ```

2. Delete the project:
   ```bash
   devagent project delete test-conversation-summary
   ```

3. Try to recreate the same project with the same tags:
   ```bash
   devagent project create "test-conversation-summary" --tags test
   ```

4. The operation fails with a unique constraint error:
   ```
   Error: UNIQUE constraint failed: project_tags.project_id, project_tags.tag
   ```

## Expected Behavior

### Issue 1: Session History Awareness
The agent should provide a summary of the actual conversation history, including:
- Creating a simple hello world example
- Extending it to a web application using Bootstrap
- The file structure should reflect the Flask application created

### Issue 2: Session Auto-Creation
The agent should:
- Either automatically create a session when executing commands that benefit from session context
- Or warn the user that no session is active and suggest creating one
- Provide an option to auto-create a session with a flag like `--auto-create-session`

### Issue 3: Pre-Session Commands in History
- Session history should only include commands that were executed after session creation
- Commands executed before the session was created should not appear in the history

### Issue 4: Project Deletion Tag Cleanup
- Project deletion should properly clean up all associated data, including tags
- After deleting a project, it should be possible to create a new project with the same name and tags
- No unique constraint violations should occur during project recreation

## Actual Behavior

### Issue 1: Session History Awareness
The agent presents an unrelated summary about a `DataLoader` class and provides a file structure that doesn't match the created application. Log output shows parsing errors:

```
2025-03-13 21:34:56,653 - context_selector - WARNING - Failed to parse code: unindent does not match any outer indentation level (<unknown>, line 4)
2025-03-13 21:34:56,653 - context_selector - WARNING - Failed to parse code: unindent does not match any outer indentation level (<unknown>, line 4)
2025-03-13 21:34:56,653 - context_selector - WARNING - Failed to parse code: unindent does not match any outer indentation level (<unknown>, line 4)
```

### Issue 2: Session Auto-Creation
The `generate` command executes without checking for an active session or offering to create one, leading to a disjointed experience where users must manually create sessions.

### Issue 3: Pre-Session Commands in History
Commands executed before session creation appear in the session history after a session is created, causing duplicate entries and incorrect context tracking.

### Issue 4: Project Deletion Tag Cleanup
When deleting a project, the system fails to properly clean up the project's tags in the database, leading to unique constraint violations when trying to recreate a project with the same name and tags. The error occurs because the database still has the project-tag association records even after the project is supposedly deleted.

## Technical Analysis

### Issue 1: Session History Awareness Bug
1. **Context Selection System**:
   - The agent likely uses its `context_selector.py` module for retrieving relevant context
   - It appears to query the Qdrant vector database (`collections/code_fragments/points/search`) when generating responses
   - The context selection appears to be prioritizing semantic similarity over session history

2. **Session History Integration**:
   - `session_manager.py` correctly captures command history
   - However, this history doesn't appear to be effectively utilized in the RAG process for queries about the conversation itself

3. **Code RAG Pipeline**:
   - The issue may be in how the `code_rag.py` module integrates session history with vector database results
   - The strategy selector might not be correctly interpreting meta-questions about the conversation

### Issue 2: Missing Session Auto-Creation
1. **Command Handling in DevAgent CLI**:
   - The `handle_generate` method in `devagent.py` doesn't check for an active session
   - No automatic session creation is implemented for commands that would benefit from session context
   - No warning is provided when operating without an active session

2. **Session-Command Integration**:
   - There appears to be weak integration between the command handlers and session management
   - Commands that benefit from session context don't verify if a session exists

### Issue 3: Pre-Session Commands in History
1. **Session History Recording Logic**:
   - The `add_to_history` method in `session_manager.py` appears to add commands to the history regardless of when they were executed
   - There's no timestamp validation to ensure commands were executed after session creation
   - This causes retroactive recording of commands that occurred before the session existed

## Relevant Files
Based on the project structure, the following files are likely involved:
- `devagent.py` - Main CLI tool 
- `session_manager.py` - Session Management System
- `code_rag.py` - RAG framework for code generation
- `context_selector.py` - Enhanced context selection

## Code Examination Required
1. How does `context_selector.py` handle query analysis for conversation summary requests?
2. Does `code_rag.py` have special handling for meta-questions about session history?
3. Is session history being incorporated into the context provided to the LLM?
4. Are there filters in place to prioritize session-specific information over general code fragments?

## Suggested Fix Approach

### For Session History Awareness:
1. Modify the query analysis in `context_selector.py` to detect meta-questions about the conversation
2. When such questions are detected, prioritize the session history from `session_manager.py` over vector database results
3. Add a special context retrieval strategy for conversation summaries that directly uses session history
4. Ensure parsing errors are handled gracefully when processing conversation history

### For Session Management:
1. Implement auto-session creation in the `handle_generate` method in `devagent.py`:
   ```python
   # Check for active session and auto-create if needed
   active_session = self.session_manager.get_active_session()
   if not active_session and args.project_id:
       # Auto-create a session named after the project
       project = self.project_manager.get_project(args.project_id)
       session_name = f"Session for {project['name']}"
       self.session_manager.create_session(
           name=session_name,
           project_id=args.project_id
       )
       print(f"Created session: {session_name}")
   ```

2. Modify the session history tracking to only record commands issued after session creation:
   ```python
   # In session_manager.py, add a creation timestamp check
   def add_to_history(self, command, args, result=None, error=None):
       # Only add to history if the command timestamp is after session creation
       command_time = datetime.datetime.now()
       session_creation_time = datetime.datetime.fromisoformat(
           self.session_data.get("metadata", {}).get("start_time", "2000-01-01T00:00:00")
       )
       if command_time > session_creation_time:
           # Add to history as normal
           # ...
   ```

3. Add session validation in commands that benefit from session context:
   ```python
   # In relevant command handlers
   if not self.session_manager.get_active_session():
       print("Warning: No active session. Session context is recommended for this operation.")
       print("Create a session with: devagent session create <name> --project-id <project-id>")
       
       if args.auto_create_session and args.project_id:
           # Auto-create if flag is provided
           # ...
   ```

## System Architecture Context
The AI Development Agent uses a Context-Extended RAG system with:
- SQLite database for project and session storage
- Qdrant vector database for code context
- Multiple context selection strategies (semantic, structural, dependency, balanced, auto)
- Session tracking via the session_manager.py component 

The fixes should integrate with these existing components while:
1. Improving the handling of conversation-related queries
2. Enhancing the integration between command execution and session management
3. Ensuring proper isolation of session history to commands executed during the session lifetime
4. Fixing the project deletion mechanism to properly clean up related database records

## User Experience Improvement
These fixes will significantly improve the user experience by:
1. Making sessions more intuitive and automatic when needed
2. Ensuring conversation summaries accurately reflect the user's actual interactions
3. Providing clearer guidance on session usage
4. Eliminating confusion from history containing pre-session commands
5. Creating a more cohesive workflow between projects and sessions
6. Allowing seamless project deletion and recreation without database errors
