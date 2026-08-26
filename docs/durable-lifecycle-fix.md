# Durable verification lifecycle fix

The durable verification fixture previously moved a job directly from
SCANNING to VERIFYING. The authoritative state graph requires the canonical
lifecycle:

QUEUED -> SCANNING -> ANALYZING -> PATCHING -> VERIFYING -> VERIFIED.

The fixture now traverses that lifecycle explicitly. Production transition
rules were not weakened.
