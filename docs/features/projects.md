---
title: Orders, Products & Stock
description: Customers, configurable products, orders, print plans, finished-goods stock and dispatch notes
---

# Orders, Products & Stock

**Projects** in the sidebar opens four sections: **Orders**, **Products**, **Customers** and **Stock**. Each section has its own permissions. The Orders list opens as cards until you save a different view in this browser; cards, table, kanban, workspace and deadlines remain available.

An order says *what is wanted* — so many of which product, for whom, by when, at what price. A product says *how it is made* — which printed and purchased parts go into one unit, and which sliced plates produce them. Progress is counted in finished units, worked out from the parts your prints actually produced.

Completed output comes from **print history** in the archives. The order also shows live and queued work, stock reservations and issues separately, so a planned or queued job never counts as a finished part.

!!! info "This replaces the old projects with a print plan"
    Targets, the copies stepper, the separate bill-of-materials table and project export are gone — the product took all of that over. Existing projects are converted automatically; see [Upgrading from the old projects](#upgrading-from-the-old-projects).

---

## :material-account-group: Customers

A customer has a name, a type, a code, several contacts with delivery details, and notes. The price lives on the order.

A customer is **optional** on an order: internal work and test prints belong to nobody, and that is a normal state rather than a gap to fill.

| Where | What it shows |
|---|---|
| **Customers** section | Searchable, paged cards or table with contacts, order counts and totals. |
| **Customer page** | Contacts, order figures, paged orders and dispatch notes. |
| **Orders** section | Filter by customer or group the list by customer. |

Deleting a customer keeps their orders — the orders simply stop belonging to anyone. Names are not forced to be unique, and two identical entries are told apart by hand: merging customers is deliberately not implemented.

---

## :material-clipboard-list: Orders

An order carries a name, an optional customer, a description, a colour badge, tags, a due date, a priority (Low / Normal / High / Urgent), an optional price, a URL, notes, attachments and a cover image.

### Order lines

Orders also have a stage and a responsible operator, separate from active/completed/cancelled status. Use the list's cards, table, kanban, workspace or deadline view to follow the same work. The readiness forecast names missing estimates or unplaceable plates instead of treating them as zero; the order detail shows machine-hours by printer model. See [When will it be ready?](../scenarios/when-will-it-be-ready.md).

A line is **`product × quantity`**, plus three optional fields:

| Field | Behaviour |
|---|---|
| **Material** | A **hard** requirement. A filament-type token (`PLA`, `PETG`, …) matched case-insensitively against the filaments a plate or a print carries. A line with no material takes anything. |
| **Colour** | A **note**. It is displayed and never filters anything — parts are routinely printed in whatever colour is loaded, sometimes from several spools at once. |
| **Note** | Free text for whatever the line needs remembering by. |

Lines are ordered, and the order matters: it decides which line gets a shared plate's parts first (see [Which order a print belongs to](#which-order-a-print-belongs-to)).

### Statuses and closing

An order is `active`, `completed` or `cancelled`, and **only you close it**. When every line is covered by printed kits or kits allocated from stock, the page raises an *All lines are covered — close the order?* banner and stops there. A completed order can be reopened; a cancelled one keeps its whole history and is excluded from a customer's "done".

!!! tip "Pickers offer open orders"
    Anywhere an order is picked — the print dialog, the archive editor, the bulk archive action — the list is the **active** orders plus whatever is already bound, so an existing link is never hidden and never silently cleared by saving a dialog.

### The figures

The strip above the lines is computed by the server on every read; the browser never derives it.

| Figure | Meaning |
|---|---|
| **Ordered** | The sum of the line quantities. Literal — this is what the customer asked for. |
| **Printed** | Units printed. Literal too: it counts prints and nothing else. |
| **From stock** | Kits taken off the products' shelves (see [Free stock of parts](#free-stock-of-parts)), each line capped by its own quantity. |
| **Covered** | Printed kits plus kits allocated from stock, capped separately on every line before the order is added up. This is the bar's numerator and the quantity left to make is derived from it. An overprint of one product cannot cover another product's shortage. |
| **Can assemble** | The covered printed kits, limited by the purchased parts actually acquired. This does not mean the order was shipped or closed. |
| **Left to cover** | What is still to be made after prints *and* kits from stock, summed from the deficits of individual lines. |
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

**Units printed is the minimum across parts** of usable ÷ per unit — the scarcest part decides, and the table shows at a glance which one it is. The **Covered** bar uses those units plus allocated stock, capped to each line's own quantity; it cannot read 100% while a different line is still short. An overprinted line reports its excess through the printed-against-ordered counts and through each part's surplus, never through the bar. Prints in the trash count towards nothing.

**Printing** is a count of live print archives; **Queued** is a count of pending jobs, not an estimate of product units. A shared plate can contribute to more than one line, so neither counter is added up from line rows.

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

**Defects.** Every completed print card shows what came off the plate and how many went in the bin, and its menu offers **Defects…** — one counter per part, capped at what the plate made, saved under the order's own permission. The order's *Defective*, *Remaining* and progress move at once. See [Recording defects](../scenarios/recording-defects.md).

---

## :material-package-variant: Products

A product is a **catalog entity** reused across orders. The product *is* the template — separate project templates no longer exist.

A product can have a SKU, version and category. It stays a **draft** until marked **ready to print**, which requires a part and a printable plate; if those disappear later, it is shown as incomplete. Variant groups let one product describe choices such as straight or angled parts. Each order line stores its chosen options and part counts, so changing the product's default later does not rewrite an existing order. A line may also request selected parts without ordering a whole kit.

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

!!! tip "Per unit `0` means «out of the kit»"
    The part is still counted for the product and can be ordered separately, but it does not contribute to a standard kit. Use **Not counted** for a calibration cube or another object that is not a product part at all.

Parts belong to a product, not to a global catalog: the same bracket in two products is two rows with two independent quantities. Within a product, merging one part into another moves its aliases across and the historical prints resolve to the survivor through the union — nothing is rewritten. Removing an alias makes that name its own part again on the next sync; renaming changes only the name.

### Additional printed parts

!!! info "After 0.7.0"
    Saved extra percentages are available in the current development branch after 0.7.0. They are not in the `0.7.0` release image.

In a printed part's editor, set an **additional percentage** to include spare parts in new order lines. For ten products containing three A parts each, 10% adds three A parts: the plan needs 33 A parts in total. The extra quantity rounds up once for the whole order line. Purchased parts and lines ordered in **parts mode** do not receive implicit extras.

Each new line keeps its percentage. Changing the catalog default affects future lines; it does not rewrite existing orders. Changing a part's base count, ignoring it, deleting it or merging it is refused when that would invalidate a saved extra-part obligation. Configure the order line before receiving or issuing its goods.

Extras are received and issued separately in **Stock and issue**. A customer order must include them in its delivery before it can close. An order without a customer can close to free stock once its main units have been received or assembled and its extras received. These planned extras are not surplus available to bank a second time.

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

Under the lines, each line carries a plan: the plates that would cover what it still needs. Where the farm has a usable lane for more than one recipe, the first choice is a **finish-sooner heuristic**: its printer models, how many lanes they have and work already occupying them come before the old useful-parts-per-hour tie-break. This can deliberately spend more machine-hours to finish the order earlier; it is not an optimisation proof or a dispatch reservation. Everything already printed, running, queued for that line or reserved from stock is subtracted first, so a plan you have half-sent stops asking for the prints you already sent.

| Element | Behaviour |
|---|---|
| **Row** | A plate (or *Whole file*), the parts it covers, and a count you can change. Time, filament and cost are shown **per print**. |
| **Surplus after this plan**, and the totals | Follow the count as you type — a what-if over work not yet sent, not an order figure. |
| **Add a plate…** | Adds a plate the plan did not pick, at a count of one. |
| **Not sliced** | Plates that cannot be planned are listed under their own muted heading. |
| **No plate for a part** | A part no candidate plate makes at all is named rather than quietly left out, with a link to the product's files. |

A plan that stops at its safety limit says so, instead of looking exactly like a finished one.

!!! warning "The plan sees capacity; dispatch still decides readiness"
    A read-only farm snapshot supplies active, unpaused, AutoQueue-eligible lanes and their current work. An offline printer is not discarded merely for being offline; archived, maintenance, paused and AutoQueue-disabled printers receive no new planned work. Filament, live connectivity and every final queue gate remain dispatch-time checks. If no usable lane matches the only recipe, BamDude keeps that recipe visible so the forecast can say why it cannot run yet. See [Auto-Queue → Routing is not dispatching](auto-queue.md#routing-is-not-dispatching).

A closed order plans nothing, and the block says so rather than disappearing — a section that is simply absent reads as "this order has nothing to print", which is the one thing a failed or closed plan must not say.

### Alternative files per printer model

When a part is sliced for two machines there are two files with the same yield, and a plan that picked one of them would hide the other — even where half the farm can print nothing else.

Each row therefore carries a **File** switch listing the other candidate plates whose yield of the parts *this line counts* is identical, each labelled with the printer model its file was sliced for. Choosing one re-does that row's time, filament and cost while the count stays exactly where it was, because the two files make the same parts.

- **To printer…** on such a row asks which machine first, then opens the usual print dialog already holding the file that machine was sliced for, with the printer pinned. A printer in maintenance mode is not offered; an archived one never appears.
- **Split across files** shares one row's count between them. The auto-queue routes an item by the model its file names, so this is the only way one order line's work reaches two printer models at once — and the numbers have to add up to the row's count, or that row and the whole plan refuse to be sent rather than quietly sending the wrong number.
- A file a row already offers this way is no longer listed under **Add a plate…**, where it would put the same work on screen twice.

With **Rebalance across printer models** on (Settings → Printing → Auto-Queue Routing), the split is a starting point: still-pending copies can later move to whichever model frees up first — see [Rebalancing across printer models](auto-queue.md#rebalancing-across-printer-models).

### Sending the plan to the queue

A single row goes to the auto-queue on its own, the whole plan goes at once, or **To printer…** opens the usual print dialog for one machine. That dialog opens at one copy — set the number there.

Both queue targets fill in the **print options you saved as a preference** (swap macros, calibration and the rest) — the same profile the print dialog reads. The preference is looked up by the chosen printer's model, or, for the auto-queue, by the model the file was sliced for, so one plan spanning two machines reads two profiles. Swap macros stay muted where they would fire twice: on a printer with swap mode off, or for a file that already carries them baked in.

Once queued, a copy belongs to its file's model until rebalancing moves it — automatically with the setting on, or with the line's **Rebalance** button.

### Plate and feed-rule validation

Before creating jobs, the server validates every selected source in that request: the actual plate, its G-code, model, used channels, and required nozzles. If a source is invalid, that request does not create part of the plan while silently omitting the rest.

**Whole file** stays a recipe choice. If the 3MF contains one unambiguous printable plate, the queue receives its actual number, including 2 or 5. Several printable plates need an explicit selection. Choosing Auto-Queue does not make an unsliced recipe printable.

Automatic and named-printer targets receive the same plate requirements. Auto-Queue keeps the exact model of the selected alternative file; quantity, order line, and the split of copies between files stay intact. A multicolor plan is allowed when every channel has its own compatible source. Copy count never grants automatic permission to change colors. See [Filament Routing](filament-routing.md).

A production plan does not confirm that a ready printer exists: a valid job can wait for the required filament or printer state. Preparation that never starts a print is not counted as produced parts or a completed print.

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

Stock is a **ledger of movements**, never a counter. A part's balance is the sum of its movements; a product's **kits** are the whole units the shelf can already make — the minimum across counted parts of balance ÷ per unit, the same "scarcest part decides" rule that drives a line's progress. Each movement has a reason that decides its sign. Common examples:

| Reason | Sign | When |
|---|---|---|
| **Surplus banked** | + | You pressed **Bank the surplus** on an order. |
| **Print without an order** | + | A print completed belonging to no order. |
| **Reserved for an order** | − | A line took kits off the shelf. |
| **Individual parts reserved** | − | A line took loose parts, including incomplete kits or additional parts. |
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

### Taking individual parts from stock

!!! info "After 0.7.0"
    Reserving incomplete kits by individual component is available after 0.7.0. The `0.7.0` release supports finished goods and complete stock kits; it does not implement the loose-component flow below.

**Take from stock** can reserve incomplete kits as well as finished products and complete kits. If ten products need A×3 and B×1, taking A30 from stock leaves only B10 to print. When B10 is printed, the receipt uses the reserved A parts to complete the ten products.

The banner names the individual parts and quantities. Reservations belong to the order; simply viewing its plan does not consume free stock. A later delivery offers only the components still missing, including planned additional parts. Repeating the action does not reserve the same parts twice. Cancellation or a reduced quantity returns unused reservations, and the activity journal records what was taken.

### Taking kits from stock

A line for a product with something on its shelf offers **From stock** under the quantity, defaulting to what is available and capped by the line's own quantity. What you take is **reserved for that line**, and every figure counts it as done — the need, the progress bar, the plan and the close-the-order banner — so a line covered from the shelf asks for no prints at all.

The request is trimmed to what is actually there at the moment you save, and you are told when it was: a neighbouring order may have taken the last two while the dialog was open.

The reservation comes back on its own when the line is deleted, when its quantity drops below the reservation, when the order is cancelled, and when the order is deleted. Deleting an order does one thing more: its finished prints stop belonging anywhere, so they are credited back onto the shelf as order-less prints. Both movements are marked *the order was deleted* in the table.

Three things it deliberately does **not** do:

- a **completed** order gives none of that back — not when it is cancelled, not when one of its lines goes, not when the order itself is deleted, and its prints are not re-credited either: those kits went out inside the units the customer received, and the prints went with them. **One door stays open even then.** Typing a new **From stock** number on a completed order's line still releases the old reservation and takes the new one — that field is the operator correcting what the order took off the shelf, and refusing it would leave a mistake with nowhere to be fixed. The other three doors only dispose of paperwork and say nothing about the parts, which is why they stay shut.
- reopening a cancelled order does not re-reserve, because the shelf may have gone to somebody else in the meantime.
- a **duplicated** order reserves nothing, because a reorder must not quietly empty the shelf.

### The shelf on the product page

The product's **Stock** tab shows the free-parts shelf alongside finished-goods positions and movements: the kit count, a balance for every counted part — zeros included — and the journal with date, part, signed change, reason and note. The journal pages through older movements.

**Adjust** writes a correction as a movement with a note you must supply, never as a silent overwrite, and a correction that would take a part below zero is refused. In the catalog, a product card carries its kit count as a badge when there is anything on the shelf.

Deleting a part removes its ledger; **merging** two parts moves the movements onto the survivor, because a merge says the two were always the same thing. Deleting a product removes the ledgers of all its parts. Deleting a print leaves its movements alone and simply drops the reference — the parts are still on the shelf.

### The Stock section

**Projects → Stock** opens on **Finished goods**. Each stock position represents one product configuration, with its location, minimum, on-hand, reserved and available quantities. The list marks positions below their minimum. Open a position to see its reservations, other configurations and the parts its kit needs. Receive finished units, take stock, reserve them or issue them to a customer. **Assemble** uses free printed parts and adds finished units in one recorded movement.

**Free parts** shows the balance of each part, active order reservations and how many kits each configuration could make. A part with zero units per kit remains visible as *Out of kit*. The **Journal** pages through movements in both ledgers, with filters for product and operation.

An issue from an order or directly from stock creates a numbered **dispatch note**. Its recipient, units and waybill are recorded when the issue is made; the waybill can be edited later. Orders can receive finished printed units into stock and issue them in batches, so issuing some units does not close the rest of the order. Stock movements and corrections have separate permissions; see below.

---

## :material-shield-key: Permissions

The workshop has four sections — orders, products, customers and stock — and each has its own rights. Filing prints under orders is a right of its own.

| Permission | Covers |
|---|---|
| `orders:read` | Orders: the lists, the order page, its plan, forecast, journal, attachments and cover; the customer's name and the contact's name and role. |
| `orders:create` | Creating an order, duplicating one, an order from files. |
| `orders:update` | An order's fields, status, stage, lines, configuration, purchases, attachments and cover; defects recorded from the order; filing future work under it. |
| `orders:delete` | Deleting an order. |
| `orders:file_prints` | Filing any print — past or future, yours, someone else's, or one started from the printer's screen or a slicer — under an open order, moving it to another line, taking it out. It does not let you edit a print's photos, files or notes. |
| `products:read` | The catalog, the product page, its parts, variants, plates and files (as far as the library lets you see them), purchase prices, attachments, export. |
| `products:create` | Creating a product — from scratch, from a file, by import or by duplicating. |
| `products:update` | A product's card, parts, variants, categories, its links to library files and folders, attachments and cover. |
| `products:delete` | Deleting a product. |
| `customers:read` | The customer directory: contacts with phone, e-mail, city and delivery; notes. |
| `customers:create` | Creating a customer — also from the order form. |
| `customers:update` | Editing a customer and its contacts; the list of delivery methods. |
| `customers:delete` | Deleting a customer. |
| `stock:read` | Finished positions, the parts shelf, the journal, dispatch notes, the stock tiles. |
| `stock:move` | Moving goods: receipts, reservations, assembly, issues and dispatch notes, taking from stock into an order line, banking an order's surplus. |
| `stock:adjust` | Correcting the books: stocktakes, manual corrections, write-offs, counting an old print onto the shelf, a position's location and minimum. |

**Filing prints.** A past print is filed, moved to another line or taken out of an order by someone with `orders:file_prints`, or by someone who may edit orders (`orders:update`) and may edit that print (`archives:update_own` for your own, `archives:update_all` for any). Future work — the print dialog, the queue, a reprint, a queue job's clone, the plate's «Repeat», Telegram — needs `orders:file_prints` or `orders:update`; without either, a reprint or a clone goes without the order, and the button says so before anything is sent. Nothing new is filed under a closed order. A print whose output the order has taken into stock cannot leave it, and a print in the trash is not filed — restore it first; a batch with one such print moves nothing.

**From other sections.** Linking a library file or folder to products, unlinking it, and moving files when the move changes which products they belong to also need `products:update` (and the library's own rights). A file that lands in a folder linked to products — uploaded, sliced or unpacked from a ZIP — takes the folder's links without asking: the link is a rule its author set for the folder. Taking from stock needs `stock:move`; giving back what an order held when it is cancelled, completed or reduced needs no stock right. A delete asks for the rights of what it really changes: a customer with active orders also needs `orders:update`, a product with stock also `stock:adjust`.

**What you may not read stays empty.** A page of one section shows another section's fields only to someone who may read that section: without `customers:read` an order shows its contact without the phone; without `products:read` the purchase prices are «—». Filtering or sorting a list by a field you may not read is refused. A dispatch note shows the recipient's phone and address and the supplier's bank details only to someone with `customers:read` or `stock:move`; anyone else sees its number, date, order, customer, units and waybill.

For [API keys](api-keys.md#permission-model), the **Manage Projects** scope (`can_manage_projects`) carries every workshop write, filing prints and reading customers; reading orders, products and stock rides `can_read_status`. The scope is off on existing keys after an upgrade and is granted per key under **Settings → API Keys**.

**After the upgrade** every group can do what it did before: the old «Projects» rights become the matching rights of all four sections, and Administrators, Operators and Viewers get their default sets. A custom group that held *File prints under orders* without the right to edit orders does not keep it, and a user who had «edit» in one group and *File prints under orders* in another keeps only their own prints — the upgrade log names such groups. A status-only API key no longer reads customers.

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
