# 5. Rice’s Theorem and the Semantic Boundary

**Executive thesis:** Rice’s theorem does not make software hopeless; it tells us where a general semantic decision procedure cannot exist and therefore where architecture must change the question.

## The precise boundary

For arbitrary programs, nontrivial semantic properties are undecidable in general. The theorem does not say that every useful property of every bounded artifact is undecidable, and it does not say testing is useless. It says there is no universal algorithm that can accept arbitrary program text and decide every nontrivial property of its behavior.

## Why authorship is irrelevant

The theorem does not care whether the program was written by a staff engineer, a contractor, an LLM, or an AGI. Once the organization makes arbitrary implementation the object from which it expects general semantic certainty, it inherits the same boundary. More intelligence can improve many cases without becoming a universal decider.

## The ggen sidestep

ggen does not defeat Rice. It sidesteps the Rice-bound question by restricting the object of judgment. Admission retracts raw observations into a bounded formal sublanguage where declared constraints can be checked. Manufacture then projects from that admitted object. Undecidability is fenced rather than abolished.

## Operating practice

When a review question takes the form “does this arbitrary code really mean what we intended?”, ask whether the intended property can be made explicit upstream. Prefer decidable admission predicates, bounded formal kernels, structural constraints, independent witnesses, and exact replay over claims of omniscient understanding.

## Diagnostic question

Which important claim still depends on recovering arbitrary semantics from arbitrary code?
