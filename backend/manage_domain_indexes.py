"""Print proposed index names by default. --apply explicitly creates indexes."""
import argparse
import asyncio
import json
from pymongo.errors import PyMongoError
from core.database import load_backend_environment, DatabaseSettings, create_database_client
from core.domain_indexes import domain_index_specs, ensure_domain_indexes


async def main(apply):
    if not apply:
        print(json.dumps({name: [dict(index.document) for index in indexes] for name, indexes in domain_index_specs().items()}, default=dict, indent=2))
        return
    load_backend_environment()
    client = create_database_client(DatabaseSettings.from_environment())
    try:
        result = await ensure_domain_indexes(client[DatabaseSettings.from_environment().database_name])
        print(json.dumps({'created_or_verified': result}, indent=2))
    except PyMongoError:
        raise SystemExit('Index provisioning failed. Check database connectivity/permissions; no raw details exposed.')
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    asyncio.run(main(parser.parse_args().apply))
