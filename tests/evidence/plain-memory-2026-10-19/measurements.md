# Measurements (UTF-8 bytes, taken on ORIGINAL unsanitized files)

Caps: whole file 4,096; sections Identity and state 800, Boundaries and blockers 600, Next action 500, Resume reading 600, Evidence and working changes 1000, Do not redo 596

## run1 checkpoint (pre-resume, recovered from transcript Write)
total 3078 bytes, sha256 5cdc80d7b26a21bd14afe5f84427c3a599255255f81e816e89fcdd781954f2c9
- Identity and state: 582
- Boundaries and blockers: 515
- Next action: 287
- Resume reading: 524
- Evidence and working changes: 669
- Do not redo: 501

## after fresh session (rewritten by fresh session)
total 3437 bytes, sha256 e96191bcc2e6f332d2c4e28ef77340777f51f24c03cab4572313e86ccf29aa72
- Identity and state: 642
- Boundaries and blockers: 588
- Next action: 259
- Resume reading: 549
- Evidence and working changes: 905
- Do not redo: 494

## run2 repeat (same path)
total 3391 bytes, sha256 7282e81c94f21235b60a5c7285d2f9f23c3f7397c5d7bf34efe31533fac7f092
- Identity and state: 642
- Boundaries and blockers: 542
- Next action: 259
- Resume reading: 549
- Evidence and working changes: 905
- Do not redo: 494

## run3 collision -2
total 3593 bytes, sha256 156f7477ba149e28987be60fedd81a4c2f87f58c50c7df40e7a7caa4993b5c18
- Identity and state: 642
- Boundaries and blockers: 608  OVER CAP by 8
- Next action: 259
- Resume reading: 549
- Evidence and working changes: 1059  OVER CAP by 59
- Do not redo: 476

## run3 original (tampered copy, must be untouched by run3)
total 3304 bytes, sha256 37e1ee401641c16f952f66df0d5f709e1a4ae0f7564900c380ad9a1570e40d9c
- Identity and state: 555
- Boundaries and blockers: 542
- Next action: 259
- Resume reading: 549
- Evidence and working changes: 905
- Do not redo: 494

## run1 resume line
247 bytes, 243 chars (over the 200-char target; reported as an exception by the run)
