# v26.9.1 portfolio survey design

The portfolio survey is an observation/projection capability for the composition root.

It enforces four separations:

- portfolio membership is not release admission;
- release role is not constitutional role;
- ref drift is not standing promotion;
- observation/report generation is not consequential DO.

`release/v26.9.1/manifest.toml` remains the admitted release graph. `release/v26.9.1/constitutional-role-crosswalk.toml` gives every release role an explicit constitutional projection. `scripts/survey_portfolio.py` observes GitHub, resolves current refs, inventories core PR/issue WIP, and emits CSV/JSON/Markdown projections plus SHA-256 checksums.

The workflow is read-only. It has no repository write permission and no BRCE/DO authority. A newer SHA is reported as drift and retains the manifest standing attached to the admitted SHA; it is never promoted automatically.

Generated survey files are evidence projections only and are uploaded as workflow artifacts. They do not outrank the manifest, owning repository verifiers, or exact-subject execution receipts.

The fleet observation count is no longer a source-code constant. `verify_portfolio.py` checks that the admitted observed count is mathematically consistent with the admitted pagination evidence. A future repository-count change therefore requires a new observation, not a code edit to a historical literal.
