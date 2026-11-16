# Run mission orchestration locally

Phase 2 runs a fixture assessment. Temporal schedules the tasks and MongoDB stores the progress shown in Mission Control. The existing Security Runs worker continues to handle its own queue.

From the backend directory, install the dependencies and provision the indexes on a MongoDB replica set:

```powershell
python -m pip install -r requirements.txt -r requirements-missions.txt
python manage_domain_indexes.py --apply
```

Start a Temporal development server with `temporal server start-dev`. Run each process in its own terminal from the backend directory:

```powershell
python -m mission_orchestration worker
python -m mission_orchestration dispatcher

Set `MONGO_URL` and `DB_NAME` to the same database used by the API. Both orchestration processes default to Temporal at `127.0.0.1:7233`, namespace `default`, and task queue `havosec-missions-v1`. To override these defaults, set `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, and `TEMPORAL_MISSION_TASK_QUEUE` consistently on both processes. Each organization can run one fixture mission at a time.

To run the integration checks, set `MISSION_TEST_MONGO_URL` to an isolated MongoDB replica set and `MISSION_TEST_TEMPORAL_ADDRESS` to a Temporal development server:

```powershell
python -m pytest -q tests/test_mission_orchestration.py
```

The tests use a temporary database and unique Temporal workflow IDs. The Temporal test simulates a dispatcher interruption before delivery is recorded, restarts the worker during activity retry, and checks cancellation and retry limits.

## Governed fixture execution

The worker checks the mission, organization, requester, project, repository asset, and current task before admitting each fixture attempt. New missions capture the asset scope when they are created. Older Phase 2 missions bind their scope once when first admitted by the gateway. The fixture adapter returns fixed outputs and does not fetch a repository, read files, or start tools.

The organization document in `client_companies` may set `mission_policy.fixture` to `allow`, `deny`, or `require_approval`. The default allows the synthetic fixture. Unknown values deny execution. A mission waiting for approval keeps its organization slot, checks again every ten seconds, and moves to `needs_review` after thirty minutes if it cannot proceed.

Organization administrators can review, approve, and revoke fixture actions in Mission Control. The same controls are available through the API. `GET /api/missions/{mission_id}/actions` lists fixture actions with their policy decisions, approvals, attempts, and recorded results. To approve an action whose decision is `require_approval`, send its `digest` as `{"action_digest":"…"}` to `POST /api/missions/{mission_id}/actions/{task_id}/approve`. To revoke it, send the same body to `POST /api/missions/{mission_id}/actions/{task_id}/approvals/{approval_id}/revoke`. An approval expires after fifteen minutes and authorizes only the action it was granted for. An eligible retry reuses the same logical action, and a recorded result is returned without executing the adapter again. Policy decisions and approval grants and revocations are recorded in `mission_execution_events`.
