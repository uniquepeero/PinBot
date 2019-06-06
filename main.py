import requests
import json
import configparser
import logging
import os
from time import sleep
from pprint import pformat
from fuzzywuzzy import fuzz
from math import log as LOG


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", 'w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

class Pinnacle:
	AUTH = ''
	URL = 'https://api.pinnacle.com'
	proxydict = {}
	def __init__(self):
		config = configparser.ConfigParser()
		if os.path.isfile('config.ini'):
			config.read('config.ini')
			try:
				self.AUTH = config['Pinnacle']['KEY']
			except Exception as e:
				log.error(f'[Pinnacle] "KEY" constant with auth key not found: {e}' )
			try:
				self.proxydict['main'] = config['Proxy']['Main']
			except Exception as e:
				log.error(f'Proxy not found: {e}')
		else:
			log.error('config.ini file not found')

	def lines_sports(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		try:
			res = requests.get(f'{self.URL}/v2/sports', headers=headers, proxies=proxies)
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
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/fixtures?sportId={sportId}{since}', headers=headers, proxies=proxies)
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
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		if eventIds is None:
			events = ''
		else:
			# Сюда добавить список
			events = f'&eventIds=[{eventIds}]'
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/odds?sportId={sportId}&oddsFormat=Decimal{events}{since}', headers=headers, proxies=proxies)
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
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		try:
			res = requests.get(f'{self.URL}/v1/client/balance', headers=headers, proxies=proxies)
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Client balance request: Code {res.status_code} / {res.json()}')
		except Exception:
			log.error(f'Get client balance: ', exc_info=True)

	def check_exists(self, predict, current):
		if current:
			for league in current['league']:
				for event in league['events']:
					for alexevent in predict:
						c_h = event['home']
						c_a = event['away']
						p_1 = alexevent['p1']
						p_2 = alexevent['p2']

						if (fuzz.token_sort_ratio(c_h, p_1) > 69 or fuzz.token_sort_ratio(c_a, p_1) > 69) and \
							(fuzz.token_sort_ratio(c_h, p_2) > 69 or fuzz.token_sort_ratio(c_a, p_2) > 69) and \
							('1.5 Sets' not in c_h and '2.5 Sets' not in c_h): # Убрать это позже и добавить возможность по сетам
							if fuzz.token_sort_ratio(c_h, p_1) < 70:
								alexevent['p1'] = c_h
								alexevent['p2'] = c_a
								alexevent['p1_odds'], alexevent['p2_odds'] = alexevent['p2_odds'], alexevent['p1_odds']
							alexevent['isfound'] = True
							alexevent['league'] = league['name']
							alexevent['league_id'] = league['id']
							alexevent['id'] = event['id']
							log.debug(f'FOUND!\nID: {event["id"]}\nLeague: {league_name}\nPlayers: {event["home"]} - {event["away"]}\n{predict}')

	def check_odds(self, predict, odds):
		if odds:
			for league in odds['leagues']:
				for event in predict:
					if event['isfound'] and event['league_id'] == league['id']:
						for event_odds in league['events']:
							if event_odds['id'] == event['id']:
								for period in event_odds['periods']:
									if period['number'] == 0 and 'moneyline' in period.keys(): # ПРОВЕРИТЬ NUMBER == 0
										if 'home_found' not in event['odds'].keys():
											event['odds']['home_found'] = period['moneyline']['home']
											event['odds']['away_found'] = period['moneyline']['away']
											log.debug(f'Found odds: {event}')
										event['odds']['home'] = period['moneyline']['home']
										event['odds']['away'] = period['moneyline']['away']
										if period['moneyline']['home'] - event['odds']['home'] >= 0.01:
											event['odds']['value'] = True
											event['odds']['valueplayer'] = 'home'
											log.debug(f'Found value {event}')
										if period['moneyline']['away'] - event['odds']['away'] >= 0.01:
											event['odds']['value'] = True
											event['odds']['valueplayer'] = 'away'
											log.debug(f'Found value {event}')
										if 'spreads' in period.keys():
											hdp = period['spreads'][0]['hdp']
											if (hdp < 0 and hdp <= 2.0) or (hdp > 0 and hdp >= 2.0):
												event['hdp_dict'] = period['spreads'][0]
												log.debug(f'Found Handicap in:\n{event}')


	def placebet(self):
		pass

	def stakeamount(self, bank, odds):
		return round((bank * LOG(1 - (1 / (odds / (1 + 0.04))), 10 ** -40)), 1)



if __name__ == '__main__':
	try:
		log.info('Started')
		pin = Pinnacle()
		tennis = 33
		firstline = pin.lines_fixtures(tennis)
		log.debug(f'First line: {pformat(firstline)}')
		last = firstline['last']
		alexline = [
			{
				'p1': 'Katerina Siniakova',
				'p2': 'Madison Keys',
				'p1_odds': 2.05,
				'p2_odds': 1.8,
				'isfound': False
			},
			{
				'p1': 'Belinda Bencic',
				'p2': 'Donna Vekic',
				'p1_odds': 1.8,
				'p2_odds': 2.1,
				'isfound': False
			}
		]

		sleep(5)
		line = pin.lines_fixtures(tennis, last)
		log.debug(f'Line with LAST: {pformat(line)}')
		sleep(5)
		odds = pin.lines_odds(tennis, 754643274)
		log.debug(f'Odds: {pformat(odds)}')

		pin.check_exists(alexline, firstline)


	except Exception:
		log.error(f'Main got: ', exc_info=True)
	finally:
		log.info('Closed')