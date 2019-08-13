import requests
import json
import configparser
import logging
import os
import gspread
import datetime
from time import sleep
#from pprint import pformat
#from fuzzywuzzy import fuzz
from math import log as LOG
from oauth2client.service_account import ServiceAccountCredentials


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", 'w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)


class Sheets:
	sheet = None

	def __init__(self):
		try:
			log.info('Connecting to Google Sheets...')
			self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			self.creds = ServiceAccountCredentials.from_json_keyfile_name('secret.json', self.scope)
			self.client = gspread.authorize(self.creds)
			self.sheet = self.client.open('Pinn Line').sheet1
			log.info('Successfuly connected to Google Sheet')
		except:
			log.error('GSheets connect error: ', exc_info=True)

	def getvalues(self):
		if self.creds.access_token_expired: self.client.login()
		if self.sheet:
			allvalues = self.sheet.get_all_values()
			if len(allvalues) > 1:
				eventslist = []
				for event in alexline:
					eventslist.append(event['event'])

				for index, item in enumerate(allvalues[1:]):
					if item[0] and len(item[0]) > 3 and item[1] and len(item[1]) > 3 and \
						item[2] and len(item[2]) > 0 and item[3] and len(item[3]) > 0 and \
						item[4] and len(item[4]) > 0 and item[5] and len(item[5]) > 0:

						if f'{item[0]} - {item[1]}' not in eventslist:
							if item[2] != '-':
								team = 'home' if '1' in item[2] else 'away'
								moneyline = {'team': team}
							else:
								moneyline = None

							if item[3] != '-':
								team = 'home' if item[3][0] == '1' else 'away'
								value = item[3][2:]
								handicap1 = {'team': team,
								             'value': value}
							else:
								handicap1 = None

							if item[4] != '-':
								team = 'home' if item[4][0] == '1' else 'away'
								value = item[4][2:]
								handicap2 = {'team': team,
								             'value': value}
							else:
								handicap2 = None

							if item[5] != '-':
								dirrection = 'over' if item[5][0].lower() == 'o' else 'under'
								value = float(item[5][2:])
								total = {'dirrection': dirrection,
								         'value': value}
							else:
								total = None

							alexline.append({
								'event': f'{item[0]} - {item[1]}',
								'p1': item[0],
								'p2': item[1],
								'moneyline': moneyline,
								'handicap1': handicap1,
								'handicap2': handicap2,
								'total': total,
								'isfound': False,
								'bet': {
									'moneyline': False,
									'handicap1': False,
									'handicap2': False,
									'total': False
								}
							})
							log.debug(f'Got new event row: "{item[0]} - {item[1]}"')
			
			elif len(allvalues) < 1:
				log.warning('Got fully empty sheet')


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
		proxies = {
			'http': self.proxydict['main'],
			'https': self.proxydict['main']
		}
		if since is None:
			since = ''
		else:
			since = f'&since={since}'
		try:
			res = requests.get(f'{self.URL}/v1/fixtures?sportId={sportId}{since}', headers=headers)
			if res.status_code == requests.codes.ok:
				if res and len(res.content) > 0:
					return res.json()
				else:
					return None
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
			url = f'{self.URL}/v1/odds?sportId={sportId}&oddsFormat=Decimal&toCurrencyCode={balancedict["currency"]}{events}{since}'
			res = requests.get(url, headers=headers)
			if res.status_code == requests.codes.ok:
				if res and len(res.content) > 0:
					return res.json()
				else:
					return None
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
			res = requests.get(f'{self.URL}/v1/client/balance', headers=headers)
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
					if event['liveStatus'] != 1:
						for alexevent in predict:
							if not alexevent['isfound']:
								if (event['home'] == alexevent['p1']) and (event['away'] == alexevent['p2']):
									alexevent['isfound'] = True
									alexevent['league'] = league['name']
									alexevent['league_id'] = league['id']
									alexevent['id'] = event['id']
									log.debug(f'FOUND!\nID: {event["id"]}\nLeague: {league["name"]}\nPlayers: {event["home"]} - {event["away"]}\n{predict}')


	def check_odds(self, predict, odds):
		if odds:
			for league in odds['leagues']:
				for event in predict:
					if event['isfound'] and event['league_id'] == league['id']:
						for event_odds in league['events']:
							if event_odds['id'] == event['id']:
								for period in event_odds['periods']:
									if period['number'] == 0 in period.keys():
										event['lineid'] = period['lineId']

										if event['moneyline'] and 'moneyline' in period.keys():
											event['moneyline']['odds'] = period['moneyline'][event['moneyline']['team']]

											self.placebet(balancedict['bank'], event['moneyline']['odds'], event['league_id'], event['lineid'], event['id'], 'MONEYLINE', event['moneyline']['team'])

										if 'spreads' in period.keys():
											event['favorite'] = 'home' if period['spreads'][0]['hdp'][0] == '-' else 'away'
											for handicap in ['handicap1', 'handicap2']:
												if event[handicap]:
													if event[handicap]['team'] != event['favorite']:
														event[handicap]['fvalue'] = float(event[handicap]['value'].replace('-', '') if '-' in event[handicap]['value'] else '-' + event[handicap]['value'])
														for hdp in period['spreads']:
															if hdp['hdp'] == event['handicap1']['fvalue']:
																event[handicap]['odds'] = hdp[event[handicap]['team']]
																if 'altLineId' in hdp.keys():
																	event[handicap]['altlineid'] = hdp['altLineId']
																else:
																	event[handicap]['altlineid'] = None
																self.placebet(balancedict['bank'], event[handicap]['odds'], event['league_id'], event['lineid'], event['id'], 'SPREAD', event[handicap]['team'], event[handicap]['altlineid'])

										if 'totals' in period.keys():
											for total in period['totals']:
												if total['points'] == event['total']['value']:
													event['total']['odds'] = total[event['total']['dirrection']]
													if 'altLineId' in total.keys():
														event['total']['altlineid'] = total['altLineId']
													else:
														event['total']['altlineid'] = None
													self.placebet(balancedict['bank'], event['total']['odds'], event['league_id'], event['lineid'], event['id'], 'TOTAL_POINTS', None, event['total']['altlineid'], event['total']['dirrection'].upper())



	def placebet(self, bank, odds, leagueid, lineid, eventid, bettype, team, altlineid=None, side=None):
		teams = {
			'home': 'Team1',
			'away': 'Team2'
		}
		try:
			if self.gethometeam()[leagueid] != 'Team1': teams['home'], teams['away'] = teams['away'], teams['home']
		except Exception:
			log.error('Get home team value in placebet(): ', exc_info=True)

		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		payload = {
			"oddsFormat": "DECIMAL",
			"acceptBetterLine": True,
			"stake": float(self.stakeamount(bank, odds)),
			"winRiskStake": "RISK",
			"lineId": lineid,
			"altLineId": altlineid,
			"fillType": "NORMAL",
			"sportId": TENNIS,
			"eventId": eventid,
			"periodNumber": 0,
			"betType": bettype,
			"team": teams[team],
			"side": side
		}
		try:
			res = requests.post(f'{self.URL}/v2/bets/straight', headers=headers, data=json.dumps(payload))
			if res.status_code == requests.codes.ok:
				return res.json()
			else:
				log.error(f'Lines Parlay Odds request: Code {res.status_code} / {res.json()}')
				return None
		except Exception:
			log.critical(f'Get Lines Parlay Odds: ', exc_info=True)


	def stakeamount(self, bank, odds):
		return round((bank * LOG(1 - (1 / (odds / (1 + 0.04))), 10 ** -40)), 1)


	def gethometeam(self):
		headers = {
			'Accept': 'application/json',
			'Authorization': self.AUTH
		}
		try:
			res = requests.get(f'{self.URL}/v2/leagues', headers=headers)
			if res.status_code == requests.codes.ok:
				r = res.json()
				d = {}
				for league in r['leagues']:
					d[league['id']] = league['homeTeamType']
				return d
			else:
				log.error(f'Get Leagues(hometeam): Code {res.status_code} / {res.json()}')
				return None
		except Exception:
			log.critical(f'Get leagues: ', exc_info=True)



if __name__ == '__main__':
	try:
		log.info('Started')
		alexline = []
		sheet = Sheets()
		pin = Pinnacle()
		TENNIS = 33
		last = last_odds = None
		currTime = checkTime = balancetimecheck = datetime.datetime.now()
		while True:
			# Присваивание банка на день в 6:00 UTC
			if currTime >= balancetimecheck:
				balancetimecheck.replace(hour=6, minute=00)
				balancetimecheck += datetime.timedelta(days=1)
				balance = pin.client_balance()
				balancedict = {'bank': balance['availableBalance'], 'currency': balance['currency']}

			log.debug('Getting values from Sheets...')
			sheet.getvalues()
			log.debug(f'Done. Values: {alexline}')
			deltaTime = currTime - checkTime
			if deltaTime.seconds > 61:
				last = last_odds = None
				checkTime = datetime.datetime.now()
			log.debug(f'Getting line since {last}...')
			line = pin.lines_fixtures(TENNIS, last)
			log.debug(f'Done. Fixtures:\n{line}')
			currTime = datetime.datetime.now()

			if line:
				last = line['last']
				log.debug('Checking exists...')
				pin.check_exists(alexline, line)
				log.debug('Done.')
			log.debug(f'Getting odds since {last_odds}...')
			odds = pin.lines_odds(TENNIS, last_odds)
			log.debug(f'Done. Odds:\n{odds}')

			if odds:
				last_odds = odds['last']
				log.debug('Checking Odds...')
				pin.check_odds(alexline, odds)
				log.debug('Done.')
			log.debug('Sleep for 5 secs')
			sleep(5)


	except Exception:
		log.error(f'Main got: ', exc_info=True)
	finally:
		log.info('Closed')


#TODO Просмотреть и сверить отчет odds. Какие там period number, везде ли 0.
#TODO Присваивать кэфы для нужных событий (if event['moneyline'] and 'moneyline' in period.keys() and ВОЗМОЖНО not  event['bet']['moneyline']
# Нашли все кэфы - вызываем функцию проставления. В ней дописать сохранение размера ставки
# Если есть parentid - сохранять его (Fixtures). Если есть altline в нужных hdp/points в ответе с odds - сохранять их