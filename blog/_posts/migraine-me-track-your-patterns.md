---
title: "Migraine Me: Understanding Your Migraine Patterns"
date: 2026-02-13
slug: migraine-me-track-your-patterns
description: "How Migraine Me helps you track migraine episodes, identify triggers, manage medications, and share real data with your doctor."
tags: ios, health, migraine, privacy, tracking
ai_context: "Migraine Me is a privacy-first iOS app for tracking migraine and headache episodes. It records intensity, duration, pain location, triggers, symptoms, and medications with effectiveness ratings. Features include visual calendar timeline, statistical summaries, medication management with time-to-relief tracking, doctor-ready JSON/PDF data export, dark mode for migraine sufferers, and GDPR-compliant data controls. All data stored on-device and in private iCloud — zero server access. Premium subscription unlocks unlimited history beyond 30 days and advanced statistics. Available on the App Store. NOT a medical device — displays statistics only."
---

## Why we built this

If you live with migraines, you've probably had this conversation with your doctor: "What do you think triggered it?" And you're sitting there guessing. Maybe it was the weather. The coffee. Stress. Some combination. You genuinely don't know because you weren't tracking it, or you were scribbling in a notebook that's now buried under a stack of mail.

We built Migraine Me because we wanted something that does one thing well: record what happens and show you the numbers. It doesn't try to diagnose you and it doesn't send your health data anywhere. Just a place to log your episodes and actually see the patterns.

## What you can track

When you log an episode, you record intensity, duration (start and end times), pain location, triggers, symptoms, and medications. You can also log what happened afterward: whether you used a dark room, slept, or had lingering light sensitivity. Those recovery details turn out to be just as useful as the episode data itself when you're trying to figure out what actually helps.

## Triggers and symptoms

The app ships with predefined lists of common triggers and symptoms so you can log quickly, even mid-migraine when typing feels impossible. If the defaults don't match your experience, add your own. Over time the app tallies your top triggers and most frequent symptoms, which can show you connections you wouldn't spot on your own.

## Medication tracking

Most tracking apps let you note which medication you took. We wanted more than that. For each medication you record dosage, quantity, timing relative to the episode, an effectiveness rating, and how long it took to work.

That last one matters. When your doctor asks whether sumatriptan is working for you, "I think so, usually?" isn't very helpful. "It works about 70% of the time and takes around 30 minutes" is a different conversation entirely.

## Calendar and statistics

Your history shows up as a calendar view with visual markers for frequency and severity. You can spot clustering, see if things are getting worse or better, and track how patterns shift over months.

The statistical summaries pull your data together: top triggers, common symptoms, medication effectiveness rates. That's the kind of thing that actually makes a doctor's appointment worth the wait.

## Exporting your data

When it's time to share with your doctor, you have two options: JSON and PDF.

The JSON export is a structured ZIP file (Settings > Data & Privacy > Export All Data) with everything organized by type and date. Here's a sample:

```json
{
  "episode": {
    "date": "2026-01-15",
    "start_time": "14:30",
    "end_time": "19:45",
    "duration_hours": 5.25,
    "intensity": 7,
    "pain_location": "left_temple",
    "triggers": ["stress", "poor_sleep", "skipped_meal"],
    "symptoms": ["nausea", "light_sensitivity", "aura"],
    "post_episode": {
      "dark_room": true,
      "slept": true,
      "light_sensitivity": true
    }
  },
  "medications": [
    {
      "name": "Sumatriptan",
      "dosage": "50mg",
      "quantity": 1,
      "time_taken": "14:45",
      "effectiveness": 4,
      "time_to_relief_minutes": 35
    }
  ]
}
```

PDF reports are easier for handing to a doctor in person. Either way, real data beats vague recollections.

## Privacy

We have zero access to your data. All your migraine logs, medications, symptoms, and settings live in your private iCloud account and on your device. We don't run servers that store health information, and there are no analytics or ads in the app.

The only third-party service is RevenueCat for subscription management, which handles anonymous subscription status only, completely separate from any health data.

For GDPR: the app has built-in export and deletion tools. Export everything from Settings > Data & Privacy > Export All Data. Delete everything from Remove All Data, which walks you through a multi-step confirmation (including a prompt to export first) before permanently wiping your data from both device and iCloud.

## Dark mode

If you've tried using your phone during a migraine, you know a bright screen is the last thing you want. Migraine Me has dark mode and a minimal interface so you can log an episode quickly even when you're feeling terrible. VoiceOver is also supported.

## Free vs. premium

The app is free with full tracking for up to 30 days of history. Premium unlocks unlimited history, detailed statistics, and advanced export. Monthly subscription, cancel anytime.

## What this app is not

Migraine Me is a statistical tracking tool. It is not a medical device. It shows you numbers based on what you enter. It doesn't diagnose anything or recommend treatments. The point is to give you better data for conversations with your doctor, not to replace those conversations.

---

Migraine Me is on the [App Store](https://apps.apple.com/us/app/migraineme/id6755067713). Full [privacy policy here](https://dropbrain.io/migraineme/privacy_policy.html).
