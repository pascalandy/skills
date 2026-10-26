# Harbor departure screens show "No departures"

Posted in #passenger-info-ops, Wednesday 2026-10-14. All times UTC.

**Ines Varga, station manager, Harbor (08:02):**

> All four departure screens on the Harbor concourse say "No departures", and they have since about 08:00. Trains are running normally and platform staff are calling them out by hand. The website still lists the Harbor trains when I search for Harbor, so it is only the screens. Passengers keep asking at the desk. Can someone look?

**Teo Brandvold, on call for departures-api (08:09):**

> Looking. The change this morning is departures-api 3.4, deployed at 07:55. It added a response cache for departures, keyed by stop and minute. No rollback yet: I want to know why before we touch anything.
