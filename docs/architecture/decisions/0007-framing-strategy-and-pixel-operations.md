# ADR 0007: Separate framing strategy from pixel operations

## Status

Accepted

## Context

PiPrints needs consistent output aspect ratios while keeping image-processing
components independently testable. Choosing which region to retain is a policy
decision, whereas cropping and resizing are pixel transformations. Combining
these responsibilities would make it harder to add a different framing policy
without duplicating image manipulation.

## Decision

`CenterCropAspectRatioStrategy` calculates a PiPrints-owned `CropBox` from
source dimensions and a target `AspectRatio`; it does not manipulate pixels.
`CropOperation` applies an explicit crop box, and `ResizeOperation` changes the
resulting dimensions. Callers compose crop before resize in `PhotoPipeline`.
Layouts continue to compose already processed photos and do not decide framing.

## Consequences

The first center-crop policy is deterministic and can be tested without Pillow
image operations. Future framing policies can produce the same `CropBox`
contract without changing pixel operations. Cropping at source resolution
discards unwanted pixels before scaling, avoiding unnecessary resize work. The
pipeline remains generic and has no layout or aspect-ratio knowledge.
