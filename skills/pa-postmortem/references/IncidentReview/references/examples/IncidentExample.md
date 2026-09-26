# Incident Review Example

## Summary

An application deploy introduced a configuration mismatch that caused elevated 500s for 18 minutes before rollback.

## Impact

Roughly 22% of requests failed during the window.

## Timeline

1. Deploy started at 14:02.
2. Error rate increased at 14:05.
3. Rollback completed at 14:20.

## Root Cause

The new deploy assumed an environment variable existed in production, but the value had only been configured in staging.

## Contributing Factors

- Missing deployment validation for required production configuration
- Alerting fired after the error threshold was already sustained

## Detection and Response

On-call detected the spike from error-rate alerts and rolled back after confirming correlation with the deploy.

## Fixes Applied

- Rolled back the deploy
- Added startup validation for required environment variables

## Follow-up Actions

- Add deployment checks for required production config
- Shorten alert evaluation for this error class
