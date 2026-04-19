---
process: membership-new-and-renewal
version: 1.1
status: active
last_updated: 2026-04-19
owner: VP Membership
backup: President
description: >
  Covers all paths by which a person becomes or remains a CVW member:
  in-person new application, online new application, and online renewal.
  Ends when the membership database and public member list are updated.

roles:
  - id: vp-membership
    title: VP Membership
    db_title: VP Member Services
    backup: President
    responsibilities:
      - Receives all application notifications
      - Verifies payment has been confirmed
      - Updates the membership database in Dropbox
      - Posts updated member list to the website
  - id: treasurer
    title: Treasurer
    db_title: Treasurer
    responsibilities:
      - Receives PayPal payment notifications
      - Confirms payment receipt to VP Membership
  - id: greeter
    title: Greeter
    notes: Currently filled by Buck or Ron
    responsibilities:
      - Accepts cash or check payments at meetings
      - Deposits payments
      - Communicates payment info to VP Membership by email

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
        action: Paper form is scanned and emailed to VP Membership
        inputs: [paper-application-form]
        outputs: [scanned-application-email]
      trigger-online-new:
        action: Form submission is automatically emailed to VP Membership
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
          Greeter deposits the payment and emails payment info
          (amount, member name, date) to VP Membership.
        inputs: [cash-or-check]
        outputs: [payment-confirmation-email-to-vp]
      paypal:
        actor: treasurer
        trigger: [trigger-online-new, trigger-online-renewal]
        action: >
          Member completes PayPal payment. PayPal confirmation is automatically
          emailed to VP Membership and Treasurer.
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
---

# Membership — New Members and Renewals

This document describes how CVW processes new member applications and annual renewals. It covers all three paths: showing up at a meeting, applying online, and renewing online. All three paths end with the membership database and public member list being updated.

---

## The Three Paths

### Path 1 — In-Person Application (at a meeting)

1. The applicant fills out a paper application form at the meeting.
2. The form is scanned and emailed to the VP Membership.
3. The applicant pays by cash or check — given to greeter or store manager at the meeting.
4. The Treasurer deposits the payment.
5. The Treasurer emails payment details (member name, amount, date) to the VP Membership.
6. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

### Path 2 — Online Application (new member)

1. The applicant submits the online application form on the CVW website.
2. The submission is automatically emailed to the VP Membership.
3. The applicant completes payment via PayPal.
4. PayPal sends a confirmation email to the VP Membership and the Treasurer.
5. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

### Path 3 — Online Renewal (existing member)

1. The member submits the online renewal form on the CVW website.
2. The member completes payment via PayPal.
3. PayPal sends a confirmation email to the VP Membership and the Treasurer.
4. VP Membership updates the membership database in Dropbox and posts the updated member list to the website.

---

## What Can Go Wrong

- **Payment received but database not updated** — VP Membership should update the DB within 48 hours of receiving payment confirmation. If you are VP Membership and are going to be unavailable, notify the President to cover.
- **Cash/check payment not communicated** — The Greeter must communicate to VP Membership after every meeting where dues were collected. Don't wait.
- **Online form submission lost** — Check with the applicant and have them resubmit if needed.
- **Applicant paid but never received confirmation** — VP Membership should send a brief acknowledgment email once the database is updated.
