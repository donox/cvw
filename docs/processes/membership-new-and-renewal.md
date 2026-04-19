---
process: membership-new-and-renewal
version: 1.0
status: draft
last_updated: 2026-04-19
owner: VP Membership
description: >
  Covers all paths by which a person becomes or remains a CVW member:
  in-person new application, online new application, and online renewal.
  Ends when the membership database and public member list are updated.

roles:
  - id: vp-membership
    title: VP Membership
    responsibilities:
      - Receives all application notifications
      - Verifies payment has been confirmed
      - Updates the membership database in Dropbox
      - Posts updated member list to the website
  - id: treasurer
    title: Treasurer
    responsibilities:
      - Receives PayPal payment notifications
      - Confirms payment receipt to VP Membership
  - id: greeter
    title: Greeter
    notes: Currently filled by Buck or Ron
    responsibilities:
      - Accepts cash or check payments at meetings
      - Deposits payments
      - Communicates payment info to VP Membership

triggers:
  - id: trigger-in-person
    label: In-Person Application
    description: Applicant arrives at a meeting and fills out a paper form
  - id: trigger-online-new
    label: Online Application
    description: Applicant submits the online application form
  - id: trigger-online-renewal
    label: Online Renewal
    description: Existing member renews via the online renewal form

steps:
  - id: receive-application
    label: Receive Application
    actor: vp-membership
    trigger_variants:
      trigger-in-person:
        action: Paper form is scanned and emailed to VP Membership and the AI-monitored mailbox
        inputs: [paper-application-form]
        outputs: [scanned-application-email]
      trigger-online-new:
        action: Form submission is automatically emailed to VP Membership and the AI-monitored mailbox
        inputs: [online-application-form]
        outputs: [application-email]
      trigger-online-renewal:
        action: Renewal submission automatically routes to PayPal payment step; no separate application document
        inputs: [online-renewal-form]
        outputs: [paypal-payment-request]

  - id: process-payment
    label: Process Payment
    depends_on: [receive-application]
    variants:
      cash-or-check:
        actor: greeter
        trigger: trigger-in-person
        action: >
          Member pays by cash or check to Buck, Ron, or Don at the meeting.
          Greeter deposits the payment and communicates payment info
          (amount, member name, date) to VP Membership and the AI-monitored mailbox.
        inputs: [cash-or-check]
        outputs: [payment-confirmation-to-vp]
        open_question: >
          Is this communicated by email or via a form? ("email, form?" noted in current diagram)
      paypal:
        actor: treasurer
        trigger: [trigger-online-new, trigger-online-renewal]
        action: >
          Member completes PayPal payment. PayPal confirmation is automatically
          emailed to VP Membership, Treasurer, and the AI-monitored mailbox.
        inputs: [paypal-payment]
        outputs: [paypal-confirmation-email]

  - id: update-membership-db
    label: Update Membership Database
    actor: vp-membership
    depends_on: [process-payment]
    action: >
      VP Membership updates the membership database spreadsheet in Dropbox
      and posts the refreshed member list to the CVW website.
    inputs: [application-data, payment-confirmation]
    outputs: [updated-dropbox-db, updated-website-member-list]
    notes: >
      This is the terminal step. All three paths (in-person, online new,
      online renewal) converge here.

decision_points:
  - id: application-path
    after: null
    label: How is the application being submitted?
    branches:
      - condition: Member is present at a meeting
        goto: trigger-in-person
      - condition: Member submits online for the first time
        goto: trigger-online-new
      - condition: Existing member renews online
        goto: trigger-online-renewal

artifacts:
  - id: paper-application-form
    label: Paper Application Form
    location: TBD — printed at meetings
  - id: online-application-form
    label: Online Application Form
    location: CVW website application page
  - id: online-renewal-form
    label: Online Renewal Form
    location: CVW website renewal page
  - id: dropbox-db
    label: Membership Database
    location: Dropbox (shared folder — link TBD)
  - id: ai-monitored-mailbox
    label: AI-Monitored Mailbox
    location: TBD
    notes: Receives copies of all application and payment notifications; purpose is automated processing or alerting

open_issues:
  - Payment communication method for cash/check path is unspecified (email vs. form)
  - Location of Dropbox membership DB needs to be recorded here
  - AI-monitored mailbox address and what it does with messages should be documented
  - Who is the fallback if the VP Membership role is vacant?
  - Is "Don" in the greeter list the same as the process owner? Clarify to avoid single-point-of-failure notation.
---

# Membership — New Members and Renewals

This document describes how CVW processes new member applications and annual renewals. It covers all three paths: showing up at a meeting, applying online, and renewing online. All three paths end with the membership database and public member list being updated.

---

## Who Is Involved

| Role | Current Person | What They Do |
|------|---------------|--------------|
| VP Membership | TBD | Central coordinator — receives all applications and payment confirmations, updates the database and website |
| Treasurer | TBD | Confirms PayPal payments for online paths |
| Greeter | Buck or Ron | Accepts cash/check at meetings, deposits funds, notifies VP Membership |

> **Note for incoming officers:** If you are taking over one of these roles, make sure you have access to the AI-monitored mailbox and the Dropbox membership folder before your predecessor steps down.

---

## The Three Paths

### Path 1 — In-Person Application (at a meeting)

1. The applicant fills out a paper application form at the meeting.
2. The form is scanned and emailed to the VP Membership and the AI-monitored mailbox.
3. The applicant pays by cash or check — given to Buck, Ron, or Don at the meeting.
4. The Greeter deposits the payment.
5. The Greeter communicates payment details (member name, amount, date) to the VP Membership and the AI-monitored mailbox. *(Method — email or form — to be confirmed.)*
6. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

### Path 2 — Online Application (new member)

1. The applicant submits the online application form on the CVW website.
2. The submission is automatically emailed to the VP Membership and the AI-monitored mailbox.
3. The applicant completes payment via PayPal.
4. PayPal sends a confirmation email to the VP Membership, the Treasurer, and the AI-monitored mailbox.
5. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

### Path 3 — Online Renewal (existing member)

1. The member submits the online renewal form on the CVW website.
2. The member completes payment via PayPal.
3. PayPal sends a confirmation email to the VP Membership, the Treasurer, and the AI-monitored mailbox.
4. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

---

## What Can Go Wrong

- **Payment received but database not updated** — VP Membership should update the DB within 48 hours of receiving payment confirmation. If you are VP Membership and are going to be unavailable, designate a backup.
- **Cash/check payment not communicated** — The Greeter must notify VP Membership after every meeting where dues were collected. Don't wait.
- **Online form submission lost** — The AI-monitored mailbox provides a redundant copy. If VP Membership didn't receive a notification, check that mailbox.
- **Applicant paid but never received confirmation** — VP Membership should send a brief acknowledgment email once the database is updated.

---

## Open Questions

The following items are noted in the current diagram as unresolved and should be decided before this process is finalized:

1. What is the exact method for Greeters to communicate cash/check payment info to VP Membership — email, a form, or something else?
2. What is the address and role of the AI-monitored mailbox? What automation (if any) is it driving?
3. Where exactly is the Dropbox membership database? Record the folder path or link here.
4. Who is the designated backup if the VP Membership role is temporarily vacant?
