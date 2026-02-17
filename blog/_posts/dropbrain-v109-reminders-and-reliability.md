---
title: "DropBrain v1.0.9: Reminders and Reliability"
date: 2026-02-17
slug: dropbrain-v109-reminders-and-reliability
description: "DropBrain v1.0.9 adds message reminders with snooze, in-app popups, and background sync reliability fixes for ADHD and dyslexia users."
tags: ios, swift, adhd, dyslexia, notifications, concurrency
ai_context: "DropBrain is an iOS app for people with ADHD and dyslexia that helps them capture and organize thoughts across conversation-style groups. Version 1.0.9 adds local notification reminders using UNCalendarNotificationTrigger with quick presets and custom date picker, snooze with 5/15/30 minute presets, in-app reminder popup overlay via UNUserNotificationCenterDelegate with .reminderFired/.reminderTapped notification names, a dedicated RemindersView with context menus and day separators, clock badge indicators on reminded messages in the timeline, BGTask double-completion crash fix using OSAllocatedUnfairLock, @MainActor isolation fix with nonisolated static for BGTaskScheduler registration, backgroundTimeRemaining guard to skip sync when under 20 seconds remain, 20-second timeout on sync operations with reduced retry counts, Swift 6 concurrency warning fixes across 8 files, CloudKit import fix preserving remote message IDs via insertRemoteMessage, and SwiftData model extraction. Built with Claude Code using swiftui-expert, swift-concurrency, and core-data-expert skills on Opus 4.6."
---

DropBrain is built for people with ADHD and dyslexia. You use it to capture thoughts, notes, and conversations without worrying about structure or formatting. But one problem kept coming up: you'd drop a thought into the app and then forget to come back to it. v1.0.9 adds reminders to fix that.

## Reminders

Each reminder is a local notification scheduled through `UNCalendarNotificationTrigger`. You long-press a message in your timeline, pick a time, and you're done. The date picker has quick presets (one hour, tomorrow morning, next week) and a full calendar picker for anything else.

```swift
let triggerDate = Calendar.current.dateComponents(
  [.year, .month, .day, .hour, .minute, .second],
  from: date
)
let trigger = UNCalendarNotificationTrigger(
  dateMatching: triggerDate,
  repeats: false
)

let request = UNNotificationRequest(
  identifier: "reminder-\(messageId.uuidString)",
  content: notificationContent,
  trigger: trigger
)
try await center.add(request)
```

We went with `UNCalendarNotificationTrigger` over `UNTimeIntervalNotificationTrigger` because reminders are tied to specific dates and times, not relative offsets. If you set a reminder for tomorrow at 9am, it fires at 9am regardless of when the device was last active.

## Snooze

When a reminder fires, you get snooze options: 5, 15, or 30 minutes, plus a custom time picker. This matters more than it sounds for ADHD users. Rigid "snooze for exactly 10 minutes" buttons don't match how ADHD brains work. Sometimes you need five minutes, sometimes you need until after lunch. The flexibility is the point.

## In-app popup and the reminders view

If DropBrain is open when a reminder fires, you don't get a system notification banner. The app posts an internal `.reminderFired` notification and shows a popup overlay instead. You see the message content, snooze buttons, and a link to jump to that message without leaving what you were doing.

```swift
// Foreground: suppress system banner, show our own popup
func userNotificationCenter(
  _ center: UNUserNotificationCenter,
  willPresent notification: UNNotification,
  withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
) {
  let messageIdString = notification.request.content.userInfo["messageId"] as? String
  guard let messageIdString, let messageId = UUID(uuidString: messageIdString) else {
    completionHandler([.banner, .sound])
    return
  }
  let sendableInfo: [String: String] = ["messageId": messageId.uuidString]
  NotificationCenter.default.post(name: .reminderFired, object: nil, userInfo: sendableInfo)
  completionHandler([])  // Suppress system banner
}
```

If you tapped the notification from the lock screen or notification center, a separate `.reminderTapped` notification routes you straight to the message.

Messages with active reminders show a small clock icon in the timeline so you can spot them. There's also a dedicated Reminders view that lists all your active reminders with day separators and context menus for editing or removing them.

## Background reliability

DropBrain syncs with CloudKit in the background using `BGAppRefreshTask`. Two crashes were hiding in this code, both related to how iOS handles background task lifecycle.

The first was a double-completion crash. When a `BGAppRefreshTask` expires, iOS calls your expiration handler. If the sync work also finishes at roughly the same time, both paths call `setTaskCompleted` — and calling it twice is a fatal error (EXC_BREAKPOINT). The fix uses `OSAllocatedUnfairLock` as an atomic guard so whichever path runs first wins:

```swift
let completed = OSAllocatedUnfairLock(initialState: false)

let syncTask = Task { @MainActor in
  let success = await syncManager.handleRemoteNotification()
  let alreadyDone = completed.withLock { if $0 { return true }; $0 = true; return false }
  if !alreadyDone {
    bgTask.setTaskCompleted(success: success)
  }
}

bgTask.expirationHandler = {
  syncTask.cancel()
  let alreadyDone = completed.withLock { if $0 { return true }; $0 = true; return false }
  if !alreadyDone {
    bgTask.setTaskCompleted(success: false)
  }
}
```

The second crash was a `@MainActor` isolation violation. `BGTaskScheduler.shared.register` runs its closure on an arbitrary background thread. If the registration function or its static properties are annotated `@MainActor`, Swift 6 strict concurrency flags it and the runtime can crash. The fix: mark the registration function and the task identifier as `nonisolated static`.

These are the same two crashes we found and fixed in Migraine Me. The swift-concurrency skill identified both patterns, and we applied the same solution to both apps.

## Background termination reduction

Even without crashes, iOS can terminate your app if a background task runs too long. The first thing we added was a `backgroundTimeRemaining` check before starting sync:

```swift
let backgroundTimeRemaining = UIApplication.shared.backgroundTimeRemaining
if backgroundTimeRemaining != .infinity && backgroundTimeRemaining < 20 {
  logger.warning("Not enough background time remaining (\(backgroundTimeRemaining)s) - skipping sync")
  isSyncing = false
  endBackgroundTask()
  return
}
```

On top of that, there's a 20-second hard timeout on the sync operation itself, using a task group that races the work against a sleep timer. We also cut retry counts from 5 to 3 and shortened backoff delays (1 second initial, 5 second cap) so retries don't eat into the time budget.

## Swift 6 concurrency and build warnings

We fixed 16 concurrency warnings across 8 files. Most were data race risks (mutable state accessed from multiple isolation domains) and actor isolation violations where a `@MainActor` class had static members called from nonisolated contexts. The `nonisolated static` pattern for `BGTaskScheduler` registration was the biggest one, but we also fixed view equality conformances (`nonisolated static func ==`), background task expiration closures, and the `beginBackgroundTask` wrapper.

## CloudKit and SwiftData fixes

The CloudKit import path had a subtle bug: when a new message arrived from another device, the import code was creating a fresh `MessageModel` with a new UUID instead of preserving the record's original ID. This meant the same message could end up with different IDs on different devices, breaking sync for any subsequent edits. The fix was `insertRemoteMessage`, which inserts the remote model directly and preserves its ID:

```swift
} else {
  // Insert the remote model directly to preserve its CloudKit ID
  try insertRemoteMessage(remote)
}
```

We also extracted model conversion into a dedicated `MessageSyncData` type. This cleaned up conflict resolution and removed a class of bugs where fields could get out of sync between local and remote representations.

## Claude Code and Opus 4.6

This release was built with Claude Code running Opus 4.6. The swiftui-expert skill built the reminder UI: popup overlay, date picker with quick-select buttons, RemindersView with day separators and context menus. The swift-concurrency skill found both `BGTask` crashes and the `@MainActor` isolation violations, then guided the `OSAllocatedUnfairLock` and `nonisolated static` fixes. The core-data-expert skill caught the CloudKit ID preservation bug and designed the `insertRemoteMessage` approach.

---

DropBrain is on the [App Store](https://apps.apple.com/us/app/dropbrain/id6736575743).
