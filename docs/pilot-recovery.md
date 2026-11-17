# Pilot data recovery rehearsal

The **Mission integration** job runs a MongoDB backup and restore rehearsal after the public Tile_Studio pilot mission finishes. It uses the job's temporary MongoDB replica set, with a random source database and a separate random restore database. Its backup stays in memory and neither database is reused after the job.

The rehearsal verifies the mission status and scan report through the same API routes used by Mission Control. It also compares the approval, action audit, and outbox records with the source and checks that the restored mission indexes exist. A second organization must receive a 404 when requesting the restored report or actions. The job logs the time for this small fixture and fails if the restore or any check fails.

## Recovery checklist for a pilot environment

1. Pause new missions and stop the dispatchers and workers for the environment being recovered. Keep the original database and backup available while you investigate.
2. Restore MongoDB into a separate, access-controlled environment. Confirm mission status, reports, approval and action records, and indexes. Test access with an account from a different organization before exposing the restored API to users.
3. Reconcile restored outbox records with Temporal history before enabling dispatch. Record any unresolved mission or publication outcome for review. Check an uncertain publication against the expected GitHub branch and pull request before retrying.
4. Record the backup timestamp, recovery duration, and missing records or artifacts. Set pilot backup retention and recovery targets based on the hosted environment and a representative rehearsal.

This CI check covers MongoDB data at a point when the test mission has finished. Temporal history, externally stored artifacts, ongoing writes, and managed database backups need separate recovery checks before a live pilot.
