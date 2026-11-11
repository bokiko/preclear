# Review brief: rerun-2026-11-11-claude-sonnet-5-5

This brief is built from the filed files of one dated evidence folder. Every number in it is quoted from those files, and every line that starts with `> ` is quoted text. The harness has judged nothing.

## What to return

Give one line for each row and layout listed under Rows and layouts below. Each line names a conclusion in a few words and gives the reason. When a row cannot be judged from the files named in its quoted lines, write a plain statement saying so for that row instead of a conclusion. Add no score and no summary of the whole folder.

## Folder

- folder: rerun-2026-11-11-claude-sonnet-5-5
- model: claude-sonnet-5-5
- Claude Code build: 2.1.310
- Run state: complete
- row 7 review table of the committed triple folder: rerun-2026-11-09-claude-sonnet-5-5-triple (its row7-review.md)
- row 7 review table of this folder: none is filed in this folder

## Digest table

> # Digest table, part 1
> This part lists every row folder present in this dated folder at the moment it was written. The latest part is the complete one; earlier parts are never edited. Costs are quoted as the usage files hold them.
> rows: 21
> | Folder | State | Attempt | Reason | Skill sha256 | Adapter sha256 | Stub sha256 | Wrapper sha256 | Cost (USD) |
> | --- | --- | --- | --- | --- | --- | --- | --- | --- |
> | plain-memory | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.220019500000000006 |
> | hub-memory | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.25914469999999998 |
> | bound-ledger | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.4243717999999999 |
> | row1-wrong-binding | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.26818169999999996 |
> | row2-double-conflict | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.42735889999999993 |
> | row3a-missing-executable | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.226219 |
> | row3b-denied-helper-write | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.3148145 |
> | row3c-unbound-fallback-none | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.187976 |
> | row4a-unknown-backend | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.2280918 |
> | row4b-conflicting-blocks | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | 96791fa6f223da0a78836cebd5a340d926954834eb17e76476afea6f25233a0c | 3d43613ee253e7e5cda7a8bb344a771e31542c0aa9f29653498cbec918b97851 | 0.22885509999999998 |
> | row5a-no-memory | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.1652819 |
> | row5b-disabled-memory | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.19547949999999997 |
> | row6-readonly-plan | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.1982779 |
> | row7-all-destinations-denied | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.22240689999999998 |
> | row8a-non-git | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.26456339999999999 |
> | row8b-detached-head | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.27237849999999999 |
> | row8c-unborn-branch | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.256106500000000004 |
> | row9-linked-worktree | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.2608693 |
> | row10-large-status | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.36691180000000001 |
> | row11-concurrent-change | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.28388210000000003 |
> | row12-frozen-handoff | filed | 1 | - | 86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06 | eca134a3defce9f67f7ed05a60b7da32d589df5f5cdaacbbf97682c5ebdbe132 | UNCONFIRMED | UNCONFIRMED | 0.47550190000000004 |
> total: 5.746692699999999770 USD from 21 cost value(s); 0 UNCONFIRMED

## Rows and layouts

### plain-memory (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2618/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 9324af7b-da8d-4a06-80a0-ad439c1109bd, s2 9324af7b-da8d-4a06-80a0-ad439c1109bd, s3 3c77c0dc-d3df-4f68-bf56-c341673190e7 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0527334 and 5 turns, s2 cost 0.12074100000000001 and 11 turns, s3 cost 0.046545100000000006 and 3 turns (source: usage.txt)

### hub-memory (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2834/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s2 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s3 574434b4-5f11-4d71-8408-660a74e0709b (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.057078 and 5 turns, s2 cost 0.15339049999999999 and 17 turns, s3 cost 0.0486762 and 3 turns (source: usage.txt)

### bound-ledger (filed)

> - [ ] helper calls (all stages): attempted 11, executed 11, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: no (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
> - [ ] session ids per stage: s1 db7c801d-3030-4285-954a-3e1d4fa28a40, s2 db7c801d-3030-4285-954a-3e1d4fa28a40, s3 3f6cc69f-b9bc-4d3a-861d-19c81858eeea (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0536723 and 5 turns, s2 cost 0.3158604 and 33 turns, s3 cost 0.0548391 and 3 turns (source: usage.txt)

### row1-wrong-binding (filed)

> - [ ] helper calls (all stages): attempted 2, executed 2, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2665/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 84a440b8-9fe2-4ce3-a3dd-40323967aeb1, s2 84a440b8-9fe2-4ce3-a3dd-40323967aeb1, s3 acf1f513-79b8-4ad6-8ff2-2330aef1062e (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.055681999999999995 and 5 turns, s2 cost 0.15498 and 14 turns, s3 cost 0.0575197 and 6 turns (source: usage.txt)

### row2-double-conflict (filed)

> - [ ] helper calls (all stages): attempted 8, executed 7, denied 0, compound refusals 1 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: no (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2769/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 a62931a8-0694-4737-920d-e8e9aa32f026, s2 a62931a8-0694-4737-920d-e8e9aa32f026 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0563066 and 5 turns, s2 cost 0.37105229999999995 and 38 turns (source: usage.txt)

### row3a-missing-executable (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2727/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 03a7a675-8bf0-46ef-a2f0-058e08bd7eee, s2 03a7a675-8bf0-46ef-a2f0-058e08bd7eee (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0532885 and 5 turns, s2 cost 0.17293050000000001 and 21 turns (source: usage.txt)

### row3b-denied-helper-write (filed)

> - [ ] helper calls (all stages): attempted 5, executed 3, denied 1, compound refusals 1 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2644/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 81360632-924c-40b5-857c-78195ace9e54, s2 81360632-924c-40b5-857c-78195ace9e54 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.05333989999999999 and 5 turns, s2 cost 0.2614746 and 27 turns (source: usage.txt)

### row3c-unbound-fallback-none (filed)

> - [ ] helper calls (all stages): attempted 2, executed 1, denied 0, compound refusals 1 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
> - [ ] session ids per stage: s1 2cce4477-7eb5-4b29-bb1a-0ecf2426233c, s2 2cce4477-7eb5-4b29-bb1a-0ecf2426233c (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0535509 and 5 turns, s2 cost 0.13442510000000002 and 10 turns (source: usage.txt)

### row4a-unknown-backend (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2834/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 3f99f947-f802-49e5-8095-81f4a4cfe813, s2 3f99f947-f802-49e5-8095-81f4a4cfe813 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.05551120000000001 and 5 turns, s2 cost 0.1725806 and 16 turns (source: usage.txt)

### row4b-conflicting-blocks (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
> - [ ] session ids per stage: s1 632b7b51-4b07-44d0-9e9c-6c0d0646814e, s2 632b7b51-4b07-44d0-9e9c-6c0d0646814e (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.057496599999999995 and 5 turns, s2 cost 0.1713585 and 9 turns (source: usage.txt)

### row5a-no-memory (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2476/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc, s2 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0447066 and 4 turns, s2 cost 0.1205753 and 10 turns (source: usage.txt)

### row5b-disabled-memory (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2692/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 d2f780c6-6079-4e02-bb55-003dfd31b863, s2 d2f780c6-6079-4e02-bb55-003dfd31b863 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0416388 and 4 turns, s2 cost 0.1538407 and 16 turns (source: usage.txt)

### row6-readonly-plan (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2724/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 f43fe444-2783-4b09-9774-bbda070d6560, s2 f43fe444-2783-4b09-9774-bbda070d6560 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.047196 and 4 turns, s2 cost 0.15108190000000002 and 15 turns (source: usage.txt)

### row7-all-destinations-denied (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
> - [ ] session ids per stage: s1 bf313c82-a6c4-43de-9326-3c7f2c47f7a3, s2 bf313c82-a6c4-43de-9326-3c7f2c47f7a3, s3 10062b61-00cb-48d4-8e2a-1118c0a63520 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.047807499999999996 and 4 turns, s2 cost 0.11986020000000001 and 11 turns, s3 cost 0.0547392 and 4 turns (source: usage.txt)

### row8a-non-git (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2830/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 fe615e8c-42e7-4326-9890-b2a64ef5d23d, s2 fe615e8c-42e7-4326-9890-b2a64ef5d23d, s3 08552d61-2128-4162-98a5-087076871cdf (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.04387099999999999 and 4 turns, s2 cost 0.16562359999999998 and 17 turns, s3 cost 0.05506880000000001 and 7 turns (source: usage.txt)

### row8b-detached-head (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2571/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 2b542a48-2e28-40e9-962d-4e7679c94bb7, s2 2b542a48-2e28-40e9-962d-4e7679c94bb7, s3 84ef8bc3-5376-43ca-9299-68f58d75b4c8 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.04762999999999999 and 4 turns, s2 cost 0.1426712 and 14 turns, s3 cost 0.08207729999999999 and 6 turns (source: usage.txt)

### row8c-unborn-branch (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2679/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 52fa3032-6149-423a-a0d5-7ff597f1d0bb, s2 52fa3032-6149-423a-a0d5-7ff597f1d0bb, s3 e1128fe7-d1f5-404b-898c-82c554cf24ba (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0467351 and 4 turns, s2 cost 0.15344609999999997 and 17 turns, s3 cost 0.055925300000000004 and 8 turns (source: usage.txt)

### row9-linked-worktree (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2779/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 59e6c9eb-7cb7-43b4-90a4-d13595b5bf99, s2 59e6c9eb-7cb7-43b4-90a4-d13595b5bf99, s3 01644d7a-af31-4e8d-8468-115f18357829 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.046497300000000005 and 4 turns, s2 cost 0.15877019999999997 and 17 turns, s3 cost 0.0556018 and 7 turns (source: usage.txt)

### row10-large-status (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2919/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 360ff92c-5213-4b02-bea0-88537c3ea862, s2 360ff92c-5213-4b02-bea0-88537c3ea862, s3 9648808c-c38c-4432-b0ee-6b9fd07e0e41 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0490269 and 5 turns, s2 cost 0.24821100000000004 and 21 turns, s3 cost 0.06967390000000001 and 6 turns (source: usage.txt)
> - [ ] expected outcome, quoted-porcelain fallback and NUL redirect refused: quoted form executed 2, NUL form executed with a redirection 0, NUL form denied with a redirection 1, NUL form executed without a redirection 1, sidecar status.txt present, 1367 bytes, 0 NUL bytes (source: mechanical-checks.md Row 10 status form, the /preclear full trace, snap-2-after-preclear/preclear)

### row11-concurrent-change (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 2791/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39, s2 e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39, s3 63413984-fd7a-4e95-ab68-4f22a7aca3b6 (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.0514867 and 5 turns, s2 cost 0.176541 and 18 turns, s3 cost 0.0558544 and 5 turns (source: usage.txt)

### row12-frozen-handoff (filed)

> - [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md, s4-preclear-refresh-full-trace.md)
> - [ ] ledger digests unchanged, setup to snap-4-after-refresh: yes (source: snap-0-setup/sha.txt, snap-4-after-refresh/sha.txt)
> - [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md, s4-preclear-refresh-full-trace.md)
> - [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
> - [ ] checkpoint bytes versus cap: 3239/4096 (source: measurements.txt)
> - [ ] session ids per stage: s1 36ffc8c3-bb43-4a3f-87ca-00de30e41ca9, s2 36ffc8c3-bb43-4a3f-87ca-00de30e41ca9, s3 fcd43228-5751-47dd-b25a-d3d479ce37ef, s4 fcd43228-5751-47dd-b25a-d3d479ce37ef (source: session.id, session-resume.id, usage.txt)
> - [ ] cost and turns per stage: s1 cost 0.048074200000000004 and 4 turns, s2 cost 0.2166703 and 21 turns, s3 cost 0.06726470000000001 and 5 turns, s4 cost 0.14349269999999997 and 13 turns (source: usage.txt)
