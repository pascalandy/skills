# Decompose

Use this method when a proposed solution, requirement, or limitation may contain inherited assumptions disguised as necessities.

## Method

1. State the function or outcome being protected before examining the current form
2. Break the claim, system, or requirement into independently testable parts
3. Classify each claimed constraint by source

| Constraint class | Test |
|---|---|
| Physical or empirical | Reality or observed behavior imposes it |
| Legal or contractual | A binding rule or commitment imposes it |
| Interface or system | Another component depends on it |
| Resource | Time, money, people, capacity, or information limits it |
| Policy | An authority chose it and can revise it |
| Convention | Existing practice favors it but does not require it |
| Preference | A stakeholder values it |
| Assumption | It is being treated as true without enough support |

4. Record the evidence, owner, reversibility, and cost of violating or changing each constraint
5. Challenge only the classifications that affect the solution space
6. Reconstruct the smallest approach that satisfies the hard constraints and the intended function
7. Compare the reconstruction with the inherited form and name the assumption that created the largest difference

Analogy is evidence about a possible pattern, not proof. Law, contracts, public interfaces, and deliberate human commitments can be hard constraints in practice even though they are not laws of physics.

## Completion criterion

Finish when every decision-relevant limitation has a source, evidence level, and reversibility, and the resulting solution no longer depends on an unexamined assumption.
