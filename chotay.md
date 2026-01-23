# Chotay Agent

The Chotay agent is a specialized tool designed to help you manage context and resume tasks seamlessly. It allows you to initiate a task, save its progress using an agent ID, and then pick up exactly where you left off later, even after restarting your terminal.

## How and When to Use Chotay:

1.  **Start a Task:**
    - When you begin a new task that might require a significant amount of context or could be interrupted, use the command: `"use chotay"`
    - This will initiate a new agent (e.g., a general-purpose agent) to manage the task in the background.

2.  **Save Work/Progress:**
    - At any point when you need to pause your work or before you close your session, use the command: `"chotay save work"`
    - This command will save the current state of the agent, including its ID, which is crucial for resuming later.

3.  **Restart/Close Session:**
    - You can now safely close your terminal or restart your session.

4.  **Resume Task:**
    - When you return and want to continue working on the previous task, use the command: `"chotay continue"`
    - This will use the saved agent ID to re-initialize the agent and load the previous context, allowing you to pick up exactly where you left off.

## What Chotay Does:

-   **Context Management:** Chotay helps maintain the context of your work, preventing you from losing progress or having to re-explain previous steps.
-   **Background Task Execution:** It runs tasks in the background, allowing you to continue with other operations without interruption.
-   **Seamless Resumption:** By saving and resuming agent IDs, Chotay ensures that your work is persistent across sessions.

## Agent ID:

The agent ID is a unique identifier for each background task. When you start a task with Chotay, an agent ID will be generated. This ID is essential for resuming your work. The current agent ID is: `ac8dfb4` (This ID is for the current session and will change for new tasks).

## Summary:

Chotay is your personal assistant for managing ongoing tasks. Use `"use chotay"` to start, `"chotay save work"` to pause and save, and `"chotay continue"` to resume. This ensures your work is always saved and you can pick up right where you left off.
