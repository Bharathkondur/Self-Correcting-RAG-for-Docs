# Security policy

Please report suspected vulnerabilities privately through GitHub's security advisory feature rather than
opening a public issue. Include reproduction steps, affected endpoints, and potential impact.

The application treats uploaded documents as untrusted input, but no prompt-injection defence is complete.
Do not use the demo to process secrets or regulated data without adding authentication, durable tenant
isolation, malware scanning, encrypted storage, audit logging, and an organisation-specific threat model.

Only the latest `main` branch is supported for security fixes.

