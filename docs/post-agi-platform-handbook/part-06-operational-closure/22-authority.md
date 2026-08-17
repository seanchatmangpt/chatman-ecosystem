# 22. Authority Without Ambient Privilege

A post-AGI system should be designed under the assumption that raw intelligence will become extremely capable. Safety therefore cannot depend on the model being unable to imagine a consequential operation.

The system must distinguish capability from authority.

\[
Capability(x,a) \not\Rightarrow Authority(x,a)
\]

## Credentials are capabilities

A credential makes an operation technically possible. It does not answer whether the operation is permitted for the current subject and purpose.

This is a subtle but essential distinction because conventional automation frequently encodes authority as possession of secrets.

The post-AGI architecture instead treats credentials as execution capabilities consumed only after an explicit authority decision.

## No privileged artifact classes

Neither model output nor formal proof receives ambient authority.

A signed plan can still be unauthorized. A theorem can still describe a forbidden operation. A valid Terraform plan can still target the wrong account. A successful test suite can still correspond to the wrong commit.

Authority is its own edge in the graph.

## Authority as reachability

Let the graph contain principals, subjects, capabilities, brokers, policies, and consequential transitions. A lawful DO path must include the required authority edges.

Security can then ask whether an untrusted node can reach a forbidden consequence.

This provides a stronger architectural target than hoping every generated instruction is benign.

## Delegation is explicit

A2A systems make delegation central. One intelligence may ask another to perform a capability, but delegation must preserve the authority scope.

The delegate cannot gain a broader subject, longer lifetime, or stronger consequence class merely because it has more technical capability.

Receipts should preserve the delegation chain.

## Authority expires

Long-lived ambient authorization increases the reachable attack surface. Where possible, operational authority should be subject-specific, purpose-specific, time-bounded, and consumable.

This does not require humans in every loop. It requires an explicit law governing when the machine may advance.

## Falsifier

A system violates this chapter if possession of a connector, API token, cluster role, or deployment key is treated as sufficient justification for the operation using it.

## Operational exercise

Pick one automation credential. List every operation the credential technically allows. Then list the smaller set the automation is actually authorized to perform. If the runtime cannot enforce the difference, the authority model is weaker than the credential model.