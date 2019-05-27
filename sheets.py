import gspread
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs.log", encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

def main():
	log.info('Started')
	try:
		scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
		creds = ServiceAccountCredentials.from_json_keyfile_name('secret.json', scope)
		client = gspread.authorize(creds)
		sheet = client.open('Pinn Line').sheet1
		log.info('Successfuly connected to Google Sheet')
	except:
		log.error('GSheets connect error: ', exc_info=True)

	sleep(2)
	alex_line = {}
	while True:
		sleep(2)
		allvalues = sheet.get_all_values()
		if len(allvalues) > 1:
			for index, item in enumerate(allvalues[1:]):
				if item[0] > 5 and item[1] > 5 and item[2] > 2 and item[3] > 2:
					event = f'{item[0]} - {item[1]}'
					if event not in alex_line:
						alex_line[event] = {
							'p1': item[0],
							'p2': item[1],
							'p1_odds': item[2],
							'p2_odds': item[3],
							'isFound': False}
						log.info(f'Got new event row: "{event}"')
						log.info(f'Alex Line Dict:\n{alex_line}')

		elif len(allvalues) < 0:
			log.warning('Got fully empty sheet')

# TODO

main()