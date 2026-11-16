import asyncio
import logging
from dataclasses import replace
from datetime import timedelta

from pymongo.errors import PyMongoError
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError

from mission_orchestration.plan import CANCEL_SIGNAL, TERMINAL_STATUSES, WORKFLOW_TYPE, MissionRef


logger = logging.getLogger(__name__)
RPC_TIMEOUT = timedelta(seconds=10)


class MissionDispatcher:
    def __init__(self, store, client, task_queue):
        self.store = store
        self.client = client
        self.task_queue = task_queue

    async def dispatch_one(self):
        command = await self.store.claim_command()
        if command is None:
            return False
        mission = MissionRef(command['organization_id'], command['mission_id'])
        try:
            document = await self.store.get_mission(mission)
            if document['status'] not in TERMINAL_STATUSES:
                if command['type'] == 'start_mission':
                    if document.get('orchestration', {}).get('workflow_id') != mission.workflow_id:
                        await self.start_workflow(replace(mission, mission_type=document['mission_type']))
                else:
                    handle = self.client.get_workflow_handle(mission.workflow_id)
                    await handle.signal(CANCEL_SIGNAL, rpc_timeout=RPC_TIMEOUT)
        except RPCError as exc:
            await self.store.defer_command(command, exc.status.name)
        except ValueError:
            await self.store.defer_command(command, 'mission_unavailable')
        else:
            await self.store.deliver_command(command, mission.workflow_id)
        return True

    async def start_workflow(self, mission):
        try:
            await self.client.start_workflow(
                WORKFLOW_TYPE, mission, id=mission.workflow_id, task_queue=self.task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE, rpc_timeout=RPC_TIMEOUT,
            )
        except WorkflowAlreadyStartedError:
            # The previous attempt may have started the workflow before losing the lease.
            pass

    async def run(self):
        while True:
            try:
                if await self.dispatch_one():
                    continue
            except PyMongoError:
                logger.warning('Mission dispatcher could not reach MongoDB. Retrying.')
            await asyncio.sleep(1)
