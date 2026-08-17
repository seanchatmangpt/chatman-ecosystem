# Appendix G — GymAct World Specification

A minimal world specification should define:

1. ontology and object classes;
2. initial state generator;
3. observation function;
4. available action classes;
5. action preconditions;
6. transition function;
7. refusal/failure states;
8. resource and cost model;
9. termination conditions;
10. evidence emitted by each transition;
11. correspondence assumptions linking the gym to the claimed real-world class.

## Two observation modes

A strong benchmark often provides both:

- **full modeled state**, for upper-bound planning experiments; and
- **bounded observation**, for realistic AutoFDE/agent evaluation.

Do not mix the scores without naming the information regime.

## Safety rule

Gym execution is CONSTRUCT/experimental execution. Promotion to real DO always requires independent operational admission.