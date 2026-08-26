# Verification package boundary fix

The verification package already defined `VerificationReport` but did not
export it at the package boundary. The sandbox package similarly already had
the concrete execution result type but did not expose the name expected by
current callers.

Both package boundaries now export the existing concrete types. No duplicate
verification or sandbox result models were added.
