# Agent Skills — License and Attribution

The six SKILL.md files in this directory are unmodified copies from Addy Osmani's `agent-skills` repository:

**Source:** https://github.com/addyosmani/agent-skills
**License:** MIT

Included skills:

1. `spec-driven-development/SKILL.md`
2. `planning-and-task-breakdown/SKILL.md`
3. `incremental-implementation/SKILL.md`
4. `test-driven-development/SKILL.md`
5. `documentation-and-adrs/SKILL.md`
6. `git-workflow-and-versioning/SKILL.md`

## How These Skills Work

Your coding agent (Antigravity, Claude Code, Codex, or Cursor) automatically scans this directory on session start and loads the `name` and `description` fields from each SKILL.md. When you make a request, the agent matches your intent against these descriptions and loads the full SKILL.md content for the relevant skill.

You do not need to manually invoke these skills. Talk to the agent naturally about what you want — "let's write a spec," "break this into tasks," "implement the upload endpoint" — and the agent will match your request to the appropriate skill and follow its workflow.

## Do Not Modify

These files are part of the graded artifact. Modifying them is grounds for losing points on the "`.agent/skills/` folder" rubric item. If you want to add your own custom skills, do so in a separate folder (e.g., `.agent/custom-skills/`) — do not edit these.

## MIT License (from the source repository)

```
MIT License

Copyright (c) 2025 Addy Osmani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
