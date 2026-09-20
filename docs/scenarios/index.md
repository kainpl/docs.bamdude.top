---
title: Scenarios
description: Real situations on a print farm, walked through end to end — which features take part, what to click, and what BamDude then does on its own
---

# Scenarios

The feature pages say what each feature does. These pages start from the other end: a **situation** on a real farm, with numbers, and the road from there to the result — through whichever features it takes, in the order it takes them.

Every scenario follows the same shape:

| Section | What it answers |
|---|---|
| **The situation** | Where you are — printers, models, what the customer said, what is going wrong. |
| **The goal** | What "done" looks like. |
| **What is involved** | The features that take part, with a link to each. |
| **Step by step** | What to open and what to press, and what you see after each step. |
| **What BamDude does on its own after that** | The part you do not have to do — the algorithm behind the button. |
| **Pitfalls and what-ifs** | The places people trip, and what happens when the plan meets reality. |

The farm in these pages is a made-up one: **48 printers of five models across three electrical phases**, a customer on the phone, and one operator. The numbers are there so the steps are concrete — swap in your own.

!!! tip "Where the truth is"
    A scenario describes the road as it is today. Where a step is still manual, the page says so rather than promising a button that does not exist — and the page is updated when the road changes.

---

## :material-transmission-tower: Power and starts

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-sine-wave: Three phases, one bed heating per phase](three-phases.md)
The farm sits on a three-phase supply and every plate-change round trips a breaker. Tags name the phase, the staggered start caps each phase on its own.
</div>

<div class="feature-card" markdown>
### [:material-flash: Keeping the breaker and the power bill in check](power-budget.md)
Staggered starts against the peak, smart-plug auto-off against the idle draw, and a kWh figure on every print so the cost is known, not guessed.
</div>

</div>

---

## :material-clock-outline: Queues and priorities

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-run-fast: An urgent print ahead of the queue](urgent-print.md)
Four brackets by lunchtime, on a farm where the auto-queue feeds every printer. Three ways to cut in, and which one to use when.
</div>

<div class="feature-card" markdown>
### [:material-printer-3d-nozzle: A hundred parts across five printer models](one-part-five-models.md)
One part, sliced once per model, wanted a hundred times. Let the plan split the count by what the farm can actually take, and send it in one go.
</div>

<div class="feature-card" markdown>
### [:material-weather-night: A night shift with nobody in the shop](unattended-night.md)
The auto-queue keeps the printers fed, swap mode clears plates, the alarms that matter get through quiet hours, and a failed print pauses itself.
</div>

</div>

---

## :material-clipboard-list: Orders and stock

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-calendar-question: The customer asks when fifty will be ready](when-will-it-be-ready.md)
From an order line to a date: the plan says what to print, the forecast says when the farm gets there, the filament table says whether the spools last.
</div>

<div class="feature-card" markdown>
### [:material-close-octagon: Recording scrap](recording-defects.md)
Three of the eight lids warped. Where the number goes, what it changes on the order, and what is counted for you when you skip an object mid-print.
</div>

<div class="feature-card" markdown>
### [:material-tray-full: Surplus on the shelf, reused by the next order](spare-parts-on-the-shelf.md)
The plate makes four, the order wanted three. The fourth goes onto a shelf, and the next order takes it instead of printing.
</div>

</div>

---

## :material-tools: Keeping the farm running

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-wrench-clock: Maintenance across fifty printers](maintenance-at-scale.md)
Nine task types that know which machine has rods and which has rails, print-hour intervals, and a Telegram button for the person holding the grease.
</div>

<div class="feature-card" markdown>
### [:material-television: A camera wall on the workshop TV](camera-wall-tv.md)
A screen on the wall that shows every camera and names no file — a kiosk token in the URL, nothing to log in to.
</div>

</div>
