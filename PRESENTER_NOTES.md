# Presenter notes

## Opening: the story (about 45 seconds)

> Imagine you are on call for an online checkout service. Around one in four
> operations is failing or delayed. The logs show “token expired” and intermittent
> 502 errors. The team recently rotated credentials, so a credential problem is
> an obvious first hypothesis.
>
> We give an agent the same tools an engineer would use: the ticket, logs, metrics,
> and troubleshooting guides. Its job is to gather evidence and propose a fix.
> Along the way, Switchyard decides whether each model step should use the
> efficient model or the more capable model.
>
> Can routing produce a well-supported diagnosis at lower cost than always using
> the capable model?

Pause and ask: **“What evidence would you check before rotating the credentials again?”**
Do not reveal the answer until the investigation has run.

## Reveal: the clock is wrong (about 30 seconds)

> The same token succeeds on another validator, and it still has 40 minutes of
> validity according to trusted time. Only the blue worker group is failing.
> Its clock is an hour fast, so it thinks a valid token has already expired.
>
> The proposed fix is to synchronize the affected workers' clocks, then verify
> token validation and service recovery. The recent credential rotation was a
> misleading clue.

Evidence in the synthetic INC-004 fixture:

| Evidence | What it establishes |
|---|---|
| L1 | The token's issuer and signature are valid, despite the expiry error. |
| L2 | An independent validator accepts it; trusted time shows 40 minutes left. |
| L3 | Blue fails while green accepts the same credential. |
| M1 | Blue is +3,600 seconds; green is +0.2 seconds; credential refresh succeeds. |

“502” is the ticket's accompanying symptom; the decisive evidence points to clock
skew. Avoid inventing a separate network cause that the fixtures do not establish.

## Explain the routing (about 30 seconds)

> The judge estimates whether the efficient model can handle the current task and
> evidence. Switchyard compares that estimate with a threshold and chooses a model.
> Each chosen model can call tools or submit a diagnosis. The final report is checked
> by Python rules, separately from the routing judge.

Describe the actual model choices shown on screen. Do not promise that the capable
model always starts or that a particular step always uses one model. A healthy router
can choose one model throughout. Zero router issues means the judgments were usable;
it does not prove those judgments were accurate.

## Close with the comparison

Read three things in order: **reports passed → total cost → elapsed time**.

> “Here is what happened on this incident at these illustrative prices. Judge calls
> count toward both cost and time. A cheaper answer only helps if it retains the
> evidence and quality we need.”

Use a savings number only when measured in your own live or clearly labelled recorded
comparison. Rehearsal is scripted and supports no quality, cost, or speed claims.
Two similar runs on one synthetic incident do not establish production reliability.

## Before presenting

- Run setup before the audience arrives and collapse code cells.
- Choose `INC-004` for this story. Other incidents have different causes.
- Keep a saved live comparison ready. `REPLAY_PATH` replays only the comparison;
  skip the live investigation cell if you want a fully recorded presentation.
- The optional final cell reprices existing usage or opens full diagnostic details.
- Use several cases and repeats before drawing broader conclusions. Temperature zero
  can reduce variation; it does not guarantee identical results or correct judgments.
