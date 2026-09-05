---
title: Orders, Products & Stock
description: Customers, orders of product × quantity, products made of printed and purchased parts, a plan that says what to print next, and a free stock of spare parts
---

# Orders, Products & Stock

**Projects** in the sidebar opens three tabs: **Orders**, **Products** and **Customers**.

An order says *what is wanted* — so many of which product, for whom, by when, at what price. A product says *how it is made* — which printed and purchased parts go into one unit, and which sliced plates produce them. Progress is counted in finished units, worked out from the parts your prints actually produced.

Every figure on an order comes from **print history**: the archives, never the queue. The queue only ever answers "what is still waiting".

!!! info "This replaces the old projects with a print plan"
    Targets, the copies stepper, the separate bill-of-materials table and project export are gone — the product took all of that over. Existing projects are converted automatically; see [Upgrading from the old projects](#upgrading-from-the-old-projects).

---

## :material-account-group: Customers

A customer is a name, a free-form contact and notes. No discounts, no invoicing details — the price lives on the order.

A customer is **optional** on an order: internal work and test prints belong to nobody, and that is a normal state rather than a gap to fill.

| Where | What it shows |
|---|---|
| **Customers** tab | A flat table: name, contact, how many orders, how many are active / completed / cancelled, total price. |
| **Customer page** | The same figures, plus every order they placed rendered as the ordinary order cards. |
| **Orders** tab | Filter by customer, or group the list by customer. |

Deleting a customer keeps their orders — the orders simply stop belonging to anyone. Names are not forced to be unique, and two identical entries are told apart by hand: merging customers is deliberately not implemented.

---

## :material-clipboard-list: Orders

An order carries a name, an optional customer, a description, a colour badge, tags, a due date, a priority (Low / Normal / High / Urgent), an optional price, a URL, notes, attachments and a cover image.

### Order lines

A line is **`product × quantity`**, plus three optional fields:

| Field | Behaviour |
|---|---|
| **Material** | A **hard** requirement. A filament-type token (`PLA`, `PETG`, …) matched case-insensitively against the filaments a plate or a print carries. A line with no material takes anything. |
| **Colour** | A **note**. It is displayed and never filters anything — parts are routinely printed in whatever colour is loaded, sometimes from several spools at once. |
| **Note** | Free text for whatever the line needs remembering by. |

Lines are ordered, and the order matters: it decides which line gets a shared plate's parts first (see [Which order a print belongs to](#which-order-a-print-belongs-to)).

### Statuses and closing

An order is `active`, `completed` or `cancelled`, and **only you close it**. When every line has reached its quantity the page raises an *All lines are printed — close the order?* banner and stops there. A completed order can be reopened; a cancelled one keeps its whole history and is excluded from a customer's "done".

!!! tip "Pickers offer open orders"
    Anywhere an order is picked — the print dialog, the archive editor, the bulk archive action — the list is the **active** orders plus whatever is already bound, so an existing link is never hidden and never silently cleared by saving a dialog.

### The figures

The strip above the lines is computed by the server on every read; the browser never derives it.

| Figure | Meaning |
|---|---|
| **Ordered** | The sum of the line quantities. Literal — this is what the customer asked for. |
| **Printed** | Units printed. Literal too: it counts prints and nothing else. |
| **From stock** | Kits taken off the products' shelves (see [Free stock of parts](#free-stock-of-parts)), each line capped by its own quantity. |
| **Complete** | Units printed **plus the kits taken from stock**, limited by the purchased parts actually acquired. |
| **Remaining** | What is still to be made, after prints *and* kits from stock. |
| **Print time · Filament · Cost · Defective** | Summed over the order's prints. Time is the measured duration where one was recorded, else the slicer's estimate; filament is summed as it stands, including prints that never finished. |
| **Margin** | Price minus cost, shown when a price is set. |
| **Other prints** | How many prints belong to the order but to none of its lines. |

Each line expands into a row per printed part:

| Column | Meaning |
|---|---|
| **Per unit** | How many of this part make one unit of the product. |
| **Need** | Per unit × the quantity still to be made, after kits taken from stock. |
| **Usable** | Printed minus defective, over the line's completed prints. |
| **In progress** | Whatever is on a printer right now. |
| **Remaining** | Need minus usable, floored at zero. |
| **Surplus** | Usable minus what the line's **full** quantity requires, floored at zero. Kits from stock lower the need above; they never raise this. |

**Units printed is the minimum across parts** of usable ÷ per unit — the scarcest part decides, and the table shows at a glance which one it is. Progress is capped at 100 %: an overprinted line reports its excess through the printed-against-ordered counts and through each part's surplus, never through the bar. Prints in the trash count towards nothing.

### Which order a print belongs to

The unit of attribution is a print's **part row**, not the print. One plate can carry parts of two products (two different lids on one bed) and one file can belong to two products (a shared flask), so a single print can feed several lines. Three steps, in this order:

1. **A line you filed it under** is the print's home: every part row that line's product counts lands there in full, need or no need. Your hand is never second-guessed. Rows that product does not count fall through to step 2 among the other lines.
2. **Otherwise the plate names a set of products** — every product of the order that holds this file and plate. Candidate lines are this order's lines for those products, in line order, whose material accepts the print's filaments. Each part row is then handed out to the first candidate that counts it and still needs it, the remainder to the next such line, and whatever is left once every need is met to the first candidate that counts it — visible surplus, never discarded.
3. **Otherwise: Other prints.** Counted in time, filament and cost; never in parts. That is deliberate change given back rather than swallowed: *"printed PLA, PETG was ordered"* is worth seeing.

Prints filed by hand are resolved before loose ones, so what you filed already sits in a line's need when the rest is handed out. A print with no explicit line is re-attributed on **every read**, so editing lines rewrites the history under them — a property, not a leak.

!!! note "Whole-file plates"
    A plate index of `0` means "the whole file" — a single-plate 3MF or raw G-code — and matching a print against such a row sums every plate of that file. A non-zero index names one plate of a multi-plate 3MF.

### Prints, queue and activity

The order page's **Prints** section groups prints by the line they fed, with **Other prints** and, for anything bound to the order but named in no group, *Not filed under any group*. A badge says whether a print was **Filed** by hand or **Attributed** by the rules above. Row actions file a print under a line or remove it from the order; past twenty pages the notice becomes **Load older prints**.

Beneath it: **Queue** (what is still waiting for this order, with the line each item belongs to), **Activity** (prints started, completed, failed, cancelled, queued, auto-queued, and the order's own creation), **Notes** and **Attachments**.

To file many prints at once, select them on the [Archives](archiving.md) page and use **Assign to order**, which takes an order and optionally one of its lines.

---

## :material-package-variant: Products

A product is a **catalog entity** reused across orders. The product *is* the template — separate project templates no longer exist.

The catalog carries an **In catalog** flag. A product outside it is not offered when adding an order line, unless the line already points at it; a catalog grows forever, and without the flag the product picker would become the pain the project picker used to be.

| Action | What it does |
|---|---|
| **New product** | An empty product you fill in by hand. |
| **From file…** | Picks a library file, names the product after it, links it, and fills both the composition from its plates and the model card — with the pictures and documents the 3MF carries — from the file itself. "Print this file five times" never needs hand-authoring a product first. |
| **Import…** | Takes a ZIP exported from another BamDude — see [Export and import](#export-and-import). |
| **Duplicate** | Copies the composition with its aliases, the card, the attachments and the file / folder links. Never any history. |
| **Delete** | Refused with a clear message while any order line still references the product. Hide it from the catalog instead. |

### Composition: printed and purchased parts

| Kind | Fields |
|---|---|
| **Printed** | Name, **per unit**, aliases (the object names on the plates that mean this part), and a *from file* badge while the row is still the seeded default. |
| **Purchased** | Name, per unit, unit price, where to buy, remarks. |

Purchased parts are tracked **per order**, not per product: the order's procurement checklist holds need / acquired / remaining, so *"printed, waiting on screws"* is a state the page can show.

!!! tip "Per unit `0` means «do not measure this part»"
    The part stays in a plate's yield but creates neither need nor surplus — calibration cubes and test pieces riding along on a shared plate belong here.

Parts belong to a product, not to a global catalog: the same bracket in two products is two rows with two independent quantities. Within a product, merging one part into another moves its aliases across and the historical prints resolve to the survivor through the union — nothing is rewritten. Removing an alias makes that name its own part again on the next sync; renaming changes only the name.

### Plates as recipes

Linking a library **file or folder** to a product does everything else by itself: the product gains a plate row for every plate of every linked file, and every object name on those plates resolves to exactly one printed part — a name no part covers creates one, with the count on the plate where it was first seen as its per-unit figure. You review and correct it; editing a row clears the *from file* badge.

**A plate's yield is never cached.** Re-slice a file and the next read of the product yields something different, exactly as it should. Unlinking a file drops its plates and leaves the parts alone — quantities belong to the product, not to the file.

A plate linked to several products is normal. Each product sets the objects it does not use to `0` per unit, and attribution then hands each object to the product that counts it.

The product page lists plates grouped by file, with materials, colours, print time and filament for each, *Whole file* where the index is `0`, and a *not sliced* label where the file is a mesh rather than a sliced plate. An unsliced plate is a real recipe row and is shown rather than hidden — it is simply never planned.

The same part is often sliced **once per printer model**: several files, the same parts. That is a normal shape here, and the plan block knows about it — see [Alternative files per printer model](#alternative-files-per-printer-model).

### The model card

What a thing *is* — its description, designer, licence, source page and design ID, together with pictures, a bill of materials and an assembly guide — travels inside the 3MF the designer shipped. A product reads that from any file linked to it and keeps it in its own record.

- The pictures become a **gallery** you can reorder, add to and open full-size. One picture is the **cover**: whichever you pick, or an image you upload just for that, and the first picture in the gallery when you have picked nothing. It is what the product cards and the product strip on an order card show.
- The bill of materials and the assembly guide become **attachments filed by kind**, and what each kind accepts is deliberately narrow, so an attachments folder cannot be used as a place to park programs.
- **Re-read from file…** fills what is still blank and refreshes only the attachments that came from that same file. A field you filled keeps your value — clear it first if you want the file's version.
- **Nothing is ever written back into a library file.** Those bytes are the basis of deduplication and of the archive chain of custody.

Any 3MF in the library shows the same card, read-only, from its **Model card** entry in the [File Manager](file-manager.md), with **Create product from this file** on it.

The product page also reports **Printed for orders** — units of this product made across every order it appears in, of any status. It is not "how many times this file was printed": a print outside an order does not count here.

### Export and import

**Export** packs a product into a ZIP — the card, the composition, the attachments, the cover and every linked file. **Import** unpacks it on another BamDude: files it already has are matched by content and reused, anything genuinely new is ingested into the library through the ordinary upload path so hashing, dedup and metadata stay the library's, and the plates come back from the files themselves. Anything the imported files cannot account for is reported to you as a warning rather than quietly invented.

Orders have no export: they are local to the farm that took them.

---

## :material-lightbulb-on: What to print next

Under the lines, each line carries a plan: the plates that would cover what it still needs, ranked by **how many useful parts each one makes per hour of print time**. Everything already printed, running, queued for that line or reserved from stock is subtracted first, so a plan you have half-sent stops asking for the prints you already sent.

| Element | Behaviour |
|---|---|
| **Row** | A plate (or *Whole file*), the parts it covers, and a count you can change. Time, filament and cost are shown **per print**. |
| **Surplus after this plan**, and the totals | Follow the count as you type — a what-if over work not yet sent, not an order figure. |
| **Add a plate…** | Adds a plate the plan did not pick, at a count of one. |
| **Not sliced** | Plates that cannot be planned are listed under their own muted heading. |
| **No plate for a part** | A part no candidate plate makes at all is named rather than quietly left out, with a link to the product's files. |

A plan that stops at its safety limit says so, instead of looking exactly like a finished one.

!!! warning "Nothing here asks whether a printer is free"
    Choosing a queue says where the work is filed; whether a machine can take it is decided at dispatch, exactly as for anything else in a queue. See [Auto-Queue → Routing is not dispatching](auto-queue.md#routing-is-not-dispatching).

A closed order plans nothing, and the block says so rather than disappearing — a section that is simply absent reads as "this order has nothing to print", which is the one thing a failed or closed plan must not say.

### Alternative files per printer model

When a part is sliced for two machines there are two files with the same yield, and a plan that picked one of them would hide the other — even where half the farm can print nothing else.

Each row therefore carries a **File** switch listing the other candidate plates whose yield of the parts *this line counts* is identical, each labelled with the printer model its file was sliced for. Choosing one re-does that row's time, filament and cost while the count stays exactly where it was, because the two files make the same parts.

- **To printer…** on such a row asks which machine first, then opens the usual print dialog already holding the file that machine was sliced for, with the printer pinned. A printer in maintenance mode is not offered; an archived one never appears.
- **Split across files** shares one row's count between them. The auto-queue routes an item by the model its file names, so this is the only way one order line's work reaches two printer models at once — and the numbers have to add up to the row's count, or that row and the whole plan refuse to be sent rather than quietly sending the wrong number.
- A file a row already offers this way is no longer listed under **Add a plate…**, where it would put the same work on screen twice.

### Sending the plan to the queue

A single row goes to the auto-queue on its own, the whole plan goes at once, or **To printer…** opens the usual print dialog for one machine. That dialog opens at one copy — set the number there.

Both queue targets fill in the **print options you saved as a preference** (swap macros, calibration and the rest) — the same profile the print dialog reads. The preference is looked up by the chosen printer's model, or, for the auto-queue, by the model the file was sliced for, so one plan spanning two machines reads two profiles. Swap macros stay muted where they would fire twice: on a printer with swap mode off, or for a file that already carries them baked in.

---

## :material-file-document-edit: Filing a print under its order

Starting or queueing a **library file** — from the [File Manager](file-manager.md), a printer card, the [Queue](print-queue.md) page or the [auto-queue](auto-queue.md) panel — shows an **Order** field.

- The list holds the open orders that have a line whose product contains this plate, each with the product and **how many prints it still needs**. It is ranked needs-first, then by order priority, then by deadline, then by age. How *much* is still needed does not rank, because sorting by it would starve either the big order or the nearly-finished one.
- The first order that still needs the plate is chosen for you. When none of them needs it, **Without an order** is the default and the candidates stay selectable — printing ahead is legitimate.
- An order whose lines the plate cannot tell apart is offered **once per line**, each labelled with its material. Refusing to guess between two lines is not a reason to hide the choice from you.
- Switching plates re-asks, because a different plate makes different parts. With several plates ticked, the order travels with the print and the **line is worked out per plate**, so two plates of one file can land on two different lines.
- The field appears only where nobody has answered already — the plan block names its own line, and a reprint from an archive keeps the original print's — and only for operators who may read orders at all.

Behind the field, two rules work together. When a queue writer is given an order and the plate belongs to **exactly one** of its lines, that line is recorded for you, the plate's own filament picking between two lines of the same product; where two lines genuinely cannot be told apart, nothing is guessed. And the plan counts queue rows that carry **no** line anyway, resolving each of them the same way on every read — so anything queued before this existed, from the API or from Telegram or by hand, starts counting without anybody touching it.

A print started from the printer's own screen is filed afterwards: the archive editor carries an order picker and a line picker, and the Archives page's **Assign to order** does it for a whole selection.

---

## :material-tray-full: Free stock of parts

A plate makes four lids and the order needed three. The fourth is not a rounding error, it is a thing on a shelf — and this is where it lives.

Stock is a **ledger of movements**, never a counter. A part's balance is the sum of its movements; a product's **kits** are the whole units the shelf can already make — the minimum across counted parts of balance ÷ per unit, the same "scarcest part decides" rule that drives a line's progress. There are exactly five reasons, and the reason decides the sign:

| Reason | Sign | When |
|---|---|---|
| **Surplus banked** | + | You pressed **Bank the surplus** on an order. |
| **Print without an order** | + | A print completed belonging to no order. |
| **Reserved for an order** | − | A line took kits off the shelf. |
| **Reservation released** | + | That line gave them back. |
| **Hand correction** | ± | You counted the shelf yourself. |

Only a **counted printed part** — printed, with a per-unit quantity above zero — has stock. Purchased parts are procurement, and stay out of all of this.

### Banking a surplus

**Bank the surplus** sits in the order header. One press moves each line's extra parts onto their products' shelves and tells you what moved. Only the **difference** moves, so pressing it again moves nothing and says so rather than pretending, and you can press it again later when more surplus has appeared. A cancelled order can bank too — the parts did not disappear when the order did.

It is deliberately not automatic. A surplus is sometimes shipped with the order and sometimes scrapped, and only the operator knows which.

!!! warning "Surplus is measured against the full quantity of a line"
    Kits taken from the shelf lower a line's *need* — and its progress, and its plan — but they never raise its surplus. They are a loan, and releasing the reservation is what gives them back; the button never does. Otherwise the same kits would land on the shelf twice.

### Prints without an order

A print that completes filed under **no** order is credited to stock automatically, good parts only — printed minus defective. The accounting then follows you if you change your mind: file that print under an order afterwards and the credit is taken back; take it back out and it returns. A reversal that would push a part below zero is refused, but the print is still filed — those parts were already spent, and refusing the filing would punish you for the books not balancing.

Prints from before this existed are **not** swept up: a farm with years of history would grow a shelf nobody has ever seen. The archive editor offers **Count into stock** for a print that **finished successfully** and belongs to no order, one at a time, when you say so — a failed or cancelled print made nothing there is anything to count.

### Taking kits from stock

A line for a product with something on its shelf offers **From stock** under the quantity, defaulting to what is available and capped by the line's own quantity. What you take is **reserved for that line**, and every figure counts it as done — the need, the progress bar, the plan and the close-the-order banner — so a line covered from the shelf asks for no prints at all.

The request is trimmed to what is actually there at the moment you save, and you are told when it was: a neighbouring order may have taken the last two while the dialog was open.

The reservation comes back on its own when the line is deleted, when its quantity drops below the reservation, when the order is cancelled, and when the order is deleted. Deleting an order does one thing more: its finished prints stop belonging anywhere, so they are credited back onto the shelf as order-less prints. Both movements are marked *the order was deleted* in the table.

Three things it deliberately does **not** do:

- a **completed** order gives none of that back — not when it is cancelled, not when one of its lines goes, not when the order itself is deleted, and its prints are not re-credited either: those kits went out inside the units the customer received, and the prints went with them. **One door stays open even then.** Typing a new **From stock** number on a completed order's line still releases the old reservation and takes the new one — that field is the operator correcting what the order took off the shelf, and refusing it would leave a mistake with nowhere to be fixed. The other three doors only dispose of paperwork and say nothing about the parts, which is why they stay shut.
- reopening a cancelled order does not re-reserve, because the shelf may have gone to somebody else in the meantime.
- a **duplicated** order reserves nothing, because a reorder must not quietly empty the shelf.

### The shelf on the product page

**Free stock** sits under the composition: the kit count as its headline, a balance for every counted part — zeros included, because an empty shelf and a product with nothing to count are different answers — and the movements table with date, part, the signed change, the reason, where it came from and any note. The table shows the most recent movements and says so when that is all it is showing.

**Adjust** writes a correction as a movement with a note you must supply, never as a silent overwrite, and a correction that would take a part below zero is refused. In the catalog, a product card carries its kit count as a badge when there is anything on the shelf.

Deleting a part removes its ledger; **merging** two parts moves the movements onto the survivor, because a merge says the two were always the same thing. Deleting a product removes the ledgers of all its parts. Deleting a print leaves its movements alone and simply drops the reference — the parts are still on the shelf.

---

## :material-shield-key: Permissions

Orders, products, customers, the plan and the shelf all live under one family of permissions — nothing new was added for any of them.

| Permission | Covers |
|---|---|
| `projects:read` | Reading orders, products, customers, the plan block and the free stock. |
| `projects:create` | Creating an order, a product or a customer. |
| `projects:update` | Editing them, filing prints, sending a plan to a queue, banking a surplus, reserving kits and correcting the shelf. |
| `projects:delete` | Deleting them. |

For [API keys](api-keys.md#permission-model), the **Manage Projects** scope (`can_manage_projects`) carries create / edit / delete across all three entities; read-only access rides `can_read_status`. The scope is off on existing keys after an upgrade and is granted per key under **Settings → API Keys**.

---

## :material-database-arrow-right: Upgrading from the old projects

The upgrade migration converts everything in place, in one transaction, and needs nothing from you.

- **Every project becomes one product plus one order** with a single line. Print history stays attached, and every print, queue item and auto-queue item of the project gets that order line.
- **Templates become products** with no order behind them; their attachments are copied across to the product.
- **Files and folders move their links** from projects to products, each print-plan row becomes a plate of the product, and per-part targets and bill-of-materials rows become printed and purchased parts.
- **Old targets are preserved wherever they can be preserved exactly.** Per-part targets become a kit ordered N times, so a product reads as *1 + 1, ordered × 780* rather than *780 + 780, ordered × 1*. A project-level target becomes the order quantity where it divides exactly, and stays at one rather than rounding where it does not. A product whose files were deleted long ago takes its parts from its own completed prints.
- The old budget becomes the order's **price**, the old *archived* status becomes **completed**, and nested projects are flattened.
- **Library files that never recorded what they hold get it filled in** during the upgrade, and tried again at every start for the ones an unreachable network share put out of reach. A product bound to such a file gains its parts the moment its file does.

Gone with the change: plate and per-part targets, project templates, nested projects, project export and import, and the separate bill-of-materials and print-plan tables with their editors. Library files now link to a **product** rather than to an order.

!!! note "The shelf starts empty"
    Nothing is backfilled into [free stock](#free-stock-of-parts). Which of your historical prints were shipped years ago is not something a migration can know, so the shelf begins at zero and fills from the first order-less print or the first press of **Bank the surplus**.

---

## :material-link-variant: See also

- [File Manager](file-manager.md) — linking files and folders to products, and the model card of any 3MF.
- [Per-Printer Queues](print-queue.md) and [Auto-Queue Routing](auto-queue.md) — where the **Order** field appears when you queue a file.
- [Print Archiving](archiving.md) — filing a print under an order after the fact, and counting an order-less print into stock.
- [Spool Inventory](inventory.md) — where the filament figures on an order come from.
