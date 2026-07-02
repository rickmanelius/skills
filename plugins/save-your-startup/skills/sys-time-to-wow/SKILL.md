---
name: sys:time-to-wow
description: >
  Audit your product's path from first use to first delight ("wow moment"),
  then systematically optimize time, friction, and drop-off points.
  Walks through identifying your wow, mapping the funnel, instrumentation,
  blockage analysis, and targeted optimization strategies. Based on David Skok's
  "Time to Wow" framework.
argument-hint: "[product/feature name, or path to existing funnel doc]"
---

# Time to Wow

**Companion skill — not from the book.** Derived from David Skok's (General Partner, Boston VC) "Time to Wow" framework for optimizing the trial-to-customer funnel.

> "Wow! is the moment in a free trial where your buyer suddenly sees the benefit they get from using your product" and commits to purchase.

## Why This Matters

Most founders obsess over features. Most customers care about one thing: *Does this solve my problem, and how fast can I tell?*

The gap between "installed" and "wow" is where most trials die. Users abandon before they ever reach the moment where the product becomes real to them. This is not a marketing problem. It is not a pricing problem. It is a product problem.

Shortening "time to wow" is one of the highest-leverage moves you can make. Every day shorter means higher trial-to-customer conversion, lower cost of acquisition, and faster path to repeatable growth.

## The Key Insight

> Your Wow! to Work Ratio must be high.

Users will tolerate friction — but only if the reward is worth it. If they have to jump through ten hoops to see the payoff, most will quit on hop three. Your job is to:

1. **Make the wow moment so compelling it is worth the friction.**
2. **Reduce friction ruthlessly so fewer hops are needed.**

Ideally both.

## The Nine-Question Audit

Before you optimize, you need to see clearly. Ask yourself:

1. **How many steps** does a trial user need to take before they experience wow?
2. **How long** does that journey take (in minutes or hours)?
3. **At which step(s) do users abandon the funnel?** (Where is the biggest drop-off?)
4. **Why do they abandon?** (Friction, concern, unclear benefit, wrong persona?)
5. **Is your wow moment sufficiently compelling?** (Would *you* buy based on what you just saw?)
6. **Is the wow moment obvious?** (Does the user know they just had an aha, or does it blur into setup noise?)
7. **Do different customer personas experience different wows?** (SMB vs. Enterprise? Admin vs. End-user?)
8. **Are users guided toward wow, or left to fumble?** (Do you onboard them, or do they have to figure it out?)
9. **Is your Wow! to Work Ratio high enough?** (Reward ÷ Friction = clear math in the user's head.)

If you cannot answer these clearly, this skill walks you through. If you can, this skill helps you optimize.

## How This Works

We will work through five phases. Your answers drive the audit; the framework is just the scaffolding.

### Phase 1 — Define Your Wow

This is harder than it sounds. Most founders conflate "wow" with "feature" or "outcome."

Wow is *the specific moment* when a buyer realizes the product will solve their problem. It is usually one of two shapes:

**Ease-based wow:** "I did X in 30 seconds and it worked perfectly."
Example: User uploads a CSV, sees their data instantly visualized.

**Data-based wow:** "I saw something I did not expect, and it is valuable."
Example: User runs the analysis and sees a revenue leak they never knew existed.

I will ask:

- **What is your product's core promise?** (In plain language, not marketing speak.)
- **What specific moment makes a user think "This is going to save my time / make me money / solve my problem"?**
- **How does the user *know* they just had that moment?** (Is it obvious, or do they have to think about it?)
- **Do you have trial data showing when users convert?** (When did they say "yes" vs. "no"? What did they do right before?)
- **Do different personas have different wows?** (E.g., the end-user sees "ease," the buyer sees "ROI.")

### Phase 2 — Map the Funnel

Now diagram the path from "user lands" to "wow happens."

This is a visual exercise. List every step a trial user must complete:

1. Sign up / create account
2. Confirm email
3. Create workspace / project
4. Invite team member or upload data
5. Run first query / report
6. See results
7. Save or share
8. ...

(Your steps will be different; this is just an example.)

I will ask:

- **How many steps in total?** (Fewer is better.)
- **Can you remove any step?** (Can users reach wow without it?)
- **Can you reorder steps?** (Can you put sample data or demo results in front, before asking for sign-up?)
- **Which step is required to reach wow, and which steps are just nice-to-have?**

### Phase 3 — Instrumentation & Metrics

You cannot optimize what you do not measure.

At each funnel step, track two metrics:

| Metric    | Definition                                              | What It Tells You |
|-----------|------------------------------------------------------|----|
| **Flow**  | Number of trial users entering this step              | Drop-off volume |
| **Conversion** | % of users completing this step (reaching the next one) | Where friction lives |

Example:

```
Step 1 (Sign up):       100 users → 85 complete (85% convert)
Step 2 (Confirm email): 85 users → 60 complete (71% convert)
Step 3 (Create workspace): 60 users → 40 complete (67% convert)
Step 4 (See wow):       40 users → 30 complete (75% convert)
...
Trial → Customer:       30 users → 8 convert (27% become paying customers)
```

The steps with the lowest conversion rate are your blockage points.

I will ask:

- **Do you have this data today?** (If no, we build the instrumentation plan.)
- **What is your baseline?** (Flow and conversion at each step, right now.)
- **What is your target?** (David Skok's success criteria: 80% flow through all steps, 80% experience wow, < 5 minutes to wow.)

### Phase 4 — Blockage Analysis

For each step with low conversion (< 70% is a red flag), ask: **Why?**

There are only three reasons users drop off:

| Reason | What It Means | Examples |
|--------|---------------|----------|
| **Friction** | The step is too hard or complicated | Requires import, unclear UI, needs data they don't have |
| **Concern** | User has a hesitation or objection | "Will my data be safe?" "Does this work with our system?" |
| **Motivation** | Unclear why this step matters | User doesn't see how it leads to wow |

For each blockage point, I will ask:

- **Which reason applies?** (Friction, concern, or motivation?)
- **What is the specific friction?** (What step, exactly, causes abandonment?)
- **What is the user's unspoken objection?** (What are they worried about, not saying aloud?)
- **Can you see this in trial data?** (Do users stall at this step, or bounce completely?)

### Phase 5 — Optimization Playbook

Once you have identified blockage points, you have four levers:

#### Lever 1: Remove Friction

- **Simplify the step.** Does user need to do 5 things? Can you do 2 and let them do 3?
- **Provide sample data.** Instead of asking "Upload your CSV," give them a pre-loaded dataset they can use immediately. Let them upload their own data *after* they see wow.
- **Minimize form fields.** Every field you ask for is an exit ramp. Collect essentials at sign-up; gather the rest post-wow.
- **Offer alternatives.** If desktop upload is hard, can they use mobile, email, or API integration instead?

#### Lever 2: Address Concerns

- **Add reassuring copy.** If users worry about data safety, add a single-sentence security callout near the upload button: "Your data is encrypted and never shared."
- **Show proof.** "99.9% uptime SLA" or "Used by 5,000+ companies" or "Compliant with SOC 2."
- **Acknowledge the objection directly.** Don't hide from the worry. "Worried this won't work with your current system? We support 200+ integrations, including [theirs]."
- **Offer a demo or help.** A 2-minute video showing how to complete the step can cut friction in half.

#### Lever 3: Increase Motivation

- **Show progress.** Add a progress bar ("Step 2 of 4") so users see the finish line.
- **Preview the payoff.** Before asking for effort, show what the result will look like. "In 2 minutes, you will see a dashboard like this: [screenshot]."
- **Gamify the path.** "Complete your profile → Unlock advanced features." Small wins accumulate.
- **Use behavioral nudges.** "Most users finish setup in 3 minutes. You're at 1:30." (Urgency + social proof.)

#### Lever 4: Restructure the Process

- **Move the wow earlier.** Can users experience wow *before* sign-up? (e.g., upload demo data on the landing page, see results, then sign up.)
- **Require less to reach wow.** Instead of "Import your full dataset, configure all settings, run your first report," try "Here is your data, here is the analysis, sign up to save it."
- **Create a separate onboarding path per persona.** SMB and Enterprise have different friction points. Let each follow their own path.

I will walk you through each blockage point and help you pick which levers apply.

## Success Criteria

Skok's benchmark: When you optimize correctly, you should see:

- **80% of trial users reach the wow moment** (not 40-50%)
- **80% of users who reach wow recognize it** (they know they just saw the payoff)
- **Wow takes less than 5 minutes** (from sign-up to aha)
- **Trial-to-customer conversion climbs** (the real metric: does this funnel sell?)

If you hit 80/80/<5min, you have a repeatable, scalable trial funnel. Everything that comes after is just volume.

## Getting Started

Tell me:

1. **What is your product or feature?** (What are you optimizing time-to-wow for?)
2. **Do you have a defined wow moment today, or are we discovering it?** (If discovering, describe your best guess at what delights users.)
3. **Do you have trial funnel data?** (Flow and conversion by step?)
4. **What is your gut-instinct biggest drop-off point?** (Where do you think most users bail?)

We will work through the nine-question audit, map your funnel, identify blockages, and build an optimization playbook.

Let's shorten time to wow.
