'''
unit test for cron monitor
written by Waff Jason
'''

import unittest
from monitor.cron_monitor import cron_monitor as cm


#global variables
base_path = '/tmp/'
db_name = 'cron_timestamp'
data_path = base_path + db_name
tmp_path = '/tmp/tmp_cron'

import os.path
class Cron_Monitor_Test(unittest.TestCase):
		
	def test_init_database(self):
		cm.init_database()
		self.assertEqual(os.path.exists(data_path), True)
		
	#register_entry(user, entry):
	def test_register_entry(self):
		cm.register_entry('jasmine', '@@@ test cron @@@')
		ref = cm.run_sql('select ref from crons where user="jasmine" and cron="@@@ test cron @@@"')
		cm.run_sql('delete from crons where user="jasmine" and cron="@@@ test cron @@@"')
		self.assertEqual(ref[0][0], 0)
			
	#increase_refnum(user, entry)	
	def test_increase_refnum(self):	
		cm.register_entry('jasmine', '@@@ test cron @@@')	
		cm.increase_refnum('jasmine', '@@@ test cron @@@')
		ref = cm.run_sql('select ref from crons where user="jasmine" and cron="@@@ test cron @@@"')
		cm.run_sql('delete from crons where user="jasmine" and cron="@@@ test cron @@@"')
		self.assertEqual(ref[0][0], 1)
		
	#delete_old_entries(user):
	def test_delete_old_entries(self):
		cm.run_sql('insert into crons(user, cron, ref) values("jasmine", "@@@ test cron @@@", 24*30)')
		cm.delete_old_entries('jasmine')
		ref = cm.run_sql('select ref from crons where user="jasmine" and cron="@@@ test cron @@@"')
		self.assertEqual(ref, [])
		cm.run_sql('insert into crons(user, cron, ref) values("jasmine", "@@@ test cron @@@", 24*30-1)')
		cm.delete_old_entries('jasmine')
		ref = cm.run_sql('select ref from crons where user="jasmine" and cron="@@@ test cron @@@"')
		cm.run_sql('delete from crons where user="jasmine" and cron="@@@ test cron @@@"')
		self.assertEqual(ref[0][0], 24*30-1)
		
	#get_users():
	def test_get_users(self):
		#print cm.get_users()
		pass
		
	#refresh_entries(user):	
	def test_refresh_entries(self):
		pass
	
	#norm_cron_entry(cron_entry):
	def test_norm_cron_entry(self):
		tentry = '*	*	*	* * /tmp #jasmine'
		self.assertEqual(cm.norm_cron_entry(tentry), '* * * * * /tmp')
		tentry = '			*	*	*	* * /tmp #jasmine'
		self.assertEqual(cm.norm_cron_entry(tentry), '* * * * * /tmp')
		tentry = '#*	*	*	* * /tmp #jasmine'
		self.assertEqual(cm.norm_cron_entry(tentry), '')
		
	
if __name__ == '__main__':
	unittest.main()
