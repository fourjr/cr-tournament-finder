import asyncio
import logging
import os
import string
import sys

import aiohttp
import clashroyale
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


class Requester:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.client = clashroyale.RoyaleAPI(os.environ['api_token'], is_async=True, timeout=5, session=self.session)
        self.log = logging.getLogger('cr-tournament-finder')
        self.mongo = AsyncIOMotorClient(os.environ['mongo'])
        self.is_closed = False
        try:
            self.loop.run_until_complete(self.poll())
        except KeyboardInterrupt:
            self.is_closed = True
            self.close()

    def close(self):
        self.loop.stop()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    async def poll(self):
        print('Application INIT')
        while not self.is_closed:
            for l in string.ascii_lowercase:
                while not self.is_closed:
                    try:
                        tournaments = await self.client.search_tournaments(name=l)
                    except clashroyale.RequestError as e:
                        self.log.warning('{} occured. Waiting 1 minute before continuing.'.format(e))
                        await asyncio.sleep(60)
                        continue
                    else:
                        self.log.info('Searched "{}"'.format(l))
                        break
                    await asyncio.sleep(0.3)

                self.loop.create_task(self.parse_tournaments(tournaments))

    async def parse_tournaments(self, tournaments):
        """Parses the tournament payload and determines if anything is new"""
        if not isinstance(tournaments, list):
            tournaments = [tournaments]
        for t in tournaments:
            data = await self.mongo.tournaments.data.find_one({'tag': t.tag})
            if not data:
                # Data is new
                self.log.info('New tournament found: {}'.format(t.tag))
                await self.mongo.tournaments.data.insert_one({'tag': t.tag})
                self.loop.create_task(self.alert_webhook(t))

    async def alert_webhook(self, tournament):
        """Alerts all end developers with a POST"""
        async for w in self.mongo.tournaments.webhooks.find():
            # Types: all, 50, 100, 200, 1000, open:all, open:50, open:100, open:200, open:1000
            if w.get('authorization'):
                auth = {'Authorization': w.get('authorization')}
            else:
                auth = None

            types = w.get('filters', [])
            post = False
            filter_val = ['all', str(tournament.max_players)]

            if 'all' in types or tournament.max_players in types:
                # all
                # 50, 100, 200, 1000
                post = True

            if tournament.open:
                filter_val.append('open:all')
                filter_val.append('open:{}'.format(tournament.max_players))
                if 'open:all' in types or 'open:{}'.format(tournament.max_players) in types:
                    # open:all
                    # open:50, open:100, open:200, open:1000
                    post = True

            del tournament.raw_data['startTime']
            del tournament.raw_data['endTime']
            del tournament.raw_data['members']
            tournament.raw_data['filters'] = filter_val

            if post:
                async with self.session.post(w.get('url'), json=tournament.raw_data, headers=auth) as resp:
                    self.log.info('POSTed to {}: {}'.format(w.get('url'), resp.status))
            else:
                self.log.info('Skipped POSTing to {}'.format(w.get('url')))


if __name__ == '__main__':
    load_dotenv()
    logger = logging.getLogger('cr-tournament-finder')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
    Requester()
