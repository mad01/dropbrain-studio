---
title: "Migraine Me v1.1.8: HIT-6, Widgets, and Sync Fixes"
date: 2026-02-17
slug: migraine-me-v118-smarter-tracking-better-insights
description: "Version 1.1.8 adds the HIT-6 questionnaire, a statistics dashboard, home screen widgets, PDF report export, and fixes two background sync crashes."
tags: ios, swift, migraine, health, swiftui, concurrency
ai_context: "Migraine Me v1.1.8 is an iOS app update introducing the HIT-6 (Headache Impact Test) clinically validated questionnaire with SwiftData persistence, a progressive-disclosure statistics dashboard built with ExpandableStatsSection and @AppStorage, home screen and lock screen WidgetKit widgets sharing data through App Groups via SharedDataManager, PDF report generation for doctor visits using UIGraphicsPDFRenderer, two BGTask crash fixes (double-completion guarded by OSAllocatedUnfairLock and @MainActor isolation resolved with nonisolated static), an actor-based PendingSyncQueue for durable CloudKit sync operations, and development assisted by Claude Code Opus 4.6 with swiftui-expert, swift-concurrency, and core-data-expert skills."
---

Version 1.1.8 adds the HIT-6 questionnaire so you can put a number on headache impact, a statistics dashboard that organizes your data into expandable sections, a home screen widget for checking your streak at a glance, and PDF reports you can hand to your doctor. Two background task crashes were also found and fixed, and sync now survives app termination.

## HIT-6 Headache Impact Test

The HIT-6 is a six-question survey that doctors actually use to measure how headaches affect daily life. Each question has five possible answers scored from 6 to 13 points, giving a total between 36 and 78. The app maps that total to one of four severity categories:

```swift
public enum HIT6Category: String, Codable, Sendable {
  case littleImpact = "LittleImpact"       // 36-49
  case someImpact = "SomeImpact"           // 50-55
  case substantialImpact = "SubstantialImpact" // 56-59
  case severeImpact = "SevereImpact"       // 60-78

  public static func from(score: Int) -> HIT6Category {
    switch score {
    case ...49: return .littleImpact
    case 50...55: return .someImpact
    case 56...59: return .substantialImpact
    default: return .severeImpact
    }
  }
}
```

Results are stored as a SwiftData `@Model` so they persist across launches and sync with iCloud. The scoring itself is a one-liner: `answers.reduce(0) { $0 + $1.rawValue }`. Having a standardized number over time gives you something concrete to show your neurologist instead of "I think they're getting worse."

## Statistics dashboard

The previous version had basic statistics. This release replaces them with a dashboard that shows the most important numbers up front and hides the rest behind collapsible sections.

The top row (hero metrics and quick facts) is always visible. Below that, detail sections for episode breakdowns, triggers, symptoms, medications, HIT-6 history, and recovery actions are wrapped in `ExpandableStatsSection`:

```swift
ExpandableStatsSection(
  title: NSLocalizedString("stats.section.triggers", comment: ""),
  icon: "bolt.trianglebadge.exclamationmark.fill",
  iconColor: colors.warning,
  isExpanded: $triggersExpanded
) {
  triggerContent(triggerData)
}
```

Each section's expanded/collapsed state is persisted with `@AppStorage` so the dashboard remembers how you left it between sessions:

```swift
@AppStorage("statsTriggersExpanded") private var triggersExpanded = true
@AppStorage("statsSymptomsExpanded") private var symptomsExpanded = true
@AppStorage("statsMedicationsExpanded") private var medicationsExpanded = true
```

A period selector at the top lets you switch between 7-day, 30-day, 90-day, and all-time views. Delta indicators compare the current period against the previous one, so you can see whether things are trending better or worse.

## Home screen widget

There's now a Migraine Me widget for your home screen or lock screen. The small widget shows four things: migraine count, headache count, current streak, and whether you have an active episode. If an episode is running, it flips to a rose-colored indicator with a live timer.

Data flows from the main app to the widget through `SharedDataManager`, which writes to an App Group `UserDefaults` container:

```swift
struct SharedDataManager {
  static let appGroupIdentifier = "group.com.migraineme.app"

  static func updateWidgetData(
    lastEpisodeDate: Date?,
    currentStreak: Int,
    hasActiveEpisode: Bool,
    activeEpisodeStartDate: Date? = nil,
    activeEpisodeType: String? = nil,
    migrainesLast30Days: Int = 0,
    headachesLast30Days: Int = 0
  ) {
    guard let defaults = sharedDefaults else { return }
    // ... write values ...
    WidgetCenter.shared.reloadAllTimelines()
  }
}
```

The widget also supports a `refreshFromDisk()` path that reads the shared `HealthEntries.json` file directly, so it can recompute stats during background refresh without the main app running. Lock screen widgets (circular and rectangular families) are included for quick streak checks.

## PDF report export

When you need to share data with your doctor, a printed summary beats scrolling through an app together. You pick a date range (30, 60, or 90 days) and get a PDF with episode counts, migraine-free streaks, average intensity and duration, monthly headache day trends, HIT-6 scores, medication effectiveness with time-to-relief numbers, trigger and symptom frequencies, and a full timeline of every episode.

The PDF is generated on-device with `UIGraphicsPDFRenderer` and saved to your Documents folder. Nothing leaves your phone unless you share the file yourself.

## Background task reliability

Two crashes were hiding in the background task handling. Both showed up as `EXC_BREAKPOINT (SIGTRAP)` on background threads, which made them hard to trace back to the actual cause.

**Double-completion crash.** `BGTask.setTaskCompleted(success:)` is a one-shot call. If both the expiration handler and the async work completion path call it, the system kills your process. The race is straightforward: expiration fires while async work is still running, both paths reach `setTaskCompleted`, and the second call traps.

The fix uses an `OSAllocatedUnfairLock` as an atomic guard so whichever path runs first wins:

```swift
nonisolated static func handleBGTask(
  _ task: BGTask,
  work: @escaping @Sendable () async -> Bool
) {
  let bgTask = SendableTask(task: task)
  let completed = OSAllocatedUnfairLock(initialState: false)

  let workTask = Task {
    let success = await work()
    if completed.withLock({
      if $0 { return true }; $0 = true; return false
    }) == false {
      bgTask.task.setTaskCompleted(success: success)
    }
  }

  task.expirationHandler = {
    workTask.cancel()
    if completed.withLock({
      if $0 { return true }; $0 = true; return false
    }) == false {
      bgTask.task.setTaskCompleted(success: false)
    }
  }
}
```

**@MainActor isolation crash.** `AppDelegate` conforms to `UIApplicationDelegate`, which in Swift 6 infers `@MainActor` on the entire class. Every closure defined inside an instance method inherits that isolation. `BGTaskScheduler` calls its handler closures on an internal background queue, so the runtime hits `_dispatch_assert_queue_fail` and traps.

The fix moves BGTask registration into a `nonisolated static` method, which breaks the `@MainActor` inheritance chain:

```swift
nonisolated static let appRefreshIdentifier = "com.migraineme.app.refresh"

nonisolated private static func performTaskRegistration() {
  BGTaskScheduler.shared.register(
    forTaskWithIdentifier: appRefreshIdentifier,
    using: nil
  ) { task in
    handleBGTask(task) {
      await BackgroundSyncService.shared.performAppRefresh()
    }
  }
}
```

The widget made this crash reliably reproducible. With a 15-minute refresh interval during active episodes, the BGTask handler fires frequently enough that the queue assertion failure went from "rare background crash" to "consistent crash after locking the phone." The swift-concurrency skill identified both issues by analyzing the actor isolation chain from `UIApplicationDelegate` through instance method closures to the BGTask handler.

## Pending sync queue

CloudKit sync can fail for all the usual reasons: no network, iCloud quota, transient server errors. Before this release, failed operations were just lost when the app got killed. Now there's an actor-based `PendingSyncQueue` that writes pending operations to the App Group container as JSON:

```swift
public actor PendingSyncQueue {
  public static let shared = PendingSyncQueue()

  private var operations: [SyncOperation] = []
  private let maxRetries = 5

  public func enqueue(_ operation: SyncOperation) {
    operations.removeAll {
      $0.entryId == operation.entryId && $0.type == operation.type
    }
    operations.append(operation)
    saveToDisk()
  }

  public func markFailed(_ operationId: UUID) {
    guard let index = operations.firstIndex(where: { $0.id == operationId })
    else { return }
    operations[index].retryCount += 1
    if operations[index].retryCount > maxRetries {
      operations.remove(at: index)
    }
    saveToDisk()
  }
}
```

The queue deduplicates by entry ID and operation type, so if you update the same record three times while offline, only the latest operation is queued. Failed operations are retried up to five times before being dropped. Using a Swift actor makes the queue thread-safe without manual lock management, which the swift-concurrency skill recommended over the original `DispatchQueue`-based approach.

## Built with Claude Code and Opus 4.6

This release was built with three Claude Code skills. The swiftui-expert skill designed the `ExpandableStatsSection` component and the widget views. The swift-concurrency skill found both BGTask crashes by tracing the `@MainActor` isolation chain and the `setTaskCompleted` race, and it recommended the actor-based `PendingSyncQueue` over the original `DispatchQueue` approach. The core-data-expert skill guided the SwiftData model for `HIT6Result`, including the `categoryRaw` / computed `category` pattern for storing enums.

---

Migraine Me is on the [App Store](https://apps.apple.com/us/app/migraineme/id6755067713).
