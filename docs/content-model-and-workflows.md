# Content Model And Workflows

Generated from:

- `profiles/default/types/*.xml`
- `profiles/default/workflows.xml`
- `profiles/default/workflows/*/definition.xml`
- `profiles/default/rolemap.xml`
- `roles/localroles.py`

## Role Legend

- `CP`: `CounterPart`
- `LR`: `LeadReviewer`
- `MSA`: `MSAuthority`
- `MSE`: `MSExpert`
- `SE`: `SectorExpert`
- `Mgr`: `Manager`
- `SA`: `Site Administrator`
- `Own`: `Owner`
- `Anon`: `Anonymous`
- `ER`: `ExpertReviewer`

Notes:

- `Observation`, `Question`, `Comment`, `CommentAnswer`, and `Conclusions` derive local roles from the parent `Observation` via `roles/localroles.py`.
- Those local roles are computed from the current user, the observation country, and the sector/NFR mapping.
- `ReviewFolder` access is mainly driven by its own workflow state and globally assigned roles.
- `ER` appears in `esd-file-workflow`, but `sharing.xml` removes it from the sharing UI, so it looks stale.

## Content Type Graph

```mermaid
flowchart TD
    ReviewFolder["ReviewFolder\nworkflow: esd-reviewtool-folder-workflow"]
    Observation["Observation\nworkflow: esd-review-workflow"]
    Question["Question\nworkflow: esd-question-review-workflow"]
    Conclusions["Conclusions\nworkflow: esd-conclusion-workflow"]
    Comment["Comment\nworkflow: esd-comment-workflow"]
    CommentAnswer["CommentAnswer\nworkflow: esd-answer-workflow"]
    NECDFile["NECDFile\nworkflow: esd-file-workflow"]
    File["Plone File\nallowed in ReviewFolder"]

    ReviewFolder -->|contains| Observation
    ReviewFolder -->|contains| File
    Observation -->|contains| Question
    Observation -->|contains| Conclusions
    Question -->|contains| Comment
    Question -->|contains| CommentAnswer
    Comment -->|contains| NECDFile
    CommentAnswer -->|contains| NECDFile
    Conclusions -->|contains| NECDFile
```

## ReviewFolder Workflow

```mermaid
stateDiagram-v2
    [*] --> private
    private --> pending: submit [Request review]
    pending --> published: publish [Review portal content]
    pending --> private: reject [Review portal content]
    published --> private: retract [Request review]
    private --> ongoing_review: start [Mgr]
    ongoing_review --> published: end-review [Mgr]
```

| State | Visible to | Can modify | Add Observation |
|---|---|---|---|
| `private` | `Mgr`, `Own` | `Mgr`, `Own` | `Mgr` |
| `pending` | `Mgr`, `Own` | `Mgr` | `Mgr` |
| `ongoing-review` | `Anon`, `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `Own`, `SE` | `Own` | `Mgr`, `LR`, `SE` |
| `published` | `Anon` | `Mgr`, `Own` | `Mgr` |

## Observation Workflow

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> pending: open [Mgr|SE|LR]
    pending --> conclusions: draft-conclusions [SE|LR]
    pending --> conclusion_discussion: request-comments [SE]
    pending --> close_requested: finish-observation [SE]
    pending --> pending: reopen-qa-chat [SE]
    conclusion_discussion --> conclusions: finish-comments [SE]
    conclusions --> close_requested: finish-observation [SE]
    close_requested --> closed: confirm-finishing-observation [LR]
    close_requested --> close_requested: recall-lr [LR]
    close_requested --> conclusions: recall-se-conclusions [SE]
    close_requested --> conclusions_lr_denied: deny-finishing-observation [LR]
    conclusions_lr_denied --> close_requested: recall-lr [LR]
    conclusions_lr_denied --> conclusions_lr_denied: recall-se-conclusions-lr-denied [SE]
    closed --> close_requested: reopen-closed-observation [Mgr]
```

Actions with no state change:

- `recall-se` in `close-requested` by `SE`
- `edit-highlights` by `SE` or `LR`

| State | Visible to | Can modify | Key extra capabilities |
|---|---|---|---|
| `draft` | `LR`, `Mgr`, `SE` | `Mgr`, `SE` | `Add Question`: `Mgr`, `SE`; `Add Conclusions`: `SE`, `LR` |
| `pending` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `LR`, `Mgr`, `SE` | `Add Question`: `SE`; `Add Conclusions`: `SE`, `LR`; `View Comment Discussion`: `CP`, `LR`, `SE`; `View Answer Discussion`: `MSA`, `MSE` |
| `conclusions` | `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `SE`, `LR` | `Add Conclusions`: `SE`, `LR` |
| `conclusion-discussion` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `View Conclusion Discussion`: `CP`, `LR`, `Mgr`, `SE` |
| `close-requested` | `LR`, `MSA`, `Mgr`, `SE` | `LR`, `Mgr` | `View Conclusion Discussion`: `LR`, `Mgr`, `SE` |
| `conclusions-lr-denied` | `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `SE`, `LR` | `Add Conclusions`: `SE`, `LR` |
| `closed` | `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Add Question`: `Mgr` |

## Question Workflow

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> drafted: send-to-lr [SE]
    draft --> counterpart_comments: request-for-counterpart-comments [SE]
    drafted --> pending: approve-question [LR]
    drafted --> draft: redraft [LR]
    drafted --> recalled_lr: recall-question-lr [LR]
    recalled_lr --> draft: reopen
    pending --> expert_comments: assign-answerer [MSA]
    pending --> pending_answer_drafting: add-answer [MSA]
    pending --> recalled_msa: recall-msa [MSA]
    pending --> closed: validate-answer-msa [SE]
    pending --> closed: close [SE]
    pending --> closed: close-lr [LR]
    pending_answer_drafting --> answered: answer-to-lr [MSA]
    expert_comments --> pending_answer_drafting: ask-answer-aproval [MSA]
    answered --> closed: validate-answer-msa [SE]
    recalled_msa --> draft: recall-sre [SE]
    counterpart_comments --> draft: send-comments [SE]
    closed --> draft: add-followup-question [SE]
    pending --> pending: delete-answer [MSA]
    draft --> closed: delete-question [SE]
```

Actions with no state change:

- `finish-observation-lr` by `LR`
- `finish-observation-re` by `SE`
- `draft-conclusions` by `SE`
- `go-to-conclusions` by `SE`
- `eselect-msexperts` by `MSA`
- `reselect-counterparts` by `SE`

| State | Visible to | Can modify | Key extra capabilities |
|---|---|---|---|
| `draft` | `CP`, `LR`, `Mgr`, `SE` | `Mgr`, `SE` | `Add Comment`: `Mgr`, `SE`; `Edit Comment`: `Mgr`, `SE`; `Add CommentAnswer`: `Mgr`; `Edit CommentAnswer`: `Mgr`; `Add NECDFile`: `Mgr`, `SE` |
| `drafted` | `CP`, `LR`, `Mgr`, `SE` | `LR`, `Mgr` | `Edit Comment`: `LR`; `Add NECDFile`: `LR`; `View Comment Discussion`: `CP`, `LR`, `SE` |
| `pending` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Add Comment`: `Mgr`; `Add CommentAnswer`: `MSA`, `Mgr`; `Edit CommentAnswer`: `MSA`, `Mgr`; `Add NECDFile`: `MSA` |
| `pending-answer-drafting` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Edit CommentAnswer`: `MSA`; `Add NECDFile`: `MSA`, `Mgr`; `View Answer Discussion`: `MSA`, `MSE` |
| `answered` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `View Answer Discussion`: `MSA`, `MSE`; `View Comment Discussion`: `LR`, `SE` |
| `expert-comments` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Reply to item`: `MSA`, `MSE`; `View Answer Discussion`: `MSA`, `MSE` |
| `counterpart-comments` | `CP`, `LR`, `Mgr`, `SE` | `Mgr` | `Reply to item`: `CP`, `LR`, `SE`; `View Comment Discussion`: `CP`, `LR`, `SE` |
| `recalled-lr` | `CP`, `LR`, `Mgr`, `SE` | `Mgr` | `Edit Comment`: `LR`; `Add NECDFile`: `LR`; `View Comment Discussion`: `LR`, `SE` |
| `recalled-msa` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Edit CommentAnswer`: `MSA`, `MSE`, `Mgr`; `Add NECDFile`: `MSA`, `MSE`, `Mgr`; `View Answer Discussion`: `MSA`, `MSE` |
| `closed` | not explicitly mapped except `Add Comment` | not explicitly mapped | `Add Comment`: `Mgr`, `SE` |

## Conclusions Workflow

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> approval: ask-approval
    draft --> comments: request-comments
    approval --> published: publish
    approval --> draft: redraft
    comments --> published: publish
    comments --> draft: redraft
    comments --> approval: ask-approval
```

Notes:

- The transitions in `esd-conclusion-workflow` have no explicit `guard-role` or `guard-permission` in the workflow XML.
- Effective access is therefore mostly controlled by the state-level permission maps.

| State | Visible to | Can modify | Key extra capabilities |
|---|---|---|---|
| `draft` | `LR`, `Mgr`, `SE` | `Mgr`, `SE` | `Add NECDFile`: `Mgr`, `Own`, `SE`; `View Conclusion Discussion`: `LR`, `Mgr`, `SE` |
| `approval` | `LR`, `Mgr`, `SE` | `LR`, `Mgr` | `Add NECDFile`: `LR`, `Mgr`; `View Conclusion Discussion`: `LR`, `Mgr`, `SE` |
| `comments` | `CP`, `LR`, `Mgr`, `SE` | `Mgr` | `Reply to item`: `CP`, `LR`, `Mgr`, `SE`; `View Conclusion Discussion`: `CP`, `LR`, `Mgr`, `SE` |
| `published` | `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `View Conclusion Discussion`: `LR`, `Mgr`, `SE` |

## Comment And Answer Workflows

```mermaid
stateDiagram-v2
    state "Comment" as CommentWF {
        [*] --> initial
        initial --> public: publish [LR]
        public --> initial: retract [LR]
    }
    state "CommentAnswer" as AnswerWF {
        [*] --> initial
        initial --> public: publish [MSA|Mgr]
        public --> initial: retract [MSA|Mgr]
    }
```

| Workflow | State | Visible to | Can modify | Key extra capabilities |
|---|---|---|---|---|
| `Comment` | `initial` | `CP`, `LR`, `Mgr`, `SE` | none explicit | delete objects: `Mgr` |
| `Comment` | `public` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Edit Comment`: `Mgr`; `Add NECDFile`: `Mgr` |
| `CommentAnswer` | `initial` | `MSA`, `MSE`, `Mgr` | `MSA`, `Mgr` | delete: `MSA`, `Mgr`; `Add NECDFile`: `MSA`, `Mgr` |
| `CommentAnswer` | `public` | `CP`, `LR`, `MSA`, `MSE`, `Mgr`, `SE` | `Mgr` | `Edit CommentAnswer`: `Mgr`; `Add NECDFile`: `Mgr` |

## NECDFile Workflow

```mermaid
stateDiagram-v2
    [*] --> initial
    initial --> confidential: to_confidential [here/confidential]
    initial --> standard: to_standard [not here/confidential]
    confidential --> standard: mgr_standard [Mgr|SA]
    standard --> confidential: mgr_confidential [Mgr|SA]
```

| State | Visible to | Can modify |
|---|---|---|
| `confidential` | `LR`, `MSA`, `MSE`, `Mgr`, `SE`, `SA` | `Mgr`, `SA` |
| `standard` | `ER`, `LR`, `MSA`, `MSE`, `Mgr`, `SE`, `SA` | `Mgr`, `SA` |

## High-Level Access Pattern

- `ReviewFolder` opens the review to more roles only in `ongoing-review`.
- `Observation` starts as `SE`-driven work, opens to `MSA` and `MSE` in `pending`, and narrows again near closure.
- `Question` is the most role-sensitive workflow:
  - `SE` authors and routes questions.
  - `LR` approves/redrafts.
  - `MSA` drafts and submits answers.
  - `MSE` mainly participates through answer discussion visibility and reply rights in `expert-comments`.
  - `CP` participates in `counterpart-comments`.
- `Comment` and `CommentAnswer` visibility broadens after publication.
- `Conclusions` remain mostly `SE` and `LR` driven until `published`.
