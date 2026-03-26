# Using Email

This guide covers how to send email to members from the CVW dashboard.

---

## Getting There

From the dashboard nav: **Email → Compose**

Or from a member's detail page, click **Send Email** to open a pre-addressed
compose form for that specific member.

---

## Sending a Message

### Step 1 — Choose recipients

**Group / All Members** (default)
- Leave the dropdown on *All Active Members* to send to everyone with Active status
- Or select a specific group from the dropdown

**Single Member**
- Select the *Single Member* radio button
- Choose the member from the dropdown (only members with email addresses are listed)

### Step 2 — Load a template (optional)

Select a saved template from the **Load Template** dropdown. This fills in the
subject and body automatically. You can edit the content after loading.

Leave the dropdown blank to write the email from scratch.

### Step 3 — Write the message

Fill in the **Subject** and **Body**.

**Personalization variables** — insert member data into the body using these placeholders:

| Variable | Replaced with |
|----------|--------------|
| `{{ first_name }}` | Member's first name |
| `{{ last_name }}` | Member's last name |
| `{{ full_name }}` | First and last name |
| `{{ email }}` | Member's email address |
| `{{ membership_type }}` | e.g. Individual, Family |
| `{{ status }}` | Active, Prospective, Former |
| `{{ dues_paid }}` | True or False |

Example body:
```
Hi {{ first_name }},

Just a reminder that your dues status is currently: {{ dues_paid }}.

See you at the next meeting!
```

### Step 4 — Set rendering mode

- **Simple** — use for most emails; handles `{{ variable }}` substitutions
- **Jinja2** — use for advanced logic (if/for statements); leave on Simple unless needed

### Step 5 — Personalise checkbox

Check **Personalise** to send individual emails with each member's data substituted.
Leave unchecked to send the same body to everyone (variables won't be replaced).

Single member sends always personalise automatically.

### Step 6 — Send

Click **Send Now**. The page will confirm how many recipients received the email.

---

## Managing Templates

Go to **Email → Templates** to create, edit, or delete reusable email templates.

Each template has:
- **Name** — internal label
- **Subject** — email subject line (can include variables)
- **Body** — email body (can include variables)
- **Type** — Simple or Jinja2

Use the **Send Test** button on a template to send a sample to your own address
before using it for a real send.

---

## Viewing Sent Email History

Go to **Email → Log** to see all previous sends with:
- Date and time
- Subject
- Number of recipients
- Status (sent / partial / failed)
- Any error details

---

## Scheduled Email

Go to **Email → Scheduled** to set up recurring emails that send automatically
on a schedule (e.g. monthly reminders). Each scheduled email uses a saved
template and targets a group or all active members.

---

## Tips

- Always send a test to yourself before a bulk send to the full membership
- Use groups to target subsets of members (e.g. members with unpaid dues)
- Check **Email → Log** after sending to confirm delivery count
- If a send fails, the log will show the error detail
