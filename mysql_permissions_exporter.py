#!/bin/python3

import time
import pymysql.cursors
import configparser
from prometheus_client import start_http_server, Gauge

class Configuration:

  def __init__(self):
    self.config = configparser.ConfigParser()
    self.SetDefaultConfig()
    self.config.read('/etc/mysql_permissions_exporter.cfg')

  def SetDefaultConfig(self):
    self.config['MySQL']     =  { 
                                  'mysql_hostname':   'localhost',
                                  'mysql_port':       '3306',
                                  'mysql_user':       'root',
                                  'mysql_password':   '',
                                  'mysql_use_socket': 'False',
                                  'mysql_socket':     '/var/lib/mysql/mysql.sock'
                                }
    self.config['WebServer'] =  {
                                  'webserver_port': '8000',
                                  'refresh': '5'
                                }
  def GetMySQLConfiguration(self):
    return self.config['MySQL']
  def GetWebServerConfiguration(self):
    return self.config['WebServer']
  
class MySQLUserInformation:
 
  def __init__(self, db):
    with db.cursor() as cursor:
      cursor.execute("""SELECT * FROM db""")

    self.result_set = cursor.fetchall()
    self.users = []
    self.GetMySQLUserData()

  def ConvertCharToInt(self, character):
    if character == 'Y':
      return 1
    else:
      return 0

  def GetMySQLUserData(self):
    counter = 0
    for row in self.result_set:
      self.users.append({
        'User':"", 
        'Host':"", 
        'Permission':
          {
            'SELECT':           0,
            'INSERT':           0,
            'UPDATE':           0,
            'DELETE':           0,
            'CREATE':           0,
            'DROP':             0,
            'GRANT':            0,
            'REFERENCES':       0,
            'INDEX':            0,
            'ALTER':            0,
            'CREATE_TMP_TABLE': 0,
            'LOCK_TABLES':      0,
            'CREATE_VIEW':      0,
            'SHOW_VIEW':        0,
            'CREATE_ROUTINE':   0,
            'ALTER_ROUTINE':    0,
            'EXECUTE':          0,
            'EVENT':            0,
            'TRIGGER':          0
          }
         })

      self.users[counter]['User']                             = row[2]
      self.users[counter]['Host']                             = row[0]
      self.users[counter]['DB']                               = row[1]
      self.users[counter]['Permission']['SELECT']             = self.ConvertCharToInt(row [3])
      self.users[counter]['Permission']['INSERT']             = self.ConvertCharToInt(row [4])
      self.users[counter]['Permission']['UPDATE']             = self.ConvertCharToInt(row [5])
      self.users[counter]['Permission']['DELETE']             = self.ConvertCharToInt(row [6])
      self.users[counter]['Permission']['CREATE']             = self.ConvertCharToInt(row [7])
      self.users[counter]['Permission']['DROP']               = self.ConvertCharToInt(row [8])
      self.users[counter]['Permission']['GRANT']              = self.ConvertCharToInt(row [9])
      self.users[counter]['Permission']['REFERENCES']         = self.ConvertCharToInt(row [10])
      self.users[counter]['Permission']['INDEX']              = self.ConvertCharToInt(row [11])
      self.users[counter]['Permission']['ALTER']              = self.ConvertCharToInt(row [12])
      self.users[counter]['Permission']['CREATE_TMP_TABLE']   = self.ConvertCharToInt(row [13])
      self.users[counter]['Permission']['LOCK_TABLES']        = self.ConvertCharToInt(row [14])
      self.users[counter]['Permission']['CREATE_VIEW']        = self.ConvertCharToInt(row [15])
      self.users[counter]['Permission']['SHOW_VIEW']          = self.ConvertCharToInt(row [16])
      self.users[counter]['Permission']['CREATE_ROUTINE']     = self.ConvertCharToInt(row [17])
      self.users[counter]['Permission']['ALTER_ROUTINE']      = self.ConvertCharToInt(row [18])
      self.users[counter]['Permission']['EXECUTE']            = self.ConvertCharToInt(row [19])
      self.users[counter]['Permission']['EVENT']              = self.ConvertCharToInt(row [20])
      self.users[counter]['Permission']['TRIGGER']            = self.ConvertCharToInt(row [21])
     
      counter += 1

  def GetUsers(self):
    return self.users

if __name__ == '__main__':
  config = Configuration()
 
  try:
    if config.GetMySQLConfiguration()['mysql_use_socket'] == "True":
      db = pymysql.connect  ( 
                              host     = config.GetMySQLConfiguration()['mysql_hostname'],
                              port     = config.GetMySQLConfiguration()['mysql_port'],
                              user     = config.GetMySQLConfiguration()['mysql_user'], 
                              password = config.GetMySQLConfiguration()['mysql_password'], 
                              db       = "mysql",
                              unix_socket=config.GetMySQLConfiguration()['mysql_socket']
                            )
    else:
      db = pymysql.connect  ( 
                              host     = config.GetMySQLConfiguration()['mysql_hostname'],
                              port     = config.GetMySQLConfiguration()['mysql_port'],
                              user     = config.GetMySQLConfiguration()['mysql_user'], 
                              password = config.GetMySQLConfiguration()['mysql_password'], 
                              db       = "mysql" 
                            )
  except:
    print("Error connecting to database at {}".format(config.GetMySQLConfiguration()['mysql_hostname']))
    exit(1)

  print("Database connection successful")

  start_http_server(int(config.GetWebServerConfiguration()['webserver_port']))
  
  gauge = Gauge(
    'mysql_permission', 
      "Permissions", 
      ["user","host","db","permission"]
    )

  try:
    while(True):
      MySQLStats = MySQLUserInformation(db)
      counter = 0
      for users in MySQLStats.GetUsers():
        for permission in users['Permission'].items():
          gauge.labels(users['User'],users["Host"], users["DB"], permission[0]).set(permission[1])
        counter += 1  
      del MySQLStats
      time.sleep(int(config.GetWebServerConfiguration()['refresh']))
  finally:
    db.close()