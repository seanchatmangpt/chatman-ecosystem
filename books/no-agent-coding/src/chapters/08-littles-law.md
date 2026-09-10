# 8. Little’s Law and Semantic WIP

**Executive thesis:** When candidate generation accelerates faster than semantic closure, WIP grows even if every local agent looks productive.

## The flow equation

Little’s Law, L = λW, gives a simple lens: inventory equals throughput times time in system. In software, inventory is not only tickets. It includes branches, candidate patches, unresolved decisions, partial proofs, approval queues, contradictory docs, generated artifacts awaiting admission, and work that is “done” only according to the producer.

## Candidate throughput is not closure throughput

AI can increase λ_candidate dramatically while λ_admitted remains bounded by integration, evidence, authority, and real-world verification. That creates a semantic queue. The organization experiences more motion, more review, more merge conflict, and more false completion without proportional increase in standing.

## Compile the recurring queue

The post-agent response is not simply faster review. Repeated adjudication should become a reusable rule. Interpret novelty once, compile the resulting law, and execute known instances without renewed interpretation. That reduces arrivals into the adjudication queue rather than merely increasing service speed.

## Operating practice

Measure WIP by semantic closure class, not by repository count. Separate represented demand, eligible demand, selected work, admitted work, active work, and terminal work. Represent broadly, admit narrowly, and finish what is admitted before widening the active frontier.

## Diagnostic question

What is your actual admitted WIP, and how much candidate inventory sits ahead of it?
