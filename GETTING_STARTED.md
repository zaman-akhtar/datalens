# Getting Started — Day 1 Checklist

Welcome to your DataLens project starter template. This guide walks you through setting up your project on Day 1 so you can focus on the spec-driven development process for the rest of the 3 weeks.

> **Read this once, do each step, then delete this file.** It is not part of the final deliverable.

---

## Step 1 — Rename and initialize your repo (5 minutes)

1. Rename this folder to something appropriate (e.g., `datalens-team-alpha`)
2. Initialize git:
   ```bash
   git init
   git add .
   git commit -m "Initial commit from starter template"
   ```
3. Create a GitHub repository for your team
4. Push:
   ```bash
   git remote add origin <your-repo-url>
   git branch -M main
   git push -u origin main
   ```

---

## Step 2 — Confirm Agent Skills are discoverable (10 minutes)

The 6 mandatory skills are already in `.agent/skills/`. Now you need to verify your coding agent discovers them.

### If you're using Antigravity

Antigravity looks for skills in `.agent/skills/` by default when your project is opened. Open this folder in Antigravity and run a test query. Ask the agent:

> "What skills do you have available for this project?"

The agent should list the six skills by name. If it doesn't, verify that you opened the correct folder and that the `.agent/skills/` directory is visible in the file tree.

### If you're using Claude Code

Claude Code looks for skills in `.claude/skills/`. You have two options:

**Option A (recommended):** Symlink the skills folder:
```bash
mkdir -p .claude
ln -s ../.agent/skills .claude/skills
```

**Option B:** Copy the skills:
```bash
mkdir -p .claude/skills
cp -r .agent/skills/* .claude/skills/
```

Then start Claude Code in this directory and ask: "What skills do you have available?"

### If you're using Cursor

Cursor uses `.cursor/rules/` with a slightly different format. You'll need to convert the SKILL.md files. See the Cursor docs: https://cursor.com/docs/context/rules

### If you're using Codex

Codex reads `AGENTS.md` at the repo root. Create one that references the skills:
```bash
cat > AGENTS.md << 'EOF'
# Agent Instructions

This project uses Addy Osmani's Agent Skills framework. The skills are in `.agent/skills/`.

When the user's intent matches a skill's description, follow that skill's workflow.

Available skills:
- spec-driven-development: Creates specs before coding
- planning-and-task-breakdown: Breaks work into ordered tasks
- incremental-implementation: Delivers changes incrementally in thin vertical slices
- test-driven-development: Drives development with tests
- documentation-and-adrs: Records decisions and documentation
- git-workflow-and-versioning: Structures git workflow practices

Read the relevant SKILL.md from `.agent/skills/<skill-name>/SKILL.md` when a task matches.
EOF
```

---

## Step 3 — Configure your environment (5 minutes)

```bash
cp .env.example .env
```

Open `.env` and fill in your LLM provider and API key. You only need ONE provider for now.

---

## Step 4 — First skill invocation — write your spec (Day 3-5)

Now the real work begins. Ask your agent:

> "Help me write the spec for this DataLens project. We are working from the Final Project Specification document and our assigned dataset is [Dataset Name]."

Your agent will recognize this as a spec-writing task, load the `spec-driven-development` skill, and guide you through filling in `SPEC.md`.

Key things to verify as the agent works:

- The agent surfaces its assumptions explicitly (every spec should start with an "ASSUMPTIONS I'M MAKING" block)
- The agent covers all six core areas (Objective, Commands, Project Structure, Code Style, Testing Strategy, Boundaries)
- Success criteria are specific and testable, not vague

---

## Step 5 — After the spec, build the plan (Day 6-7)

Once your spec is solid, ask:

> "Now let's plan the implementation. Break the work into tasks small enough to implement one at a time."

Your agent will load the `planning-and-task-breakdown` skill and help you produce `tasks/plan.md` and `tasks/todo.md`.

Key things to verify:

- Each task touches 5 files or fewer
- Each task has explicit acceptance criteria
- Dependencies between tasks are noted
- Tasks are ordered correctly

---

## Step 6 — Start building (Week 2)

On Day 8, ask the agent to start on task T010 (or whatever your first implementation task is). The agent will load `incremental-implementation` and `test-driven-development` automatically and build in small, tested slices.

---

## Reminders

- **Commit often.** Each working slice gets its own commit.
- **Review agent output.** Don't accept code you haven't at least skimmed.
- **Write ADRs as decisions happen.** Not all at the end.
- **Record notes on agent interventions.** You'll need specific examples for the final report.
- **Dry-run your README on Day 20.** It must work on a fresh machine.

---

## Now delete this file

You've read it. It is not part of the final deliverable. From the repo root:

```bash
rm GETTING_STARTED.md
git add GETTING_STARTED.md
git commit -m "Remove starter getting-started guide"
```

Good luck. You are about to learn a career-defining skill.
