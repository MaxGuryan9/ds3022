# The Vanishing Dataset

## The Case

Sometime last night, a dataset disappeared from the department server.
Five people had badge access to the server room that night. Someone's
lying about where they were — and the case file itself has a couple of
errors that will throw you off if you're not careful.

Work the case using nothing but SQL — `CREATE`, `INSERT`, `SELECT`,
`UPDATE`, and `DELETE` — against the case database (`suspects`,
`access_logs`, `alibis`). Load the starting database
(`vanishing_dataset.db`, built from `setup.sql`) in DuckDB and work
through the steps below **in order**. Each step depends on the one
before it.

Write down every query you run. Not every lead in this case is real —
you'll need to explain, in your own words, why you ruled out any dead
ends. Your query log and your reasoning both get turned in.

---

### Step 1 — Open the case (CREATE + INSERT)

Create a table called `case_log` with three columns: `case_log_id`
(integer), `note` (text), and `logged_at` (text). Insert one row: your
name and today's date as the note.

---

### Step 2 — Look at the suspects (READ)

Query the full `suspects` table. One row shouldn't be there at all —
someone on this list no longer has legitimate reason to hold a badge.
Identify who, and why.

---

### Step 3 — Clear the red herring (DELETE)

Remove that person's row from `suspects`, and remove their row(s) from
`access_logs`. Their badge should never have scanned that night.

---

### Step 4 — Build the floor directory (CREATE + INSERT)

Pinned to the case board is this directory of terminal locations:

| Terminal | Floor | Department |
|---|---|---|
| A | 2 | Data Engineering |
| B | 3 | Server Room |
| C | 3 | Server Room |
| D | 1 | Lobby |

Create a table called `terminal_map` with columns `terminal`, `floor`,
and `department`, and insert all four rows above.

---

### Step 5 — Place everyone (READ + JOIN)

Write a query that joins `access_logs` to `terminal_map` and returns,
for every remaining badge swipe, the suspect's `suspect_id`, the
`login_time`, and the `floor`/`department` where that swipe happened.
You'll want this picture in front of you for the rest of the case.

---

### Step 6 — A second look at the logs (READ + GROUP BY)

Write a query against `access_logs` that counts how many times each
`suspect_id` appears, and returns only suspects who show up **more than
once**. One name comes back. On its own, does this prove anything?

---

### Step 7 — Rule it in or out (READ + INSERT)

A witness recalls this suspect stopping by briefly around 10:50pm to
drop off a bag before going out to dinner, then returning later that
night to actually work. Look at both of their badge swipes and decide
whether that explanation is consistent with the times on record.

Insert a row into `case_log` documenting your conclusion (something
like: `'Suspect 1005's early swipe is explained — not a lead.'`).

---

### Step 8 — The maintenance window (READ)

Building security confirms one hard fact: **the badge readers were
offline for maintenance from 11:00pm to 11:15pm** on the night in
question. Any swipe logged inside that window could not have actually
happened.

Query `access_logs` for any swipe that falls inside that window. Unlike
Step 6, this one *does* prove something. Who does it catch, and why is
this different from the false lead in Step 6–7?

---

### Step 9 — Verify the alibis that hold up (UPDATE)

In `alibis`, every row starts at `verified = 0`. Update the rows for
every remaining suspect **except** the one you caught in Step 8, setting
`verified = 1`. Leave the liar's row alone.

---

### Step 10 — Fix the corrupted order (READ + UPDATE)

Each verified alibi holds a `clue_fragment`, and the `sequence` column
says what order the fragments belong in — but two of the values got
swapped in the case file.

For each verified suspect, find the badge swipe that actually matches
the time stated in their alibi (careful — one suspect has two swipes on
record, and only one of them is the one their alibi refers to). Use
those matching times, earliest to latest, to work out the correct
order, then `UPDATE` the two `sequence` values that are wrong.

---

### Step 11 — Name the culprit (READ + JOIN)

Write a query joining `suspects` and `alibis` that returns the `name`
and `badge_code` of the suspect whose alibi is still `verified = 0`.
That's your culprit.

---

### Step 12 — Crack the vault (READ + string functions + aggregate)

Two things stand between you and the missing dataset:

**a) The location.** Write a query that returns the `clue_fragment`
values for every verified suspect, ordered correctly by `sequence`. Read
them in order.

**b) The lock code.** The vault code is built from two pieces:

- the three digits in the culprit's `badge_code` (use a string function
  to pull them out — don't just retype them by hand)
- followed by the total number of suspects whose alibi you verified as
  true (a single-number count, from a query — not a guess)

Concatenate those two pieces into one code.

---

## Turn in:

1. Every query you ran, in order, including Step 7's reasoning note.
2. A sentence explaining why Step 6 was a false lead but Step 8 wasn't.
3. The name of the culprit.
4. The final location phrase.
5. The final vault code.
