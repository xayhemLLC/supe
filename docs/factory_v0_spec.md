# Factory v0 Specification

## Overview

This document describes the **Factory v0** pipeline for integrating
stateless agents, the AB memory engine and Tasc‐based task
management into a cohesive software assembly line. The goal is to
enable tasks to be planned, executed and validated by autonomous
agents while ensuring that all critical knowledge persists in AB
memory. Agents themselves are assumed to be stateless; they retain
no history across tasks and have no implicit access to prior
conversations, files or execution state. Instead, the factory uses
a disciplined set of rituals and card schemas to capture inputs and
outputs at each phase, ensuring that the next agent always has
enough context to continue.

The factory loop consists of the following phases:

1. **Intake**: A new Tasc is created and stored as an AB card.
2. **Planning**: A planner agent reads the Tasc, produces a
   specification and plan, and writes `spec` and `plan` cards.
3. **Execution**: A coder or worker agent reads the plan and
   executes the task, producing evidence and decision cards. If a
   bug is encountered, a bug card is created.
4. **Validation**: A validator agent reviews the work and writes
   decision or bug cards as appropriate.
5. **Extraction**: After each agent run, an extraction step
   summarises any problems, decisions, workarounds and evidence
   into AB cards. This is a **memory checkpoint**. A task is not
   considered complete until all required checkpoints have been
   written.
6. **Store**: All cards persist in the AB ledger. The task queue
   (Q) is updated to reflect progress and remaining work. The next
   agent receives a curated envelope containing only the necessary
   context.

## Card Schemas

The factory relies on several specialised card types. These
card types are implemented via the generic `Card` abstraction and
distinguished by their `label`. Each card has a set of named
buffers to store its content. Connections encode relationships
between cards (e.g. `plan_for`, `decision_of`).

### Spec Card (`label="spec"`)

Stores the problem definition for a Tasc. Buffers:

| Buffer Name          | Content Type          | Description                               |
|----------------------|-----------------------|-------------------------------------------|
| `spec_text`          | `text/plain`          | Formal specification of the task          |
| `known_pitfalls`     | `application/json`    | JSON list of known pitfalls (optional)    |
| `definition_of_done` | `application/json`    | JSON list of completion criteria (optional)|

### Plan Card (`label="plan"`)

Describes the intended approach. Buffers:

| Buffer Name  | Content Type       | Description                                      |
|--------------|--------------------|--------------------------------------------------|
| `plan_text`  | `text/plain`       | High-level description of the plan               |
| `plan_items` | `application/json` | JSON list of plan steps (optional)               |

### Decision Card (`label="decision"`)

Documents the action chosen after integrating subself outputs. Buffers:

| Buffer Name    | Content Type   | Description                            |
|----------------|----------------|----------------------------------------|
| `decision_text`| `text/plain`   | Text of the chosen decision/action     |
| `reasoning`    | `text/plain`   | Optional rationale for the decision    |

### Evidence Card (`label="evidence"`)

Stores artefacts produced during execution or validation. Buffers:

| Buffer Name | Content Type           | Description                                          |
|-------------|------------------------|------------------------------------------------------|
| `evidence`  | arbitrary (e.g. bytes) | Raw evidence payload (file contents, screenshot, etc)|
| `description`| `text/plain`          | Optional textual description of the evidence         |

### Bug Card (`label="bug"`)

Captures issues encountered during execution or validation. Buffers:

| Buffer Name          | Content Type   | Description                               |
|----------------------|----------------|-------------------------------------------|
| `bug_description`    | `text/plain`   | Description of the bug                    |
| `reproduction_steps` | `text/plain`   | Steps to reproduce the bug (optional)     |
| `fix`                | `text/plain`   | Description of a fix or workaround (optional)|

### Conversation Card (`label="conversation"`)

Stores compressed or summarised chat logs. Buffers:

| Buffer Name  | Content Type | Description                          |
|--------------|--------------|--------------------------------------|
| `conversation` | `text/plain` | Summarised conversation transcript  |

## Memory Checkpoints

A **Memory Checkpoint** is a mandatory write to AB at key phases. If
a checkpoint is skipped, the task is considered incomplete and
later agents will lack necessary context. Checkpoint functions are
implemented in `ab.checkpoint`.

The required checkpoints are:

| Stage            | Cards Created                      | Notes                                   |
|------------------|------------------------------------|-----------------------------------------|
| After planning   | `spec`, `plan`                     | Captures specification and plan        |
| After decision   | `decision`                         | Records the chosen action and rationale|
| After execution  | `evidence` (0 or more), `bug` (0 or more) | Stores outputs and any issues        |
| After validation | `decision` or `bug`                | Confirms success or logs failure       |
| After conversation| `conversation`                    | Stores relevant dialogues (optional)   |

## Agent Input Envelope

Before an agent is invoked, a **curated envelope** must be
constructed containing only what the agent needs. The envelope
includes:

* `tasc_id`: Identifier of the Tasc card to work on.
* `spec`: Specification text from the spec card.
* `plan`: Plan text from the plan card.
* `known_pitfalls`: List of pitfalls, if any.
* `definition_of_done`: List of completion criteria, if any.
* `definition_of_success`: Desired outcome from the Tasc card.
* `plan_items`: List of plan steps, if provided.

Optional additional context (e.g. prior decisions or evidence) may be
added if required by a particular agent type. The envelope should
remain as compact as possible.

## Execution Protocol

1. **Create**: A new Tasc card is created with fields capturing the
   task metadata (title, status, additional notes, testing
   instructions, desired outcome, dependencies).
2. **Plan**: A planner agent reads the Tasc and constructs the
   specification and plan. After planning, a memory checkpoint
   writes the spec and plan cards, and updates the task queue to
   reflect planned status.
3. **Work**: An executor agent receives the envelope and performs
   the work. After execution, the agent writes evidence cards for
   produced artefacts, bug cards for issues and a decision card
   summarising the action taken. A memory checkpoint ensures
   nothing is lost.
4. **Validate**: A validator agent reviews the outputs and writes a
   decision card or bug card. A checkpoint records the outcome.
5. **Complete**: Once all checkpoints have been satisfied and
   dependencies resolved, the Tasc status is updated to `done` and
   removed from the queue.

## Rationale

This specification enforces a clear boundary between agents and
memory. By requiring that all relevant information be stored in
AB cards and by constructing minimal input envelopes, we maintain
disciplined memory flow and ensure reproducibility. Stateless
agents become interchangeable workers that can be spun up and
terminated without losing knowledge. The factory scales by
executing many Tascs in parallel, confident that every result and
decision is traceable through AB.