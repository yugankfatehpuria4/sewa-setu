# Loom script — reply to the Deputy Commissioner (≤ 3 min)

> Before recording: transcribe the briefing (`scripts/transcribe_briefing.sh`) and replace the bracketed line in 0:20 with the DC's own complaints and timestamps.

**0:00–0:20** — Namaste, sir. I'm Rishabh, the Digital Fellow on Sewa Setu. You asked me to find out why citizens are struggling with the pension portal and fix what matters most.

**0:20–0:50** — I went through six months of server logs — one and a half million visits. Three numbers stand out. Two in every five people who reached the final Submit button got an error page — almost fourteen thousand attempts. Less than half the people who reached the document upload got past it. And since the fifteenth of March, the nightly job that grants deemed approval under the RTPS Act has crashed every single night. [Your complaints about … match this.]

**0:50–2:10** — My five fixes, most harmful first.
1. *Submission.* The server held a database line open while drawing a heavy receipt, so at busy times it ran out. Applications were often saved, but citizens were told they failed — and on retry, told they were duplicates. Now the receipt can never break a submission, and a retry shows their application number. *(Demo: submit a test application → confirmation.)*
2. *Upload.* The page said JPG or PDF up to 5 MB; the system accepted only PDFs under 100 KB, with the message "ERR_VAL_47". A phone photo of a voter ID now works, and errors say what to do. *(Demo: upload a JPG.)*
3. *Deemed approval.* A March configuration change broke the job. It runs again, in IST. Note: its first run will approve the backlog since March, as the Act requires.
4. *Privacy.* Any logged-in citizen could open anyone's record, including bank details — and could even press "approve". Citizens now see only their own; only officers can decide. *(Demo: try another ID → not found.)*
5. *Names and birth dates.* Hindi names were cut to a few letters, and 5 March was saved as 3 May. New records are now stored exactly. *(Demo: Hindi name on the status page.)*

**2:10–2:40** — What I did not touch: eligibility, the 15-day rule, and the deadline — those are your decisions. In particular, the scheme deadline in the system is tonight; if the window should stay open, that is a one-line setting I can apply on your instruction. I also did not edit any old record: names already cut short can't be recovered from the database, so I recommend the block offices verify flagged records against the age proof.

**2:40–3:00** — Remaining risks: the status password is still the date of birth, and there is no rate limiting yet. My next step would be safer citizen login and a load test before the next month-end. Thank you.

**Fallbacks:** if a live step fails, show the matching test in `tests/` and its before/after output in `docs/evidence/`.
