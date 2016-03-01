'''
python cron monitor
It tracks each user's cron entries and removes entries older than 30 days
Written by Waff Jason
'''

import subprocess
import re
import sqlite3
import os.path

# the path for local database for timestamp
# you can change it.

base_path = '/tmp/'
db_name = 'cron_timestamp'
data_path = base_path + db_name
tmp_path = '/tmp/tmp_cron'

class cron_monitor:

	def __init__(self):
		None
		
	@staticmethod
	def run_command(command):
		'''
		run the command and return the stdout result
		'''
		return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()


	@staticmethod
	def init_database():
		'''
		init the database if no database exists
		'''
		# check whether the database exists or not
		if os.path.exists(data_path) == False:
			cron_monitor.run_command('touch '+data_path)
			cron_monitor.run_sql('create table crons (id INTEGER PRIMARY KEY AUTOINCREMENT, user varchar not null, cron varchar not null, ref integer);')


	@staticmethod
	def run_sql(strsql):
		'''
		execute sql on sqlite	
		'''
		conn = sqlite3.connect(data_path)
		c = conn.cursor()	
		c.execute(strsql)
		result = c.fetchall()
		conn.commit()
		c.close()
		return result	


	@staticmethod
	def increase_refnum(user, entry):	
		'''
		increase the reference number of the entry for the user
		make monitor cron permanent 
		return the ref number
		'''	
		strsql = 'update crons set ref=ref+1 where user="' + user + '" and cron="' + entry + '"'
		cron_monitor.run_sql(strsql)
		strsql = 'update crons set ref=1 where user="root" and cron like "0 * * * * python%"'
		cron_monitor.run_sql(strsql)
		strsql = 'select ref from crons where user="' + user + '" and cron="' + entry + '"'
		return cron_monitor.run_sql(strsql)
	
	
	@staticmethod
	def register_entry(user, entry):
		'''
		register new entry for the user
		'''
		strsql = 'insert into crons(user, cron, ref) values("' + user + '", "' + entry + '", 0)'
		cron_monitor.run_sql(strsql)
	
	
	@staticmethod
	def delete_old_entries(user):
		'''
		delete entries older than 30 days (reference number if over 24 * 30)		
		'''
		strsql = 'delete from crons where user="' + user + '" and ref >= 24 * 30'
		cron_monitor.run_sql(strsql)
	
	
	@staticmethod
	def refresh_entries(user):
		'''
		refresh the crontab for the user
		'''
		strsql = 'select cron from crons where user="' + user +'"'
		entries = cron_monitor.run_sql(strsql)

		new_crontab = '\n'.join([a[0] for a in entries])
		cron_monitor.run_command('echo "'+new_crontab+'" >'+tmp_path)
		cron_monitor.run_command('crontab -u '+user+' '+tmp_path)
	
	@staticmethod
	def get_users():
		''' 
		return the users with crontab		
		'''
		# get candidate users from /var/spool/cron
		# it could contain non-user entry.
		pre_users = cron_monitor.run_command('ls /var/spool/cron')
		pre_users = set(re.split('\W+', pre_users))
		# get whole users from /etc/passwd
		etc_users = cron_monitor.run_command('cut -d \: -f 1 /etc/passwd')
		etc_users = set(re.split('\W+', etc_users))
		# get real users <- intersection
		return pre_users & etc_users - set([''])
		
	@staticmethod
	def get_user_cron_entries(user):
		'''
		return the cron entries for the user
		'''
		cron_entries = cron_monitor.run_command('crontab -u '+user+' -l')
		return re.split('\n', cron_entries.strip())
		
	@staticmethod
	def norm_cron_entry(cron_entry):
		'''
		normalize the cron_entry into standard form
			remove comments	
			trim the beginning and ending spaces
			change all whitespaces into a single space		
		'''
		
		cron_entry = cron_entry.strip()
			
		# strip the comments and normalize for further processing
		if cron_entry.find('#') == 0:
			cron_entry = ''
						
		cron_entry = re.sub('\s+', ' ', cron_entry)
		idx_c = cron_entry.find('#')
		if idx_c != -1:
			cron_entry = cron_entry[0:idx_c]
		return cron_entry.strip()
	
	@staticmethod
	def delete_removed_entries(user, cron_entries):
		'''
		delete crons removed by user herself
		'''
		strsql = 'select cron from crons where user="' + user + '"'
		all_entries = cron_monitor.run_sql(strsql)
		all_entries = [a[0] for a in all_entries]
		
		for entry in all_entries:
			if entry not in cron_entries:
				strsql = 'delete from crons where user="' + user + '" and cron = "' + entry + '"'
				cron_monitor.run_sql(strsql)
				
				
	@staticmethod
	def main():
		'''
		run main logic of the monitor
		'''
		cron_monitor.init_database();
		
		real_users = cron_monitor.get_users()
		for user in real_users:	
			cron_entries = cron_monitor.get_user_cron_entries(user)

			if cron_entries == None:
				continue
				
			crons = []	
			for cron_entry in cron_entries:
				cron_entry = cron_monitor.norm_cron_entry(cron_entry)
				
				if cron_entry == '':
					continue

				crons.append(cron_entry)
				# update the timestamp
				is_new = cron_monitor.increase_refnum(user, cron_entry) == []

				# if it is a new entry, register it with new timestamp
				if is_new:
					cron_monitor.register_entry(user, cron_entry)
			# delete entries older than 30 days
			cron_monitor.delete_old_entries(user)
	
			cron_monitor.delete_removed_entries(user, crons)
			# refresh the crontab with new information
			cron_monitor.refresh_entries(user)
				
				
if __name__ == '__main__':
	cron_monitor.main()		
