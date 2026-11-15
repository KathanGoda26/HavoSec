import argparse
import asyncio
import logging
import os
from datetime import timedelta

from temporalio.client import Client
from temporalio.worker import Worker

from core.database import DatabaseSettings, create_database_client, load_backend_environment
from mission_orchestration.activities import MissionActivities
from mission_orchestration.dispatcher import MissionDispatcher
from mission_orchestration.storage import OrchestrationStore
from mission_orchestration.workflow import RepositoryAssessment


async def run(process):
    load_backend_environment()
    settings = DatabaseSettings.from_environment()
    db_client = create_database_client(settings)
    try:
        store = OrchestrationStore(db_client[settings.database_name])
        await store.check_indexes()
        client = await Client.connect(
            os.environ.get('TEMPORAL_ADDRESS', '127.0.0.1:7233'),
            namespace=os.environ.get('TEMPORAL_NAMESPACE', 'default'),
        )
        queue = os.environ.get('TEMPORAL_MISSION_TASK_QUEUE', 'havosec-missions-v1')
        if process == 'dispatcher':
            await MissionDispatcher(store, client, queue).run()
        else:
            activities = MissionActivities(store)
            await Worker(
                client, task_queue=queue, workflows=[RepositoryAssessment],
                activities=[activities.acquire_mission_slot, activities.project_mission_progress,
                            activities.run_mission_fixture],
                max_concurrent_activities=16, graceful_shutdown_timeout=timedelta(seconds=5),
            ).run()
    finally:
        db_client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('process', choices=['dispatcher', 'worker'])
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    asyncio.run(run(parser.parse_args().process))
