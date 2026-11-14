# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all
operations. `gh` infers the repo from `git remote -v`.

## Conventions

- **Create**: `gh issue create --title "..." --body "..."`, heredoc for
  multi-line bodies. Issue titles are a plain description of the bug or job,
  not a conventional-commit line (that is for the PR).
- **Read**: `gh issue view <n> --comments`.
- **List**: `gh issue list --state open --label m1 --json number,title,labels`.
- **Comment**: `gh issue comment <n> --body "..."`.
- **Label**: `gh issue edit <n> --add-label "..."` / `--remove-label "..."`.
- **Close**: `gh issue close <n> --comment "..."`. A build issue is not closed
  on merge; it carries `pending-release` and closes in a batch when its
  release is tagged. Bugs and docs issues may close on merge.

## Issues are for bugs and team work items

The tracker holds reproducible bugs (the `bug.yml` form) and work items
created by the team (the `wayfinder.yml` form). Blank issues are disabled.

## Labels

`scripts/labels.sh` creates every label below. Run it again after editing it.

**Milestone**

- `demo`: the five-screen demo track, which runs ahead of the milestones.
- `m0` to `m7`: which milestone the work belongs to.

Every issue carries exactly one of these, and the matching milestone.

**Area** (set on pull requests by the labeler bot from the paths touched)

- `area:core`: the run manifest, the envelope, the stage contract.
- `area:sense`: targets and what holds a film together.
- `area:chassis`: parent enzymes and their provenance.
- `area:design`: variant generation, Tamarind Bio.
- `area:fold`: structure prediction, Boltz-2.
- `area:score`: stability and the integrity check.
- `area:rank`: ranking and the trade-off front.
- `area:explain`: the scientist agent.
- `area:web`: Sonazyme Lab and the API.
- `area:bio`: the biology docs.
- `targets`: target files and the target schema.
- `retrodiction`: retrodiction cases and reference data.
- `adr`: the issue needs or updates an ADR.
- `documentation`: docs only.

**Wayfinder**

- `wayfinder:map`: the single map issue for a milestone.
- `wayfinder:research`: an investigation. Output is an ADR recommendation.
- `wayfinder:prototype`: a throwaway spike a human judges.
- `wayfinder:grilling`: pressure-test a decision before it is locked.
- `wayfinder:task`: build work.
- `ready-for-agent`: the spec is settled; an implementation agent may build it.

**Priority** (bugs carry one)

- `p1`: serious. A passing retrodiction case now fails, or a number is shown
  with no manifest entry behind it.
- `p2`: an ordinary defect.
- `p3`: minor.

**Triage state**

- `needs-repro`: plausible but not yet reproduced.
- `needs-decision`: blocked on a design decision.
- `needs-research`: blocked on a research ticket, including a missing source.
- `regression`: worked in an earlier tagged release.
- `pending-release`: merged; closes when its release is tagged.

## Wayfinder

The **map** is one issue labelled `wayfinder:map`, holding three sections in
its body: Notes, Decisions so far, and Fog (what is still unknown).

**Child tickets** are GitHub sub-issues of the map, each labelled
`wayfinder:<type>` and its milestone label.

**Blocking** uses GitHub's native issue dependencies. Add an edge with
`gh api --method POST repos/Nabzx/sonazyme/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`,
where the blocker db id comes from
`gh api repos/Nabzx/sonazyme/issues/<n> --jq .id`.

**Frontier**: the map's open child tickets with no open blocker. Work them in
map order. The demo map's frontier comes first.
