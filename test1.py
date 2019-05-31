import configparser
import json
import glob
import os
import datetime
import dateparser



def DoCheck(dir, rls, r):
	now = datetime.datetime.now()

	ok = False

	rules = json.loads(rls)
	if not isinstance(rules['file'], list):
		flist = [rules['file']]
	else:
		flist = rules['file']

	for f in flist:	

		files = glob.glob(os.path.join(dir, f))

		for file in files:
			ok = False
			if now - datetime.datetime.fromtimestamp(os.path.getmtime(file)) < now - dateparser.parse(rules['time']):
				ok = True
				if rules['rule'] == 'some':
					break

			if rules['rule'] == 'all':
				r.write("{0}\n".format(json.dumps({"file":file, "ok":ok, "rule":rules['time'], "size":str(os.stat(file).st_size), "date":str(datetime.datetime.fromtimestamp(os.path.getmtime(file)))})))
				print "{0}\n".format(json.dumps({"file":file, "ok":ok, "rule":rules['time'], "size":str(os.stat(file).st_size), "date":str(datetime.datetime.fromtimestamp(os.path.getmtime(file)))}))

		if rules['rule'] == 'some':
			r.write("{0}\n".format(json.dumps({"file":os.path.join(dir, f), "ok":ok, "rule":rules['time']})))
			print "{0}\n".format(json.dumps({"file":os.path.join(dir, f), "ok":ok, "rule":rules['time']}))


def start():
	config = configparser.ConfigParser()
	config.read('example.ini')

	directories = []

	for directory in config['dirs']:
		if len(config['dirs'][directory].splitlines()) > 1:
			directories.append((directory, config['dirs'][directory].splitlines()))
		else:
			directories.append((directory, config['dirs'][directory]))


	f = open("results.txt", "w")

	for directory, values in directories:
		if isinstance(values, list):		
			for value in values:
				DoCheck(directory, value, f)
		else:
			DoCheck(directory, values, f)


	f.close()

if __name__ == "__main__":
    start()
		


