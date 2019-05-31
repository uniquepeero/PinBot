import requests
import json
import configparser
import logging
import os
from time import sleep


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", 'w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

class Pinnacle:
	AUTH = ''
	URL = 'https://api.pinnacle.com'
	def __init__(self):
		config = configparser.ConfigParser()
		if os.path.isfile('config.ini'):
			config.read('config.ini')
			try:
				self.AUTH = config['Pinnacle']['KEY']
			except Exception as e:
				log.error(f'[Pinnacle] "KEY" constant with auth key not found: {e}' )
		else:
			log.error('config.ini file not found')

	def lines_sports(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		try:
			res = requests.get(f'{self.URL}/v2/sports', headers=headers)
			if res.status_code == requests.codes.ok:
				log.debug(f'Lines Sports:\n{res.json()}')
				return res.json()
			else:
				log.error(f'Lines Sports request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get Lines Sports: ', exc_info=True)

	def find_sport_tennis(self, sports_list):
		for index in sports_list['sports']:
			if index['name'] == 'Tennis':
				return index['id']

	def lines_fixtures(self, sportId, since=None):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/fixtures?sportId={sportId}{since}', headers=headers)
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Lines Fixtures request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get Lines Fixtures: ', exc_info=True)

	def lines_odds(self, sportId, since=None, eventIds=None):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		if eventIds is None:
			events = ''
		else:
			# Сюда добавить список
			events = f'&eventIds={eventIds}'
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/odds?sportId={sportId}&oddsFormat=Decimal{events}{since}', headers=headers)
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Lines Parlay Odds request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.critical(f'Get Lines Parlay Odds: ', exc_info=True)

	def client_balance(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		try:
			res = requests.get(f'{self.URL}/v1/client/balance', headers=headers)
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Client balance request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get client balance: ', exc_info=True)

if __name__ == '__main__':
	try:
		log.info('Started')
		pin = Pinnacle()
		tennis = 33
		firstline = pin.lines_fixtures(tennis)
		last = firstline['last']
		alexline = {
			'id1': {
				'p1': 'Sloane Stephens',
				'p2': 'Polona Hercog',
				'p1_odds': 1.2,
				'p2_odds': 3.8,
				'isfound': False
			},
			'id2': {
				'p1': 'Belinda Bencic',
				'p2': 'Donna Vekic',
				'p1_odds': 1.8,
				'p2_odds': 2.1,
				'isfound': False
			}
		}
		for key, value in alexline.items():
			log.debug(f'AL Key: {key}')
			log.debug(f'AL Value: {value}')
			if value['p1'] and value['p2'] in firstline.items():
				log.info(f'FOUND {value["p1"]} and {value["p2"]} in firstline')


		line = pin.lines_fixtures(tennis)
		odds = pin.lines_odds(tennis)

	except Exception:
		log.error(f'Main got: ', exc_info=True)
	finally:
		log.info('Closed')