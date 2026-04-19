# How to Define a Club Process

This guide walks you through creating a new process document for the CVW Process Library — the section of the website that gives officers step-by-step instructions for running club operations.

You do **not** need to know anything technical. You will use an AI assistant (Claude or ChatGPT) to do the formatting work. Your job is to describe the process clearly; the AI and your system administrator do the rest.

---

## Before You Start — Gather This Information

Before opening any AI tool, answer these questions on paper or in a notes app. The clearer your answers, the better your result.

**1. What does this process cover?**
Write one or two sentences describing what the process is for and where it ends.
*Example: "This process covers collecting cash dues at a meeting and getting them recorded in the membership database."*

**2. Who is involved?**
List every person or role who does something. For each one, write what they are responsible for.
*Example: Treasurer — collects cash, deposits it, emails VP Membership with the amount.*

**3. How does the process start?**
Is there more than one way it can begin? List each starting point separately.
*Example: (a) member pays at a meeting, (b) member pays online via PayPal.*

**4. What are the steps, in order?**
For each starting point, list the steps from beginning to end. Write who does each step.
*Example — Path A (at a meeting):*
- *Treasurer collects cash or check*
- *Treasurer deposits payment*
- *Treasurer emails VP Membership with name, amount, date*
- *VP Membership updates the database*

**5. Do any paths merge?**
If multiple starting points eventually lead to the same steps at the end, note where they join up.
*Example: "Both paths end with VP Membership updating the database."*

**6. Are there any open questions or things not yet decided?**
Write these down — they will be flagged on the process page so the right people can resolve them.

---

## Step 1 — Copy This Prompt Into Your AI Tool

Open Claude (claude.ai) or ChatGPT. Paste the following block **exactly** as a new message, then hit send. Do not change it.

---

```
I need your help creating a process document for a club management system. The document uses a specific YAML + Markdown format. I will describe the process to you in plain English and you will produce the complete file.

The file format is:

---
process: short-name-with-dashes       # e.g. annual-dues-collection
version: 1.0
status: draft
last_updated: YYYY-MM-DD              # today's date
owner: Role Title                     # e.g. VP Membership
backup: Role Title                    # who covers if owner is unavailable
description: >
  One or two sentences describing what this process covers and where it ends.

roles:
  - id: role-id-lowercase-dashes      # e.g. vp-membership
    title: Role Title                 # e.g. VP Membership
    db_title: Exact Officer Title     # must match exactly: President, VP Member Services,
                                      # VP Program Coordinator, Treasurer, Secretary,
                                      # Skills Center Director, or leave blank if not an officer role
    responsibilities:
      - What this role does in this process (one item per line)
      - Add as many as needed

triggers:
  - id: trigger-id                    # e.g. trigger-in-person
    label: Short Label                # shown on tab button, e.g. "In-Person Payment"
    description: One sentence describing when/how this path starts.

steps:
  - id: step-id
    label: Step Name
    actor: role-id                    # must match a role id above
    depends_on: [previous-step-id]   # omit for first step
    trigger_variants:                 # use this when the step action differs per trigger
      trigger-id-one:
        action: What happens in this step for this trigger path.
      trigger-id-two:
        action: What happens in this step for this trigger path.
    # OR use plain action if the step is the same regardless of trigger:
    action: >
      What happens in this step.

  - id: step-id-2
    label: Step Name
    depends_on: [step-id]
    variants:                         # use this when different roles handle the step per trigger
      variant-name-a:
        actor: role-id
        trigger: trigger-id-one      # single trigger, or list: [trigger-id-one, trigger-id-two]
        action: What happens.
      variant-name-b:
        actor: other-role-id
        trigger: [trigger-id-two, trigger-id-three]
        action: What happens.

artifacts:
  - id: artifact-id
    label: Document or System Name
    location: Where to find it (URL, folder path, or TBD)

open_issues:
  - Describe any unresolved question or decision needed here.
  # Delete this section entirely if there are no open issues.
---

# Process Title

One paragraph summarizing the process for a non-technical reader.

---

## The Paths

### Path 1 — [Trigger Label]

1. Step one.
2. Step two.
...

### Path 2 — [Trigger Label]

1. Step one.
...

---

## What Can Go Wrong

- **Issue title** — How to handle it.

---

Now please ask me to describe my process. Ask me one question at a time if that helps. When you have enough information, produce the complete file. After producing it, summarize the paths back to me in plain English so I can verify it is correct.
```

---

## Step 2 — Describe Your Process to the AI

After you send the prompt above, the AI will ask you questions. Answer them using the notes you gathered in the "Before You Start" section. Be as specific as you can. If you are unsure about something, say so — the AI will add it to the Open Questions section.

When you are satisfied with the AI's plain-English summary, ask it to produce the final file. Copy the entire output — from the first `---` to the last line.

---

## Step 3 — Roughly Preview the Flow Diagram

Before handing off the file, you can preview the flow diagram yourself:

1. In the AI output, find the `steps:` section and look at the step labels and actors.
2. To see the diagram, go to **[mermaid.live](https://mermaid.live)** — a free, no-login website.
3. Ask the AI: *"Generate the Mermaid flowchart for this process using the same format as this example:"*

   ```
   flowchart TD
       START(["▶ Start"])
       DEC{"How is it submitted?"}
       START --> DEC
       path_a_0["Step Name\n(Actor)"]
       DEC -->|"Path A"| path_a_0
       path_a_0 --> shared_0
       shared_0["Final Step\n(Actor)"]
       shared_0 --> DONE(["✅ Complete"])
   ```

4. Paste the AI's Mermaid output into the left panel at mermaid.live. The diagram appears on the right. Check that the steps and handoffs look right.

This diagram preview is approximate — the actual system generates it automatically from your file. But it is a good way to spot missing steps or wrong actors before handing off.

---

## Step 4 — Hand Off to Your System Administrator

Send the complete file text to Don Oxley (or whoever manages the CVW system). Include:

- The full file text from the AI
- Any corrections or notes
- Confirmation that the plain-English summary the AI gave you was accurate

Don will use Claude Code to add the file to the system in a few minutes. Once added, you can view it at **CVW internal site → Processes** and verify the rendered version looks correct. If anything needs adjusting, just note it and it can be updated the same way.

---

## Tips

- **One path at a time.** If your process has multiple starting points, describe one fully before moving to the next. Then tell the AI "now add another path."
- **Roles must match the officer list.** The "Current Person" column pulls live from the officer database. If a role is not an official officer position, that is fine — it will just show blank in that column.
- **Open questions are fine.** If something is unresolved (e.g. a policy hasn't been decided yet), include it. The process page will flag it with a warning badge so it is visible and doesn't get forgotten.
- **Drafts are fine.** New processes start with `status: draft`. They are visible on the internal site but clearly marked. Change to `status: active` when the process is reviewed and approved.
