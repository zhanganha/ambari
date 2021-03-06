'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import StringIO
import re
from unittest import TestCase
import sys
from mock.mock import patch
from mock.mock import MagicMock
from mock.mock import create_autospec
import os, errno, tempfile
import signal
import stat
import datetime
import operator
from pwd import getpwnam

# We have to use this import HACK because the filename contains a dash
ambari_server = __import__('ambari-server')
FatalException = ambari_server.FatalException
NonFatalException = ambari_server.NonFatalException


class TestAmbariServer(TestCase):

  def setUp(self):
    out = StringIO.StringIO()
    sys.stdout = out


  def tearDown(self):
    sys.stdout = sys.__stdout__


  @patch.object(ambari_server, 'configure_database_username_password')
  @patch.object(ambari_server, 'run_os_command')
  @patch('optparse.Values')
  def test_configure_pg_hba_ambaridb_users(self, OptParseValuesMock,
                                run_os_command_method,
                                configure_database_username_password_method):
    # Prepare mocks
    run_os_command_method.return_value = (0, "", "")
    opvm = OptParseValuesMock.return_value
    opvm.database_username = "ffdf"
    tf1 = tempfile.NamedTemporaryFile()
    ambari_server.PG_HBA_CONF_FILE = tf1.name
    # Run test
    ambari_server.configure_pg_hba_ambaridb_users()
    # Check results
    self.assertTrue(run_os_command_method.called)
    self.assertTrue(configure_database_username_password_method.called)
    string_expected = self.get_file_string(self
      .get_samples_dir("configure_pg_hba_ambaridb_users1"))
    string_actual = self.get_file_string(ambari_server.PG_HBA_CONF_FILE)
    self.assertEquals(string_expected, string_actual)
    pass

  @patch('__builtin__.raw_input')
  def test_servicename_regex(self, raw_input_method):

    ''' Test to make sure the service name can contain digits '''
    ambari_server.SILENT = False
    raw_input_method.return_value = "OT100"
    result = ambari_server.get_validated_service_name("ambari", 1)
    self.assertEqual("OT100", result, "Not accepting digits")
    pass
    
  @patch('__builtin__.raw_input')
  def test_dbname_regex(self, raw_input_method):

    ''' Test to make sure the service name can contain digits '''
    ambari_server.SILENT = False
    raw_input_method.return_value = "OT100"
    result = ambari_server.get_validated_db_name("ambari")
    self.assertEqual("OT100", result, "Not accepting digits")
 

  def test_configure_pg_hba_postgres_user(self):

    tf1 = tempfile.NamedTemporaryFile()
    ambari_server.PG_HBA_CONF_FILE = tf1.name

    with open(ambari_server.PG_HBA_CONF_FILE, 'w') as fout:
      fout.write("\n")
      fout.write("local  all  all md5\n")
      fout.write("host  all   all 0.0.0.0/0  md5\n")
      fout.write("host  all   all ::/0 md5\n")

    ambari_server.configure_pg_hba_postgres_user()

    expected  = self.get_file_string(self.get_samples_dir(
      "configure_pg_hba_ambaridb_users2"))
    result = self.get_file_string(ambari_server.PG_HBA_CONF_FILE)
    self.assertEqual(expected, result, "pg_hba_conf not processed")

    mode = oct(os.stat(ambari_server.PG_HBA_CONF_FILE)[stat.ST_MODE])
    str_mode = str(mode)[-4:]
    self.assertEqual("0644", str_mode, "Wrong file permissions")



  @patch('__builtin__.raw_input')
  def get_choice_string_input(self, raw_input_method):
    prompt = "blablabla"
    default = "default blablabla"
    firstChoice = set(['yes','ye', 'y'])
    secondChoice = set(['no','n'])
    # test first input
    raw_input_method.return_value = "Y"

    result = ambari_server.get_choice_string_input(prompt, default,
        firstChoice, secondChoice)
    self.assertEquals(result, True)
    raw_input_method.reset_mock()
    # test second input

    raw_input_method.return_value = "N"

    result = ambari_server.get_choice_string_input(prompt, default,
        firstChoice, secondChoice)
    self.assertEquals(result, False)

    raw_input_method.reset_mock()

    # test enter pressed

    raw_input_method.return_value = ""

    result = ambari_server.get_choice_string_input(prompt, default,
        firstChoice, secondChoice)
    self.assertEquals(result, default)

    raw_input_method.reset_mock()

    # test wrong input
    list_of_return_values= ['yes', 'dsad', 'fdsfds']
    def side_effect(list):
      return list_of_return_values.pop()
    raw_input_method.side_effect = side_effect

    result = ambari_server.get_choice_string_input(prompt, default,
        firstChoice, secondChoice)
    self.assertEquals(result, True)
    self.assertEquals(raw_input_method.call_count, 3)

    pass



  @patch('re.search')
  @patch('__builtin__.raw_input')
  @patch('getpass.getpass')
  def get_validated_string_input(self, get_pass_method,
      raw_input_method, re_search_method):
    prompt = "blabla"
    default = "default_pass"
    pattern = "pattern_pp"
    description = "blabla2"
    # check password input
    self.assertFalse(False, ambari_server.SILENT)
    is_pass = True
    get_pass_method.return_value = "dfdsfdsfds"

    result = ambari_server.get_validated_string_input(prompt, default,
        pattern, description, is_pass)

    self.assertEquals(get_pass_method.return_value, result)
    get_pass_method.assure_called_once(prompt)
    self.assertFalse(raw_input_method.called)

    # check raw input
    get_pass_method.reset_mock()
    raw_input_method.reset_mock()
    is_pass = False
    raw_input_method.return_value = "dkf90ewuf0"

    result = ambari_server.get_validated_string_input(prompt, default,
        pattern, description, is_pass)

    self.assertEquals(raw_input_method.return_value, result)
    self.assertFalse(get_pass_method.called)
    raw_input_method.assure_called_once(prompt)



  def test_get_pass_file_path(self):
    result = ambari_server.get_pass_file_path("/etc/ambari/conf_file")
    self.assertEquals("/etc/ambari/password.dat", result)
    pass


  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_setup(self, OptionParserMock, reset_method, stop_method,
                           start_method, setup_method):
    opm = OptionParserMock.return_value
    options = MagicMock()
    args = ["setup"]
    opm.parse_args.return_value = (options, args)

    options.database=None
    options.sid_or_sname = "sid"
    ambari_server.main()

    self.assertTrue(setup_method.called)
    self.assertFalse(start_method.called)
    self.assertFalse(stop_method.called)
    self.assertFalse(reset_method.called)

    self.assertFalse(False, ambari_server.VERBOSE)
    self.assertFalse(False, ambari_server.SILENT)


  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_start(self, OptionParserMock, reset_method, stop_method,
                           start_method, setup_method):
    opm = OptionParserMock.return_value
    options = MagicMock()
    args = ["setup"]
    opm.parse_args.return_value = (options, args)

    options.database=None
    options.sid_or_sname = "sname"
    ambari_server.main()

    self.assertTrue(setup_method.called)
    self.assertFalse(start_method.called)
    self.assertFalse(stop_method.called)
    self.assertFalse(reset_method.called)

    self.assertFalse(False, ambari_server.VERBOSE)
    self.assertFalse(False, ambari_server.SILENT)



  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_start_debug_short(self, OptionParserMock, reset_method, stop_method,
                           start_method, setup_method):
    opm = OptionParserMock.return_value
    options = MagicMock()
    args = ["start", "-g"]
    opm.parse_args.return_value = (options, args)

    options.database=None
    options.sid_or_sname = "sid"

    ambari_server.main()

    self.assertFalse(setup_method.called)
    self.assertTrue(start_method.called)
    self.assertFalse(stop_method.called)
    self.assertFalse(reset_method.called)

    self.assertTrue(ambari_server.SERVER_DEBUG_MODE)  



  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_start_debug_long(self, OptionParserMock, reset_method, stop_method,
                           start_method, setup_method):
    opm = OptionParserMock.return_value
    options = MagicMock()
    args = ["start", "--debug"]
    opm.parse_args.return_value = (options, args)
    options.database=None
    options.sid_or_sname = "sid"

    ambari_server.main()

    self.assertFalse(setup_method.called)
    self.assertTrue(start_method.called)
    self.assertFalse(stop_method.called)
    self.assertFalse(reset_method.called)

    self.assertTrue(ambari_server.SERVER_DEBUG_MODE)


  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_stop(self, OptionParserMock, reset_method, stop_method,
                          start_method, setup_method):
    opm = OptionParserMock.return_value
    options = MagicMock()
    args = ["stop"]
    opm.parse_args.return_value = (options, args)

    options.database = None
    options.sid_or_sname = "sid"

    ambari_server.main()

    self.assertFalse(setup_method.called)
    self.assertFalse(start_method.called)
    self.assertTrue(stop_method.called)
    self.assertFalse(reset_method.called)

    self.assertFalse(False, ambari_server.VERBOSE)
    self.assertFalse(False, ambari_server.SILENT)


  @patch.object(ambari_server, 'setup')
  @patch.object(ambari_server, 'start')
  @patch.object(ambari_server, 'stop')
  @patch.object(ambari_server, 'reset')
  @patch('optparse.OptionParser')
  def test_main_test_reset(self, OptionParserMock, reset_method, stop_method,
                           start_method, setup_method):
    opm = OptionParserMock.return_value

    options = MagicMock()
    args = ["reset"]
    opm.parse_args.return_value = (options, args)
    options.database=None
    options.sid_or_sname = "sid"

    ambari_server.main()

    self.assertFalse(setup_method.called)
    self.assertFalse(start_method.called)
    self.assertFalse(stop_method.called)
    self.assertTrue(reset_method.called)

    self.assertFalse(False, ambari_server.VERBOSE)
    self.assertFalse(False, ambari_server.SILENT)


  def test_configure_postgresql_conf(self):
    tf1 = tempfile.NamedTemporaryFile()
    ambari_server.POSTGRESQL_CONF_FILE = tf1.name

    with open(ambari_server.POSTGRESQL_CONF_FILE, 'w') as f:
      f.write("#listen_addresses = '127.0.0.1'        #\n")
      f.write("#listen_addresses = '127.0.0.1'")

    ambari_server.configure_postgresql_conf()

    expected  = self.get_file_string(self.get_samples_dir(
      "configure_postgresql_conf1"))
    result = self.get_file_string(ambari_server.POSTGRESQL_CONF_FILE)
    self.assertEqual(expected, result, "postgresql.conf not updated")

    mode = oct(os.stat(ambari_server.POSTGRESQL_CONF_FILE)[stat.ST_MODE])
    str_mode = str(mode)[-4:]
    self.assertEqual("0644", str_mode, "Wrong file permissions")


  @patch.object(ambari_server, "restart_postgres")
  @patch.object(ambari_server, "get_postgre_status")
  @patch.object(ambari_server, "configure_postgresql_conf")
  @patch.object(ambari_server, "configure_pg_hba_ambaridb_users")
  @patch.object(ambari_server, "configure_pg_hba_postgres_user")
  def test_configure_postgres(self, configure_pg_hba_postgres_user_mock,
                              configure_pg_hba_ambaridb_users_mock,
                              configure_postgresql_conf_mock,
                              get_postgre_status_mock,
                              restart_postgres_mock):
    tf1 = tempfile.NamedTemporaryFile()
    tf2 = tempfile.NamedTemporaryFile()
    ambari_server.PG_HBA_CONF_FILE = tf1.name
    ambari_server.PG_HBA_CONF_FILE_BACKUP = tf2.name
    args = MagicMock()

    out = StringIO.StringIO()
    sys.stdout = out
    rcode = ambari_server.configure_postgres()
    sys.stdout = sys.__stdout__
    self.assertEqual(0, rcode)
    self.assertEqual("Backup for pg_hba found, reconfiguration not required\n",
      out.getvalue())

    ambari_server.PG_HBA_CONF_FILE_BACKUP = tempfile.mktemp()
    get_postgre_status_mock.return_value = ambari_server.PG_STATUS_RUNNING
    restart_postgres_mock.return_value = 0

    rcode = ambari_server.configure_postgres()

    self.assertTrue(os.path.isfile(ambari_server.PG_HBA_CONF_FILE_BACKUP),
      "postgresql.conf backup not created")
    self.assertTrue(configure_pg_hba_postgres_user_mock.called)
    self.assertTrue(configure_pg_hba_ambaridb_users_mock.called)
    mode = oct(os.stat(ambari_server.PG_HBA_CONF_FILE)[stat.ST_MODE])
    str_mode = str(mode)[-4:]
    self.assertEqual("0644", str_mode, "Wrong file permissions")
    self.assertTrue(configure_postgresql_conf_mock.called)
    self.assertEqual(0, rcode)

    os.unlink(ambari_server.PG_HBA_CONF_FILE_BACKUP)
    get_postgre_status_mock.return_value = "stopped"
    rcode = ambari_server.configure_postgres()
    self.assertEqual(0, rcode)
    os.unlink(ambari_server.PG_HBA_CONF_FILE_BACKUP)
    sys.stdout = sys.__stdout__



  @patch("time.sleep")
  @patch("subprocess.Popen")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "get_postgre_status")
  @patch.object(ambari_server, "print_info_msg")
  def test_restart_postgres(self, printInfoMsg_mock, get_postgre_status_mock,
                            run_os_command_mock, popenMock, sleepMock):
    p = MagicMock()
    p.poll.return_value = 0
    popenMock.return_value = p
    rcode = ambari_server.restart_postgres()
    self.assertEqual(0, rcode)

    p.poll.return_value = None
    get_postgre_status_mock.return_value = "stopped"
    run_os_command_mock.return_value = (1, None, None)
    rcode = ambari_server.restart_postgres()
    self.assertEqual(1, rcode)



  @patch("shlex.split")
  @patch("subprocess.Popen")
  @patch.object(ambari_server, "print_info_msg")
  def test_run_os_command(self, printInfoMsg_mock, popenMock, splitMock):

    p = MagicMock()
    p.communicate.return_value = (None, None)
    p.returncode = 3
    popenMock.return_value = p

    # with list arg
    cmd = ["exec", "arg"]
    ambari_server.run_os_command(cmd)
    self.assertFalse(splitMock.called)

    # with str arg
    resp = ambari_server.run_os_command("runme")
    self.assertEqual(3, resp[0])
    self.assertTrue(splitMock.called)



  @patch.object(ambari_server, "get_conf_dir")
  @patch.object(ambari_server, "search_file")
  def test_write_property(self, search_file_mock, get_conf_dir_mock):

    expected_content = "key1=val1\n"

    tf1 = tempfile.NamedTemporaryFile()
    search_file_mock.return_value = tf1.name
    ambari_server.write_property("key1", "val1")
    result = tf1.read()
    self.assertTrue(expected_content in result)



  @patch.object(ambari_server, "configure_database_username_password")
  @patch.object(ambari_server, "run_os_command")
  def test_setup_db(self, run_os_command_mock,
                    configure_database_username_password_mock):

    run_os_command_mock.return_value = (0, None, None)
    result = ambari_server.setup_db(MagicMock())
    self.assertTrue(configure_database_username_password_mock.called)
    self.assertEqual(0, result)



  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "run_os_command")
  def test_check_selinux(self, run_os_command_mock, getYNInput_mock):
    run_os_command_mock.return_value = (0, ambari_server.SE_STATUS_DISABLED,
                                        None)
    rcode = ambari_server.check_selinux()
    self.assertEqual(0, rcode)

    getYNInput_mock.return_value = True
    run_os_command_mock.return_value = (0,"enabled "
                                          + ambari_server.SE_MODE_ENFORCING,
                                        None)
    rcode = ambari_server.check_selinux()
    self.assertEqual(0, rcode)
    self.assertTrue(run_os_command_mock.called)
    self.assertTrue(getYNInput_mock.called)



  @patch.object(ambari_server, "print_info_msg")
  def test_get_ambari_jars(self, printInfoMsg_mock):

    env = "/ambari/jars"
    os.environ[ambari_server.AMBARI_SERVER_LIB] = env
    result = ambari_server.get_ambari_jars()
    self.assertEqual(env, result)

    del os.environ[ambari_server.AMBARI_SERVER_LIB]
    result = ambari_server.get_ambari_jars()
    self.assertEqual("/usr/lib/ambari-server", result)
    self.assertTrue(printInfoMsg_mock.called)


  @patch("glob.glob")
  @patch.object(ambari_server, "print_info_msg")
  def test_get_share_jars(self, printInfoMsg_mock, globMock):
    globMock.return_value = ["one", "two"]
    expected = "one:two:one:two"
    result = ambari_server.get_share_jars()
    self.assertEqual(expected, result)
    globMock.return_value = []
    expected = ""
    result = ambari_server.get_share_jars()
    self.assertEqual(expected, result)


  @patch("glob.glob")
  @patch.object(ambari_server, "print_info_msg")
  def test_get_ambari_classpath(self, printInfoMsg_mock, globMock):
    globMock.return_value = ["one"]
    result = ambari_server.get_ambari_classpath()
    self.assertTrue(ambari_server.get_ambari_jars() in result)
    self.assertTrue(ambari_server.get_share_jars() in result)
    globMock.return_value = []
    result = ambari_server.get_ambari_classpath()
    self.assertTrue(ambari_server.get_ambari_jars() in result)
    self.assertFalse(":" in result)


  @patch.object(ambari_server, "print_info_msg")
  def test_get_conf_dir(self, printInfoMsg_mock):
    env = "/dummy/ambari/conf"
    os.environ[ambari_server.AMBARI_CONF_VAR] = env
    result = ambari_server.get_conf_dir()
    self.assertEqual(env, result)

    del os.environ[ambari_server.AMBARI_CONF_VAR]
    result = ambari_server.get_conf_dir()
    self.assertEqual("/etc/ambari-server/conf", result)


  def test_search_file(self):

    path = os.path.dirname(__file__)
    result = ambari_server.search_file(__file__, path)
    expected = os.path.abspath(__file__)
    self.assertEqual(expected, result)

    result = ambari_server.search_file("non_existent_file", path)
    self.assertEqual(None, result)


  @patch.object(ambari_server, "search_file")
  def test_find_properties_file(self, search_file_mock):
    # Testing case when file is not found
    search_file_mock.return_value = None
    try:
      ambari_server.find_properties_file()
      self.fail("File not found'")
    except FatalException:
      # Expected
      pass
    self.assertTrue(search_file_mock.called)

    # Testing case when file is found
    value = MagicMock()
    search_file_mock.return_value = value
    result = ambari_server.find_properties_file()
    self.assertTrue(result is value)


  @patch.object(ambari_server, "find_properties_file")
  @patch("__builtin__.open")
  @patch("ambari-server.Properties")
  def test_read_ambari_user(self, properties_mock, open_mock, find_properties_file_mock):
    open_mock.return_value = "dummy"
    find_properties_file_mock.return_value = "dummy"
    # Testing with defined user
    properties_mock.return_value.__getitem__.return_value = "dummy_user"
    user = ambari_server.read_ambari_user()
    self.assertEquals(user, "dummy_user")
    # Testing with undefined user
    properties_mock.return_value.__getitem__.return_value = None
    user = ambari_server.read_ambari_user()
    self.assertEquals(user, None)


  @patch("os.path.exists")
  @patch.object(ambari_server, "set_file_permissions")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "get_ambari_properties")
  @patch.object(ambari_server, "get_value_from_properties")
  @patch("os.mkdir")
  def test_adjust_directory_permissions(self, mkdir_mock,
            get_value_from_properties_mock, get_ambari_properties_mock,
            run_os_command_mock, set_file_permissions_mock, exists_mock):
    # Testing boostrap dir wipe
    properties_mock = MagicMock()
    get_value_from_properties_mock.return_value = "dummy_bootstrap_dir"
    ambari_server.adjust_directory_permissions("user")
    exists_mock.return_value = False
    self.assertEquals(run_os_command_mock.call_args_list[0][0][0], "rm -rf dummy_bootstrap_dir")
    self.assertTrue(mkdir_mock.called)

    set_file_permissions_mock.reset_mock()
    # Test recursive calls
    old_list = ambari_server.NR_ADJUST_OWNERSHIP_LIST

    ambari_server.NR_ADJUST_OWNERSHIP_LIST = [
      ( "/etc/ambari-server/conf", "755", "{0}", True ),
      ( "/etc/ambari-server/conf/ambari.properties", "644", "{0}", False )
    ]

    ambari_server.adjust_directory_permissions("user")
    self.assertTrue(len(set_file_permissions_mock.call_args_list) ==
                    len(ambari_server.NR_ADJUST_OWNERSHIP_LIST))
    self.assertEquals(set_file_permissions_mock.call_args_list[0][0][3], True)
    self.assertEquals(set_file_permissions_mock.call_args_list[1][0][3], False)

    ambari_server.NR_ADJUST_OWNERSHIP_LIST = old_list


  @patch("os.path.exists")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "print_warning_msg")
  @patch.object(ambari_server, "print_info_msg")
  def test_set_file_permissions(self, print_info_msg_mock, print_warning_msg_mock,
                                run_os_command_mock, exists_mock):

    # Testing not existent file scenario
    exists_mock.return_value = False
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", False)
    self.assertFalse(run_os_command_mock.called)
    self.assertTrue(print_info_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()

    # Testing OK scenario
    exists_mock.return_value = True
    run_os_command_mock.side_effect = [(0, "", ""), (0, "", "")]
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", False)
    self.assertTrue(len(run_os_command_mock.call_args_list) == 2)
    self.assertFalse(print_warning_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()

    # Testing first command fail
    run_os_command_mock.side_effect = [(1, "", ""), (0, "", "")]
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", False)
    self.assertTrue(len(run_os_command_mock.call_args_list) == 2)
    self.assertTrue(print_warning_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()

    # Testing second command fail
    run_os_command_mock.side_effect = [(0, "", ""), (1, "", "")]
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", False)
    self.assertTrue(len(run_os_command_mock.call_args_list) == 2)
    self.assertTrue(print_warning_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()

    # Testing recursive operation

    exists_mock.return_value = True
    run_os_command_mock.side_effect = [(0, "", ""), (0, "", "")]
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", True)
    self.assertTrue(len(run_os_command_mock.call_args_list) == 2)
    self.assertTrue("-R" in run_os_command_mock.call_args_list[0][0][0])
    self.assertTrue("-R" in run_os_command_mock.call_args_list[1][0][0])
    self.assertFalse(print_warning_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()

    # Testing non-recursive operation

    exists_mock.return_value = True
    run_os_command_mock.side_effect = [(0, "", ""), (0, "", "")]
    ambari_server.set_file_permissions("dummy-file", "dummy-mod",
                                       "dummy-user", False)
    self.assertTrue(len(run_os_command_mock.call_args_list) == 2)
    self.assertFalse("-R" in run_os_command_mock.call_args_list[0][0][0])
    self.assertFalse("-R" in run_os_command_mock.call_args_list[1][0][0])
    self.assertFalse(print_warning_msg_mock.called)

    run_os_command_mock.reset_mock()
    print_warning_msg_mock.reset_mock()



  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "print_warning_msg")
  @patch.object(ambari_server, "run_os_command")
  def test_create_custom_user(self, run_os_command_mock, print_warning_msg_mock,
          print_info_msg_mock, get_validated_string_input_mock):
    user = "dummy-user"
    get_validated_string_input_mock.return_value = user

    # Testing scenario: absent user
    run_os_command_mock.side_effect = [(0, "", "")]
    result = ambari_server.create_custom_user()
    self.assertFalse(print_warning_msg_mock.called)
    self.assertEquals(result, (0, user))

    print_info_msg_mock.reset_mock()
    print_warning_msg_mock.reset_mock()
    run_os_command_mock.reset_mock()

    # Testing scenario: existing user
    run_os_command_mock.side_effect = [(9, "", "")]
    result = ambari_server.create_custom_user()
    self.assertTrue("User dummy-user already exists" in str(print_info_msg_mock.call_args_list[1][0]))
    self.assertEquals(result, (0, user))

    print_info_msg_mock.reset_mock()
    print_warning_msg_mock.reset_mock()
    run_os_command_mock.reset_mock()

    # Testing scenario: os command fail
    run_os_command_mock.side_effect = [(1, "", "")]
    result = ambari_server.create_custom_user()
    self.assertTrue(print_warning_msg_mock.called)
    self.assertEquals(result, (1, None))



  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "create_custom_user")
  @patch.object(ambari_server, "write_property")
  @patch.object(ambari_server, "adjust_directory_permissions")
  @patch.object(ambari_server, "print_error_msg")
  def test_check_ambari_user(self, print_error_msg_mock,
            adjust_directory_permissions_mock, write_property_mock,
            create_custom_user_mock, get_YN_input_mock, read_ambari_user_mock):

    # Scenario: user is already defined, user does not want to reconfigure it
    read_ambari_user_mock.return_value = "dummy-user"
    get_YN_input_mock.return_value = False
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertFalse(write_property_mock.called)
    self.assertFalse(create_custom_user_mock.called)
    self.assertTrue(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 0)

    get_YN_input_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()
    create_custom_user_mock.reset_mock()

    # Scenario: user is already defined, but user wants to reconfigure it

    read_ambari_user_mock.return_value = "dummy-user"
    create_custom_user_mock.return_value = (0, "new-dummy-user")
    get_YN_input_mock.return_value = True
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(write_property_mock.called)
    self.assertTrue(write_property_mock.call_args[0][1] == "new-dummy-user")
    self.assertTrue(create_custom_user_mock.called)
    self.assertTrue(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 0)

    get_YN_input_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()
    create_custom_user_mock.reset_mock()

    # Negative scenario: user is already defined, but user wants
    # to reconfigure it, user creation failed

    read_ambari_user_mock.return_value = "dummy-user"
    create_custom_user_mock.return_value = (1, None)
    get_YN_input_mock.return_value = True
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(create_custom_user_mock.called)
    self.assertFalse(write_property_mock.called)
    self.assertFalse(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 1)

    get_YN_input_mock.reset_mock()
    create_custom_user_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()

    # Scenario: user is not defined (setup process)
    read_ambari_user_mock.return_value = None
    get_YN_input_mock.return_value = True
    create_custom_user_mock.return_value = (0, "dummy-user")
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(create_custom_user_mock.called)
    self.assertTrue(write_property_mock.called)
    self.assertTrue(write_property_mock.call_args[0][1] == "dummy-user")
    self.assertTrue(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 0)

    get_YN_input_mock.reset_mock()
    create_custom_user_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()

    # Scenario: user is not defined (setup process), user creation failed

    read_ambari_user_mock.return_value = None
    get_YN_input_mock.return_value = True
    create_custom_user_mock.return_value = (1, None)
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(create_custom_user_mock.called)
    self.assertFalse(write_property_mock.called)
    self.assertFalse(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 1)

    get_YN_input_mock.reset_mock()
    create_custom_user_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()

    # negative scenario: user is not defined (setup process), user creation failed

    read_ambari_user_mock.return_value = None
    get_YN_input_mock.return_value = True
    create_custom_user_mock.return_value = (1, None)
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(create_custom_user_mock.called)
    self.assertFalse(write_property_mock.called)
    self.assertFalse(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 1)

    get_YN_input_mock.reset_mock()
    create_custom_user_mock.reset_mock()
    write_property_mock.reset_mock()
    adjust_directory_permissions_mock.reset_mock()

    # Scenario: user is not defined and left to be root
    read_ambari_user_mock.return_value = None
    get_YN_input_mock.return_value = False
    result = ambari_server.check_ambari_user()
    self.assertTrue(get_YN_input_mock.called)
    self.assertFalse(create_custom_user_mock.called)
    self.assertTrue(write_property_mock.called)
    self.assertTrue(write_property_mock.call_args[0][1] == "root")
    self.assertTrue(adjust_directory_permissions_mock.called)
    self.assertEqual(result, 0)


  @patch.object(ambari_server, "search_file")
  @patch("__builtin__.open")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "set_file_permissions")
  def test_store_password_file(self, set_file_permissions_mock,
                    read_ambari_user_mock, open_mock, search_file_mock):
    search_file_mock.return_value = "/etc/ambari-server/conf/ambari.properties"
    open_mock.return_value = MagicMock()
    ambari_server.store_password_file("password", "passfile")
    self.assertTrue(set_file_permissions_mock.called)


  @patch.object(ambari_server, "run_os_command")
  def test_check_iptables(self, run_os_command_mock):
    run_os_command_mock.return_value = (1, "test", "")
    rcode, info = ambari_server.check_iptables()
    self.assertEqual(1, rcode)
    self.assertEqual("test", info)

    run_os_command_mock.return_value = (2, "",
                                        ambari_server.IP_TBLS_SRVC_NT_FND)
    rcode = ambari_server.check_iptables()
    self.assertEqual(0, rcode)


  def test_dlprogress(self):

    out = StringIO.StringIO()
    sys.stdout = out
    ambari_server.dlprogress("filename", 10, 2, 100)
    sys.stdout = sys.__stdout__
    self.assertNotEqual("", out.getvalue())


  @patch("urllib2.urlopen")
  @patch("__builtin__.open")
  @patch.object(ambari_server, "dlprogress")
  def test_track_jdk(self, dlprogress_mock, openMock, urlopenMock):

    u = MagicMock()
    u.info.return_value = {"Content-Length":"24576"}
    chunks = [None, "second", "first"]
    def side_effect(*args, **kwargs):
      return chunks.pop()
    u.read.side_effect = side_effect
    urlopenMock.return_value = u

    f = MagicMock()
    openMock.return_value = f

    ambari_server.track_jdk("base", "url", "local")

    self.assertEqual(0, len(chunks))
    self.assertTrue(f.write.called)
    self.assertTrue(f.flush.called)
    self.assertTrue(f.close.called)
    self.assertEqual(2, len(dlprogress_mock.call_args_list))


  @patch("shutil.copy")
  @patch("os.path.join")
  @patch("os.path.exists")
  @patch.object(ambari_server, "get_ambari_properties")
  def test_install_jce_manualy(self, get_ambari_properties_mock,\
                               os_path_exists_mock, os_path_join_mock,\
                               shutil_copy_mock):
    args = MagicMock()
    args.jce_policy = "somewhere"
    p = MagicMock()
    get_ambari_properties_mock.return_value = p
    p.__getitem__.side_effect = None
    p.__getitem__.return_value = "somewhere"
    os_path_exists_mock.return_value = True
    os_path_join_mock.return_value = \
                            "/var/lib/ambari-server/resources/jce_policy-6.zip" 
    ambari_server.install_jce_manualy(args)	
    self.assertTrue(shutil_copy_mock.called)

    shutil_copy_mock.side_effect = Exception("exception")
    try:
      ambari_server.install_jce_manualy(args)
      self.fail("Should throw exception because of not found jce_policy-6.zip")
    except Exception:
       # Expected
      self.assertTrue(shutil_copy_mock.called)
      pass  

    shutil_copy_mock.side_effect = None
    args.jce_policy = None
    ambari_server.install_jce_manualy(args)


  @patch.object(ambari_server, 'read_ambari_user')
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "find_properties_file")
  @patch.object(ambari_server, "get_ambari_properties")
  @patch.object(ambari_server, "is_server_runing")
  @patch.object(ambari_server, "import_cert_and_key_action")  
  @patch.object(ambari_server, "get_YN_input")  
  @patch("__builtin__.open")
  @patch("ambari-server.Properties")
  @patch.object(ambari_server, "is_root")
  @patch.object(ambari_server, "is_valid_cert_host")  
  @patch.object(ambari_server, "is_valid_cert_exp") 
  def test_setup_https(self, is_valid_cert_exp_mock, is_valid_cert_host_mock,\
                       is_root_mock, Properties_mock, open_Mock, get_YN_input_mock,\
                       import_cert_and_key_action_mock,
                       is_server_runing_mock, get_ambari_properties_mock,\
                       find_properties_file_mock,\
                       get_validated_string_input_mock,
                       read_ambari_user_method):
      
    is_valid_cert_exp_mock.return_value=True
    is_valid_cert_host_mock.return_value=True
    args = MagicMock()
    open_Mock.return_value = file
    p = get_ambari_properties_mock.return_value

    # Testing call under non-root
    is_root_mock.return_value = False
    try:
      ambari_server.setup_https(args)
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing call under root
    is_root_mock.return_value = True
    read_ambari_user_method.return_value = None
    #Case #1: if client ssl is on and user didnt choose 
    #disable ssl option and choose import certs and keys
    p.get_property.side_effect = ["key_dir","5555","6666", "true"]
    get_YN_input_mock.side_effect = [False,True]
    get_validated_string_input_mock.side_effect = ["4444"]
    get_property_expected = "[call('security.server.keys_dir'),\n"+\
                            " call('client.api.ssl.port'),\n"+\
                            " call('client.api.ssl.port'),\n call('api.ssl')]"
    process_pair_expected = "[call('client.api.ssl.port', '4444')]"
    ambari_server.SILENT = False
    ambari_server.setup_https(args)
    
    self.assertTrue(p.process_pair.called)
    self.assertTrue(p.get_property.call_count == 4)
    self.assertEqual(str(p.get_property.call_args_list), get_property_expected)
    self.assertEqual(str(p.process_pair.call_args_list), process_pair_expected)
    self.assertTrue(p.store.called)
    self.assertTrue(import_cert_and_key_action_mock.called)

    p.process_pair.reset_mock()
    p.get_property.reset_mock()
    p.store.reset_mock()
    import_cert_and_key_action_mock.reset_mock()

    #Case #2: if client ssl is on and user choose to disable ssl option
    p.get_property.side_effect = ["key_dir","", "true"]
    get_YN_input_mock.side_effect = [True]
    get_validated_string_input_mock.side_effect = ["4444"]
    get_property_expected = "[call('security.server.keys_dir'),\n"+\
                            " call('client.api.ssl.port'),\n call('api.ssl')]"
    process_pair_expected = "[call('api.ssl', 'false')]"
    ambari_server.setup_https(args)
    
    self.assertTrue(p.process_pair.called)
    self.assertTrue(p.get_property.call_count == 3)
    self.assertEqual(str(p.get_property.call_args_list), get_property_expected)
    self.assertEqual(str(p.process_pair.call_args_list), process_pair_expected)
    self.assertTrue(p.store.called)
    self.assertFalse(import_cert_and_key_action_mock.called)

    p.process_pair.reset_mock()
    p.get_property.reset_mock()
    p.store.reset_mock()
    import_cert_and_key_action_mock.reset_mock()

    #Case #3: if client ssl is off and user choose option 
    #to import cert and keys
    p.get_property.side_effect = ["key_dir","", None]
    get_YN_input_mock.side_effect = [True, True]
    get_validated_string_input_mock.side_effect = ["4444"]
    get_property_expected = "[call('security.server.keys_dir'),\n"+\
                            " call('client.api.ssl.port'),\n call('api.ssl')]"
    process_pair_expected = "[call('client.api.ssl.port', '4444')]"
    ambari_server.setup_https(args)

    self.assertTrue(p.process_pair.called)
    self.assertTrue(p.get_property.call_count == 3)
    self.assertEqual(str(p.get_property.call_args_list), get_property_expected)
    self.assertEqual(str(p.process_pair.call_args_list), process_pair_expected)
    self.assertTrue(p.store.called)
    self.assertTrue(import_cert_and_key_action_mock.called)

    p.process_pair.reset_mock()
    p.get_property.reset_mock()
    p.store.reset_mock()
    import_cert_and_key_action_mock.reset_mock()
    
    #Case #4: if client ssl is off and 
    #user did not choose option to import cert and keys
    p.get_property.side_effect = ["key_dir","", None]
    get_YN_input_mock.side_effect = [False]
    get_validated_string_input_mock.side_effect = ["4444"]
    get_property_expected = "[call('security.server.keys_dir'),\n"+\
    " call('client.api.ssl.port'),\n call('api.ssl')]"
    process_pair_expected = "[]"
    ambari_server.setup_https(args)

    self.assertFalse(p.process_pair.called)
    self.assertTrue(p.get_property.call_count == 3)
    self.assertEqual(str(p.get_property.call_args_list), get_property_expected)
    self.assertEqual(str(p.process_pair.call_args_list), process_pair_expected)
    self.assertFalse(p.store.called)
    self.assertFalse(import_cert_and_key_action_mock.called)

    p.process_pair.reset_mock()
    p.get_property.reset_mock()
    p.store.reset_mock()
    import_cert_and_key_action_mock.reset_mock() 
    ambari_server.SILENT = True
    
  @patch.object(ambari_server, "import_cert_and_key")
  def test_import_cert_and_key_action(self, import_cert_and_key_mock):
    import_cert_and_key_mock.return_value = True
    properties = MagicMock()
    properties.get_property.side_effect = ["key_dir","5555","6666", "true"]
    properties.process_pair = MagicMock()
    expect_process_pair = "[call('client.api.ssl.cert_name', 'https.crt'),\n"+\
                          " call('client.api.ssl.key_name', 'https.key'),\n"+\
                          " call('api.ssl', 'true')]"
    ambari_server.import_cert_and_key_action("key_dir", properties)
  	
    self.assertEqual(str(properties.process_pair.call_args_list),\
                     expect_process_pair)
    
  @patch.object(ambari_server, "remove_file")
  @patch.object(ambari_server, "copy_file")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "set_file_permissions")
  @patch.object(ambari_server, "import_file_to_keystore")
  @patch("__builtin__.open")
  @patch.object(ambari_server, "run_os_command")
  @patch("os.path.join")
  @patch.object(ambari_server, "get_validated_filepath_input")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "is_valid_cert_host")  
  @patch.object(ambari_server, "is_valid_cert_exp")  
  def test_import_cert_and_key(self,is_valid_cert_exp_mock,\
                               is_valid_cert_host_mock,\
                               get_validated_string_input_mock,\
                               get_validated_filepath_input_mock,\
                               os_path_join_mock, run_os_command_mock,\
                               open_mock, import_file_to_keystore_mock,\
                               set_file_permissions_mock, read_ambari_user_mock, copy_file_mock,\
                               remove_file_mock):
    is_valid_cert_exp_mock.return_value=True
    is_valid_cert_host_mock.return_value=True
    get_validated_string_input_mock.return_value = "password"
    get_validated_filepath_input_mock.side_effect = \
                                            ["cert_file_path","key_file_path"]
    os_path_join_mock.side_effect = ["keystore_file_path", "keystore_file_path_tmp",\
                                     "pass_file_path", "pass_file_path_tmp",\
                                     "passin_file_path","password_file_path",\
                                     "keystore_cert_file_path",\
                                     "keystore_cert_key_file_path",]
    run_os_command_mock.return_value = (0, "",	"")
    om = open_mock.return_value
    expect_import_file_to_keystore = "[call('keystore_file_path_tmp',"+\
                                     " 'keystore_file_path'),\n"+\
                                     " call('pass_file_path_tmp',"+\
                                     " 'pass_file_path'),\n"+\
                                     " call('cert_file_path',"+\
                                     " 'keystore_cert_file_path'),\n"+\
                                     " call('key_file_path',"+\
                                     " 'keystore_cert_key_file_path')]"

    ambari_server.import_cert_and_key("key_dir")
    self.assertTrue(get_validated_filepath_input_mock.call_count == 2)
    self.assertTrue(get_validated_string_input_mock.called)
    self.assertEqual(os_path_join_mock.call_count, 8)
    self.assertTrue(set_file_permissions_mock.call_count == 1)
    self.assertEqual(str(import_file_to_keystore_mock.call_args_list),\
                         expect_import_file_to_keystore)

  @patch.object(ambari_server, "remove_file")
  @patch.object(ambari_server, "copy_file")
  @patch.object(ambari_server, "generate_random_string")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "set_file_permissions")
  @patch.object(ambari_server, "import_file_to_keystore")
  @patch("__builtin__.open")
  @patch.object(ambari_server, "run_os_command")
  @patch("os.path.join")
  @patch.object(ambari_server, "get_validated_filepath_input")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "is_valid_cert_host")  
  @patch.object(ambari_server, "is_valid_cert_exp")  
  def test_import_cert_and_key_with_empty_password(self, \
    is_valid_cert_exp_mock, is_valid_cert_host_mock,                                         
    get_validated_string_input_mock, get_validated_filepath_input_mock,\
    os_path_join_mock, run_os_command_mock, open_mock, \
    import_file_to_keystore_mock, set_file_permissions_mock,
    read_ambari_user_mock, generate_random_string_mock, copy_file_mock,\
    remove_file_mock):
      
    is_valid_cert_exp_mock.return_value=True
    is_valid_cert_host_mock.return_value=True
    get_validated_string_input_mock.return_value = ""
    get_validated_filepath_input_mock.side_effect =\
    ["cert_file_path","key_file_path"]
    os_path_join_mock.side_effect = ["keystore_file_path", "keystore_file_path_tmp",\
                                     "pass_file_path", "pass_file_path_tmp",\
                                     "passin_file_path","password_file_path",\
                                     "keystore_cert_file_path",\
                                     "keystore_cert_key_file_path",]
    run_os_command_mock.return_value = (0, "",	"")

    expect_import_file_to_keystore = "[call('keystore_file_path_tmp',"+\
                                     " 'keystore_file_path'),\n"+\
                                     " call('pass_file_path_tmp',"+\
                                     " 'pass_file_path'),\n"+\
                                     " call('cert_file_path',"+\
                                     " 'keystore_cert_file_path'),\n"+\
                                     " call('key_file_path.secured',"+\
                                     " 'keystore_cert_key_file_path')]"

    ambari_server.import_cert_and_key("key_dir")
    self.assertEquals(get_validated_filepath_input_mock.call_count, 2)
    self.assertTrue(get_validated_string_input_mock.called)
    self.assertEquals(os_path_join_mock.call_count, 8)
    self.assertEquals(set_file_permissions_mock.call_count, 1)
    self.assertEqual(str(import_file_to_keystore_mock.call_args_list),\
      expect_import_file_to_keystore)
    self.assertTrue(generate_random_string_mock.called)

  @patch("__builtin__.open")
  @patch.object(ambari_server, "copy_file")
  @patch.object(ambari_server, "is_root")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "set_file_permissions")
  @patch.object(ambari_server, "import_file_to_keystore")
  @patch.object(ambari_server, "run_os_command")
  @patch("os.path.join")
  @patch.object(ambari_server, "get_validated_filepath_input")
  @patch.object(ambari_server, "get_validated_string_input")
  def test_import_cert_and_key_with_incorrect_password(self,
                                                       get_validated_string_input_mock,\
                                                       get_validated_filepath_input_mock,\
                                                       os_path_join_mock,\
                                                       run_os_command_mock,\
                                                       import_file_to_keystore_mock,\
                                                       set_file_permissions_mock,\
                                                       read_ambari_user_mock,\
                                                       is_root_mock,\
                                                       copy_file_mock,\
                                                       open_mock):
    get_validated_string_input_mock.return_value = "incorrect_password"
    get_validated_filepath_input_mock.return_value = 'filename'
    open_mock.return_value = MagicMock()

    os_path_join_mock.return_value = ''
    is_root_mock.return_value = True


    #provided password doesn't match, openssl command returns an error
    run_os_command_mock.return_value = (1, "",	"Some error message")

    self.assertFalse(ambari_server.import_cert_and_key_action(*["key_dir", None]))
    self.assertFalse(ambari_server.import_cert_and_key("key_dir"))

  def test_is_valid_cert_exp(self):
    
    #No data in certInfo
    certInfo = {}
    is_valid = ambari_server.is_valid_cert_exp(certInfo)
    self.assertFalse(is_valid)
    
    #Issued in future
    issuedOn = (datetime.datetime.now() + datetime.timedelta(hours=1000)).strftime(ambari_server.SSL_DATE_FORMAT)
    expiresOn = (datetime.datetime.now() + datetime.timedelta(hours=2000)).strftime(ambari_server.SSL_DATE_FORMAT)
    certInfo = {ambari_server.NOT_BEFORE_ATTR : issuedOn,
                ambari_server.NOT_AFTER_ATTR  : expiresOn}
    is_valid = ambari_server.is_valid_cert_exp(certInfo)
    self.assertFalse(is_valid)
    
    #Was expired
    issuedOn = (datetime.datetime.now() - datetime.timedelta(hours=2000)).strftime(ambari_server.SSL_DATE_FORMAT)
    expiresOn = (datetime.datetime.now() - datetime.timedelta(hours=1000)).strftime(ambari_server.SSL_DATE_FORMAT)
    certInfo = {ambari_server.NOT_BEFORE_ATTR : issuedOn,
                ambari_server.NOT_AFTER_ATTR  : expiresOn}
    is_valid = ambari_server.is_valid_cert_exp(certInfo)
    self.assertFalse(is_valid)
    
    #Valid
    issuedOn = (datetime.datetime.now() - datetime.timedelta(hours=2000)).strftime(ambari_server.SSL_DATE_FORMAT)
    expiresOn = (datetime.datetime.now() + datetime.timedelta(hours=1000)).strftime(ambari_server.SSL_DATE_FORMAT)
    certInfo = {ambari_server.NOT_BEFORE_ATTR : issuedOn,
                ambari_server.NOT_AFTER_ATTR  : expiresOn}
    is_valid = ambari_server.is_valid_cert_exp(certInfo)
    self.assertTrue(is_valid)
    
  @patch.object(ambari_server, "get_fqdn")
  def is_valid_cert_host(self, get_fqdn_mock):
    
    #No data in certInfo
    certInfo = {}
    is_valid = ambari_server.is_valid_cert_host(certInfo)
    self.assertFalse(is_valid)
    
    #Failed to get FQDN
    get_fqdn_mock.return_value = None
    is_valid = ambari_server.is_valid_cert_host(certInfo)
    self.assertFalse(is_valid)
    
    #FQDN and Common name in certificated don't correspond
    get_fqdn_mock.return_value = 'host1'
    certInfo = {ambari_server.COMMON_NAME_ATTR : 'host2'}
    is_valid = ambari_server.is_valid_cert_host(certInfo)
    self.assertFalse(is_valid)
    
    #FQDN and Common name in certificated correspond
    get_fqdn_mock.return_value = 'host1'
    certInfo = {ambari_server.COMMON_NAME_ATTR : 'host1'}
    is_valid = ambari_server.is_valid_cert_host(certInfo)
    self.assertFalse(is_valid)

  @patch("socket.getfqdn")
  @patch("urllib2.urlopen")
  @patch.object(ambari_server, "get_ambari_properties")
  def test_get_fqdn(self, get_ambari_properties_mock, url_open_mock, getfqdn_mock):
    
    #No ambari.properties
    get_ambari_properties_mock.return_value = -1
    fqdn = ambari_server.get_fqdn()
    self.assertEqual(fqdn, None)
    
    #Check mbari_server.GET_FQDN_SERVICE_URL property name (AMBARI-2612)
    #property name should be server.fqdn.service.url
    self.assertEqual(ambari_server.GET_FQDN_SERVICE_URL, "server.fqdn.service.url")
    
    #Read FQDN from service
    p = MagicMock()
    p[ambari_server.GET_FQDN_SERVICE_URL] = 'someurl'
    get_ambari_properties_mock.return_value = p
    
    u = MagicMock()
    host = 'host1.domain.com'
    u.read.return_value = host
    url_open_mock.return_value = u
    
    fqdn = ambari_server.get_fqdn()
    self.assertEqual(fqdn, host)
    
    #Failed to read FQDN from service, getting from socket
    u.reset_mock()
    u.side_effect = Exception("Failed to read FQDN from service")
    getfqdn_mock.return_value = host
    fqdn = ambari_server.get_fqdn()
    self.assertEqual(fqdn, host)
    

  @patch.object(ambari_server, "run_os_command")
  def test_get_cert_info(self, run_os_command_mock):
    # Error running openssl command
    path = 'path/to/certificate'
    run_os_command_mock.return_value = -1, None, None
    cert_info = ambari_server.get_cert_info(path)
    self.assertEqual(cert_info, None)
    
    #Empty result of openssl command
    run_os_command_mock.return_value = 0, None, None
    cert_info = ambari_server.get_cert_info(path)
    self.assertEqual(cert_info, None)
    
    #Positive scenario
    notAfter = 'Jul  3 14:12:57 2014 GMT'
    notBefore = 'Jul  3 14:12:57 2013 GMT'
    attr1_key = 'A'
    attr1_value = 'foo'
    attr2_key = 'B'
    attr2_value = 'bar'
    attr3_key = 'CN'
    attr3_value = 'host.domain.com'
    subject_pattern = '/{attr1_key}={attr1_value}/{attr2_key}={attr2_value}/{attr3_key}={attr3_value}'
    subject = subject_pattern.format(attr1_key = attr1_key, attr1_value = attr1_value,
                                     attr2_key = attr2_key, attr2_value = attr2_value,
                                     attr3_key = attr3_key, attr3_value = attr3_value)
    out_pattern = """
notAfter={notAfter}
notBefore={notBefore}
subject={subject}
-----BEGIN CERTIFICATE-----
MIIFHjCCAwYCCQDpHKOBI+Lt0zANBgkqhkiG9w0BAQUFADBRMQswCQYDVQQGEwJV
...
5lqd8XxOGSYoMOf+70BLN2sB
-----END CERTIFICATE-----
    """
    out = out_pattern.format(notAfter = notAfter, notBefore = notBefore, subject = subject)
    run_os_command_mock.return_value = 0, out, None
    cert_info = ambari_server.get_cert_info(path)
    self.assertEqual(cert_info['notAfter'], notAfter)
    self.assertEqual(cert_info['notBefore'], notBefore)
    self.assertEqual(cert_info['subject'], subject)
    self.assertEqual(cert_info[attr1_key], attr1_value)
    self.assertEqual(cert_info[attr2_key], attr2_value)
    self.assertEqual(cert_info[attr3_key], attr3_value)

      

  @patch.object(ambari_server, "run_os_command")
  @patch("__builtin__.open")
  @patch("os.path.exists")
  def test_is_server_runing(self, os_path_exists_mock, open_mock,\
                            run_os_command_mock):
    os_path_exists_mock.return_value = True
    f = open_mock.return_value
    f.readline.return_value = "111"
    run_os_command_mock.return_value = 0, "", ""
    status, pid = ambari_server.is_server_runing()
    self.assertTrue(status)
    self.assertEqual(111, pid)
    os_path_exists_mock.return_value = False
    status, pid = ambari_server.is_server_runing()
    self.assertFalse(status)
  
  @patch.object(ambari_server, "install_jce_manualy")
  @patch("os.stat")
  @patch("os.path.isfile")
  @patch("os.path.exists")
  @patch.object(ambari_server, "track_jdk")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "write_property")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "get_JAVA_HOME")
  @patch.object(ambari_server, "get_ambari_properties")
  @patch("shutil.copyfile")
  def test_download_jdk(self, copyfile_mock, get_ambari_properties_mock, get_JAVA_HOME_mock,\
                        print_info_msg_mock, write_property_mock,\
                        run_os_command_mock, get_YN_input_mock, track_jdk_mock,
                        path_existsMock, path_isfileMock, statMock,\
                        install_jce_manualy_mock):
    args = MagicMock()
    args.java_home = "somewhere"
    path_existsMock.return_value = False
    get_JAVA_HOME_mock.return_value = False
    get_ambari_properties_mock.return_value = -1
    # Test case: ambari.properties not found
    try:
      ambari_server.download_jdk(args)
      self.fail("Should throw exception because of not found ambari.properties")
    except FatalException:
      # Expected
      self.assertTrue(get_ambari_properties_mock.called)
      pass
    # Test case: JDK already exists
    p = MagicMock()
    get_ambari_properties_mock.return_value = p
    p.__getitem__.return_value = "somewhere"
    get_JAVA_HOME_mock.return_value = True
    path_existsMock.return_value = True
    rcode = ambari_server.download_jdk(args)
    self.assertEqual(0, rcode)
    # Test case: java home setup
    get_JAVA_HOME_mock.return_value = False
    rcode = ambari_server.download_jdk(args)
    self.assertEqual(0, rcode)
    self.assertTrue(write_property_mock.called)
    # Test case: JDK file does not exist, property not defined
    path_existsMock.return_value = False
    p = MagicMock()
    get_ambari_properties_mock.return_value = p
    p.__getitem__.side_effect = KeyError("test exception")
    try:
      ambari_server.download_jdk(args)
      self.fail("Should throw exception")
    except FatalException:
      # Expected
      pass
    # Test case: JDK file does not exist, os command (curl) result does not
    # contain Content-Length
    p.__getitem__.return_value = "somewhere"
    p.__getitem__.side_effect = None
    path_existsMock.return_value = False
    run_os_command_mock.return_value = (0, "Wrong out", None)
    try:
      ambari_server.download_jdk(args)
      self.fail("Should throw exception")
    except FatalException:
      # Expected
      pass
    # Successful JDK download
    ambari_server.JDK_INSTALL_DIR = os.getcwd()
    get_YN_input_mock.return_value = True
    run_os_command_mock.return_value = (0, "Creating jdk-1.2/jre"
                                           "Content-Length: 32000\r\n"
                                           , None)
    statResult = MagicMock()
    statResult.st_size = 32000
    statMock.return_value = statResult
    rcode = ambari_server.download_jdk(args)
    self.assertEqual(0, rcode)
    # Test case: JDK file does not exist, jdk-location argument passed
    p.__getitem__.return_value = "somewhere"
    p.__getitem__.side_effect = None
    args.jdk_location = "/existing/jdk/file"
    path_existsMock.side_effect = [False, False, True, False, False, False]
    ambari_server.download_jdk(args)
    self.assertTrue(copyfile_mock.called)

    copyfile_mock.reset_mock()
    # Negative test case: JDK file does not exist, jdk-location argument
    # (non-accessible file) passed
    p.__getitem__.return_value = "somewhere"
    p.__getitem__.side_effect = None
    args.jdk_location = "/existing/jdk/file"
    path_existsMock.side_effect = [False, False, True, False, False, False]
    def copyfile_side_effect(s, d):
       raise Exception("TerribleException")
    copyfile_mock.side_effect = copyfile_side_effect
    try:
      ambari_server.download_jdk(args)
      self.fail("Should throw exception")
    except FatalException:
      # Expected
      self.assertTrue(copyfile_mock.called)
    copyfile_mock.reset_mock()
    # Test case: jdk is already installed, ensure that JCE check is not skipped
    p = MagicMock()
    get_ambari_properties_mock.return_value = p
    p.__getitem__.return_value = "somewhere"
    get_JAVA_HOME_mock.return_value = True
    path_existsMock.return_value = True
    install_jce_manualy_mock.return_value = 1
    with patch.object(ambari_server, "download_jce_policy") as download_jce_policy_mock:
      rcode = ambari_server.download_jdk(args)
      self.assertTrue(download_jce_policy_mock.called)



  @patch.object(ambari_server, "run_os_command")
  def test_get_postgre_status(self, run_os_command_mock):

    run_os_command_mock.return_value = (1, "running", None)
    result = ambari_server.get_postgre_status()
    self.assertEqual("running", result)

    run_os_command_mock.return_value = (1, "wrong", None)
    result = ambari_server.get_postgre_status()
    self.assertEqual(None, result)


  @patch("time.sleep")
  @patch("subprocess.Popen")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "get_postgre_status")
  def test_check_postgre_up(self, get_postgre_status_mock, run_os_command_mock,
                            popen_mock, sleep_mock):
    p = MagicMock()
    p.poll.return_value = 0
    popen_mock.return_value = p
    run_os_command_mock.return_value = (0, None, None)
    rcode = ambari_server.check_postgre_up()
    self.assertEqual(0, rcode)

    p.poll.return_value = 4
    get_postgre_status_mock.return_value = None
    rcode = ambari_server.check_postgre_up()
    self.assertEqual(4, rcode)



  @patch("platform.linux_distribution")
  @patch("platform.system")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "print_error_msg")
  @patch.object(ambari_server, "get_ambari_properties")
  @patch.object(ambari_server, "write_property")
  @patch.object(ambari_server, "get_conf_dir")
  def test_configure_os_settings(self, get_conf_dir_mock, write_property_mock, get_ambari_properties_mock,
                                 print_error_msg_mock, print_info_msg_mock,
                                 systemMock, distMock):
    get_ambari_properties_mock.return_value = -1
    rcode = ambari_server.configure_os_settings()
    self.assertEqual(-1, rcode)

    p = MagicMock()
    p[ambari_server.OS_TYPE_PROPERTY] = 'somevalue'
    get_ambari_properties_mock.return_value = p
    rcode = ambari_server.configure_os_settings()
    self.assertEqual(0, rcode)

    p.__getitem__.return_value = ""
    systemMock.return_value = "NonLinux"
    rcode = ambari_server.configure_os_settings()
    self.assertEqual(-1, rcode)

    systemMock.return_value = "Linux"
    distMock.return_value = ("CentOS", "6.3", None)
    rcode = ambari_server.configure_os_settings()
    self.assertEqual(0, rcode)
    self.assertTrue(write_property_mock.called)



  @patch("__builtin__.open")
  @patch.object(ambari_server, "Properties")
  @patch.object(ambari_server, "search_file")
  @patch.object(ambari_server, "get_conf_dir")
  def test_get_JAVA_HOME(self, get_conf_dir_mock, search_file_mock,
                         Properties_mock, openMock):
    openMock.side_effect = Exception("exception")
    result = ambari_server.get_JAVA_HOME()
    self.assertEqual(None, result)

    expected = os.path.dirname(__file__)
    p = MagicMock()
    p.__getitem__.return_value = expected
    openMock.side_effect = None
    Properties_mock.return_value = p
    result = ambari_server.get_JAVA_HOME()
    self.assertEqual(expected, result)

  def test_prompt_db_properties_default(self):
    args = MagicMock()
    ambari_server.load_default_db_properties(args)
    ambari_server.prompt_db_properties(args)
    self.assertEqual(args.database, "postgres")
    self.assertEqual(args.database_host, "localhost")
    self.assertEqual(args.database_name, "ambari")
    self.assertEqual(args.database_port, "5432")

  @patch.object(ambari_server, "setup_master_key")
  @patch.object(ambari_server, "read_password")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "get_YN_input")
  def test_prompt_db_properties_oracle_sname(self, gyni_mock, gvsi_mock, rp_mock, smk_mock):
    ambari_server.PROMPT_DATABASE_OPTIONS = True
    gyni_mock.return_value = True
    list_of_return_values= ["ambari-server", "ambari", "1", "1521", "localhost", "2"]
    def side_effect(*args, **kwargs):
      return list_of_return_values.pop()
    gvsi_mock.side_effect = side_effect
    rp_mock.return_value = "password"
    smk_mock.return_value = (None, False, True)

    args = MagicMock()
    ambari_server.load_default_db_properties(args)
    ambari_server.prompt_db_properties(args)
    self.assertEqual(args.database, "oracle")
    self.assertEqual(args.database_port, "1521")
    self.assertEqual(args.database_host, "localhost")
    self.assertEqual(args.database_name, "ambari")
    self.assertEqual(args.database_username, "ambari-server")
    self.assertEqual(args.sid_or_sname, "sname")

  @patch.object(ambari_server, "setup_master_key")
  @patch.object(ambari_server, "read_password")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "get_YN_input")
  def test_prompt_db_properties_oracle_sid(self, gyni_mock, gvsi_mock, rp_mock, smk_mock):
    ambari_server.PROMPT_DATABASE_OPTIONS = True
    gyni_mock.return_value = True
    list_of_return_values= ["ambari-server", "ambari", "2", "1521", "localhost", "2"]
    def side_effect(*args, **kwargs):
      return list_of_return_values.pop()
    gvsi_mock.side_effect = side_effect
    rp_mock.return_value = "password"
    smk_mock.return_value = (None, False, True)

    args = MagicMock()
    ambari_server.load_default_db_properties(args)
    ambari_server.prompt_db_properties(args)
    self.assertEqual(args.database, "oracle")
    self.assertEqual(args.database_port, "1521")
    self.assertEqual(args.database_host, "localhost")
    self.assertEqual(args.database_name, "ambari")
    self.assertEqual(args.database_username, "ambari-server")
    self.assertEqual(args.sid_or_sname, "sid")

  @patch.object(ambari_server, "setup_master_key")
  @patch.object(ambari_server, "read_password")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "get_YN_input")
  def test_prompt_db_properties_postgre_adv(self, gyni_mock, gvsi_mock, rp_mock, smk_mock):
    ambari_server.PROMPT_DATABASE_OPTIONS = True
    gyni_mock.return_value = True
    list_of_return_values= ["ambari-server", "ambari", "1"]
    def side_effect(*args, **kwargs):
      return list_of_return_values.pop()
    gvsi_mock.side_effect = side_effect
    rp_mock.return_value = "password"
    smk_mock.return_value = (None, False, True)

    args = MagicMock()
    ambari_server.load_default_db_properties(args)
    ambari_server.prompt_db_properties(args)
    self.assertEqual(args.database, "postgres")
    self.assertEqual(args.database_port, "5432")
    self.assertEqual(args.database_host, "localhost")
    self.assertEqual(args.database_name, "ambari")
    self.assertEqual(args.database_username, "ambari-server")
    self.assertEqual(args.sid_or_sname, "sname")

  @patch("glob.glob")
  @patch.object(ambari_server, "get_JAVA_HOME")
  def test_find_jdk(self, get_JAVA_HOME_mock, globMock):
    get_JAVA_HOME_mock.return_value = "somewhere"
    result = ambari_server.find_jdk()
    self.assertEqual("somewhere", result)

    get_JAVA_HOME_mock.return_value = None
    globMock.return_value = []
    result = ambari_server.find_jdk()
    self.assertEqual(None, result)

    globMock.return_value = ["one", "two"]
    result = ambari_server.find_jdk()
    self.assertNotEqual(None, result)

  @patch("os.path.exists")
  @patch.object(ambari_server, 'verify_setup_allowed')
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "configure_os_settings")
  @patch.object(ambari_server, "download_jdk")
  @patch.object(ambari_server, "configure_postgres")
  @patch.object(ambari_server, "setup_db")
  @patch.object(ambari_server, "check_postgre_up")
  @patch.object(ambari_server, "check_iptables")
  @patch.object(ambari_server, "check_ambari_user")
  @patch.object(ambari_server, "check_jdbc_drivers")
  @patch.object(ambari_server, "check_selinux")
  @patch.object(ambari_server, "setup_remote_db")
  @patch.object(ambari_server, "store_remote_properties")
  @patch.object(ambari_server, "is_local_database")
  @patch.object(ambari_server, "store_local_properties")
  @patch.object(ambari_server, "is_root")
  def test_setup(self, is_root_mock, store_local_properties_mock, is_local_database_mock, store_remote_properties_mock,
                 setup_remote_db_mock, check_selinux_mock, check_jdbc_drivers_mock, check_ambari_user_mock,
                 check_iptables_mock, check_postgre_up_mock, setup_db_mock, configure_postgres_mock,
                 download_jdk_mock, configure_os_settings_mock,get_YN_input,
                 verify_setup_allowed_method, exists_mock):
    args = MagicMock()
    failed = False
    get_YN_input.return_value = False
    verify_setup_allowed_method.return_value = 0
    exists_mock.return_value = False
    def reset_mocks():
      is_root_mock.reset_mock()
      store_local_properties_mock.reset_mock()
      store_remote_properties_mock.reset_mock()
      is_local_database_mock.reset_mock()
      setup_remote_db_mock.reset_mock()
      check_selinux_mock.reset_mock()
      check_jdbc_drivers_mock.reset_mock()
      check_ambari_user_mock.reset_mock()
      check_iptables_mock.reset_mock()
      check_postgre_up_mock.reset_mock()
      setup_db_mock.reset_mock()
      configure_postgres_mock.reset_mock()
      download_jdk_mock.reset_mock()
      configure_os_settings_mock.reset_mock()
      pass


    # Testing call under non-root
    is_root_mock.return_value = False
    try:
      ambari_server.setup(args)
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing calls under root
    # remote case
    is_root_mock.return_value = True
    check_selinux_mock.return_value = 0
    check_ambari_user_mock.return_value = 0
    check_jdbc_drivers_mock.return_value = 0
    check_iptables_mock.return_value = (0, "other")
    check_postgre_up_mock.return_value = 0
    setup_db_mock.return_value = 0
    setup_remote_db_mock.return_value = 0
    is_local_database_mock.return_value = False
    configure_postgres_mock.return_value = 0
    download_jdk_mock.return_value = 0
    configure_os_settings_mock.return_value = 0
    store_remote_properties_mock.return_value = 0
    store_local_properties_mock.return_value = 0

    result = ambari_server.setup(args)

    self.assertEqual(None, result)
    self.assertTrue(check_ambari_user_mock.called)
    self.assertEquals(True, store_remote_properties_mock.called)
    self.assertEquals(False, store_local_properties_mock.called)


    #Local case
    reset_mocks()
    is_local_database_mock.return_value = True

    try:
      result = ambari_server.setup(args)
    except FatalException:
      self.fail("Setup should be successful")
    self.assertEqual(None, result)
    self.assertEquals(True, store_local_properties_mock.called)
    self.assertEquals(False, store_remote_properties_mock.called)

    #negative case
    reset_mocks()
    is_local_database_mock.return_value = False
    setup_remote_db_mock.return_value = -1

    try:
      result = ambari_server.setup(args)
      self.fail("Should throw exception")
    except NonFatalException as fe:
      self.assertTrue("cli was not found" in fe.reason)



  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "setup_db")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "configure_database_username_password")
  @patch.object(ambari_server, "parse_properties_file")
  @patch.object(ambari_server, "execute_remote_script")
  @patch.object(ambari_server, "is_root")
  def test_reset(self, is_root_mock, execute_remote_script_mock, parse_properties_file_mock, configure_database_username_password_mock,
                 run_os_command_mock, print_info_msg_mock,
                 setup_db_mock, get_YN_inputMock):

    parse_properties_file_mock.return_value = 0
    args = MagicMock()
    args.persistence_type = "local"
    get_YN_inputMock.return_value = False

    # Testing call under non-root
    is_root_mock.return_value = False
    try:
      ambari_server.reset(args)
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing calls under root
    is_root_mock.return_value = True
    try:
      ambari_server.reset(args)
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertFalse("root-level" in fe.reason)
      pass

    get_YN_inputMock.return_value = True
    run_os_command_mock.return_value = (1, None, None)
    try:
      ambari_server.reset(args)
      self.fail("Should throw exception")
    except FatalException:
      # Expected
      pass

    run_os_command_mock.return_value = (0, None, None)
    ambari_server.reset(args)
    self.assertTrue(setup_db_mock.called)
    
    #remote db case
    args.persistence_type = "remote"
    execute_remote_script_mock.return_value=(0, None, None)
    rcode = ambari_server.reset(args)
    self.assertEqual(None, rcode)
    self.assertTrue(execute_remote_script_mock.called)


  @patch.object(ambari_server, "setup_db")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "parse_properties_file")
  @patch.object(ambari_server, "is_root")
  def test_silent_reset(self, is_root_mock, parse_properties_file_mock,
                 run_os_command_mock, print_info_msg_mock,
                 setup_db_mock):
    is_root_mock.return_value = True

    args = MagicMock()
    ambari_server.SILENT = True
    self.assertTrue(ambari_server.SILENT)
    run_os_command_mock.return_value = (0, None, None)

    def signal_handler(signum, frame):
       self.fail("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(5)
    rcode = ambari_server.reset(args)
    signal.alarm(0)
    self.assertEqual(None, rcode)
    self.assertTrue(setup_db_mock.called)

  @patch("os.chown")
  @patch("pwd.getpwnam")
  @patch.object(ambari_server, 'get_master_key_location')
  @patch.object(ambari_server, 'save_master_key')
  @patch('os.chmod', autospec=True)
  @patch.object(ambari_server, 'get_validated_string_input')
  @patch("os.environ")
  @patch.object(ambari_server, "get_ambari_properties")
  @patch("os.kill")
  @patch("os.path.exists")
  @patch("__builtin__.open")
  @patch("subprocess.Popen")
  @patch.object(ambari_server, "print_info_msg")
  @patch.object(ambari_server, "search_file")
  @patch.object(ambari_server, "find_jdk")
  @patch.object(ambari_server, "print_error_msg")
  @patch.object(ambari_server, "check_postgre_up")
  @patch.object(ambari_server, "check_iptables")
  @patch.object(ambari_server, "parse_properties_file")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "is_root")
  @patch("getpass.getuser")
  @patch("os.chdir")
  def test_start(self, chdir_mock, getuser_mock, is_root_mock, read_ambari_user_mock,
                 parse_properties_file_mock, check_iptables_mock, check_postgre_up_mock,
                 print_error_msg_mock, find_jdk_mock, search_file_mock,
                 print_info_msg_mock, popenMock, openMock, pexistsMock,
                 killMock, get_ambari_properties_mock, os_environ_mock,
                 get_validated_string_input_method, os_chmod_method,
                 save_master_key_method, get_master_key_location_method,
                 getpwnam_mock, os_chown_mock):
    args = MagicMock()

    f = MagicMock()
    f.readline.return_value = 42
    openMock.return_value = f

    p = get_ambari_properties_mock.return_value
    p.get_property.return_value = 'False'
    search_file_mock.return_value = None
    pw = MagicMock()
    pw.setattr('pw_uid', 0)
    pw.setattr('pw_gid', 0)
    getpwnam_mock.return_value = pw
    os_chown_mock.return_value = None
    # Checking "server is running"
    pexistsMock.return_value = True
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'Server is running'")
    except FatalException:
      # Expected
      pass
    self.assertTrue(killMock.called)

    killMock.reset_mock()
    parse_properties_file_mock.reset_mock()

    pexistsMock.return_value = False

    # Checking situation when ambari user is not set up
    read_ambari_user_mock.return_value = None
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'Can not detect a system user for Ambari'")
    except FatalException as e:
      # Expected
      self.assertTrue('Unable to detect a system user for Ambari Server.' in e.reason)

    parse_properties_file_mock.reset_mock()

    # Checking start from non-root when current user is not the same as a
    # custom user
    read_ambari_user_mock.return_value = "dummy-user"
    getuser_mock.return_value = "non_custom_user"
    is_root_mock.return_value = False
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'Can not start ambari-server as user...'")
    except FatalException as e:
      # Expected
      self.assertTrue('Unable to start Ambari Server as user' in e.reason)
      self.assertFalse(parse_properties_file_mock.called)

    parse_properties_file_mock.reset_mock()

    # Checking "jdk not found"
    is_root_mock.return_value = True
    find_jdk_mock.return_value = None
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'No JDK found'")
    except FatalException as e:
      # Expected
      self.assertTrue('No JDK found' in e.reason)

    find_jdk_mock.return_value = "somewhere"

    parse_properties_file_mock.reset_mock()

    ## Testing workflow under root
    is_root_mock.return_value = True

    # Remote DB
    args.persistence_type="remote"
    check_iptables_mock.return_value = (0, None)
    try:
      ambari_server.start(args)
    except FatalException as e:
      # Ignored
      pass

    self.assertFalse('Unable to start PostgreSQL server' in e.reason)
    self.assertFalse(check_postgre_up_mock.called)

    check_postgre_up_mock.reset_mock()
    parse_properties_file_mock.reset_mock()

    # Local DB
    args.persistence_type="local"

    # case: postgres failed to start
    check_postgre_up_mock.return_value = 1
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'Unable to start PostgreSQL server'")
    except FatalException as e:
      # Expected
      self.assertTrue('Unable to start PostgreSQL server' in e.reason)
      self.assertTrue(check_postgre_up_mock.called)

    parse_properties_file_mock.reset_mock()

    # case: iptables failed to stop
    check_postgre_up_mock.return_value = 0
    check_iptables_mock.return_value = (1, ambari_server.IP_TBLS_ENABLED)
    try:
      ambari_server.start(args)
      self.fail("Should fail with 'Failed to stop iptables'")
    except FatalException as e:
      # Expected
      self.assertTrue('Failed to stop iptables' in e.reason)

    parse_properties_file_mock.reset_mock()

    check_iptables_mock.return_value = (0, None)
    # Case: custom user is "root"
    read_ambari_user_mock.return_value = "root"
    ambari_server.start(args)
    self.assertTrue(popenMock.called)
    popen_arg = popenMock.call_args[0][0]
    self.assertTrue(popen_arg[0] == "/bin/sh")
    popenMock.reset_mock()

    parse_properties_file_mock.reset_mock()

    # Case: custom user is  not "root"
    read_ambari_user_mock.return_value = "not-root-user"
    ambari_server.start(args)
    self.assertTrue(chdir_mock.called)
    self.assertTrue(popenMock.called)
    popen_arg = popenMock.call_args[0][0]
    self.assertTrue(popen_arg[0] == "/bin/su")
    check_postgre_up_mock.reset_mock()

    popenMock.reset_mock()
    parse_properties_file_mock.reset_mock()

    ## Testing workflow under non-root
    is_root_mock.return_value = False
    read_ambari_user_mock.return_value = "not-root-user"
    getuser_mock.return_value = read_ambari_user_mock.return_value

    parse_properties_file_mock.reset_mock()

    # Local DB
    args.persistence_type="local"

    ambari_server.start(args)

    self.assertFalse(check_postgre_up_mock.called)

    parse_properties_file_mock.reset_mock()

    # Remote DB
    args.persistence_type="remote"

    ambari_server.start(args)

    self.assertFalse(check_postgre_up_mock.called)

    parse_properties_file_mock.reset_mock()

    # Checking call
    check_iptables_mock.reset_mock()
    check_iptables_mock.return_value = (0, None)
    ambari_server.start(args)
    self.assertTrue(popenMock.called)
    popen_arg = popenMock.call_args[0][0]
    self.assertTrue(popen_arg[0] == "/bin/sh")
    self.assertFalse(check_iptables_mock.called)

    parse_properties_file_mock.reset_mock()

    # Test start under wrong user
    read_ambari_user_mock.return_value = "not-root-user"
    getuser_mock.return_value = "non_custom_user"
    try:
      ambari_server.start(args)
      self.fail("Can not start ambari-server as user non_custom_user.")
    except FatalException as e:
      # Expected
      self.assertTrue('Unable to start Ambari Server as user' in e.reason)

    parse_properties_file_mock.reset_mock()

    # Check environ master key is set
    popenMock.reset_mock()
    os_environ_mock.copy.return_value = {"a" : "b",
        ambari_server.SECURITY_KEY_ENV_VAR_NAME : "masterkey"}
    args.persistence_type="local"
    read_ambari_user_mock.return_value = "root"
    is_root_mock.return_value = True

    ambari_server.start(args)

    self.assertFalse(get_validated_string_input_method.called)
    self.assertFalse(save_master_key_method.called)
    popen_arg = popenMock.call_args[1]['env']
    self.assertEquals(os_environ_mock.copy.return_value, popen_arg)

    parse_properties_file_mock.reset_mock()

    # Check environ master key is not set
    popenMock.reset_mock()
    os_environ_mock.reset_mock()
    p.get_property.return_value = 'True'
    os_environ_mock.copy.return_value = {"a" : "b"}
    args.persistence_type="local"
    read_ambari_user_mock.return_value = "root"
    is_root_mock.return_value = True
    get_validated_string_input_method.return_value = "masterkey"
    os_chmod_method.return_value = None

    ambari_server.start(args)

    self.assertTrue(get_validated_string_input_method.called)
    self.assertTrue(save_master_key_method.called)
    popen_arg = popenMock.call_args[1]['env']
    self.assertEquals(os_environ_mock.copy.return_value, popen_arg)


  @patch("__builtin__.open")
  @patch("os.path.exists")
  @patch("os.remove")
  @patch("os.killpg")
  @patch("os.getpgid")
  @patch.object(ambari_server, "print_info_msg")
  def test_stop(self, print_info_msg_mock, gpidMock, removeMock,
                killMock, pexistsMock, openMock):
    pexistsMock.return_value = True
    f = MagicMock()
    f.readline.return_value = "42"
    openMock.return_value = f

    ambari_server.stop(None)

    self.assertTrue(f.readline.called)
    self.assertTrue(killMock.called)
    self.assertTrue(killMock.called)
    self.assertTrue(f.close.called)
    self.assertTrue(removeMock.called)


  @patch.object(ambari_server, "configure_database_username_password")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "is_root")
  def test_upgrade_stack(self, is_root_mock, run_os_command_mock,
                         configure_postgres_username_password_mock):
    args = MagicMock()

     # Testing call under non-root
    is_root_mock.return_value = False
    try:
      ambari_server.upgrade_stack(args, 'HDP-2.0')
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing calls under root
    is_root_mock.return_value = True
    run_os_command_mock.return_value = (0, '', '')
    ambari_server.upgrade_stack(args, 'HDP-2.0')

    self.assertTrue(configure_postgres_username_password_mock.called)
    self.assertTrue(run_os_command_mock.called)


  @patch.object(ambari_server, "adjust_directory_permissions")
  @patch.object(ambari_server, "print_warning_msg")
  @patch.object(ambari_server, "read_ambari_user")
  @patch.object(ambari_server, "check_db_consistency")
  @patch.object(ambari_server, "execute_db_script")
  @patch.object(ambari_server, "check_postgre_up")
  @patch.object(ambari_server, "update_ambari_properties")
  @patch.object(ambari_server, "parse_properties_file")
  @patch.object(ambari_server, "is_root")
  def test_upgrade(self, is_root_mock, parse_properties_file_mock, update_ambari_properties_mock,
                   check_postgre_up_mock, execute_db_script_mock,
                   check_db_consistency_mock, read_ambari_user_mock,
                   print_warning_msg_mock, adjust_directory_permissions_mock):

    args = MagicMock()
    args.upgrade_script_file = "/var/lib/"\
      "ambari-server/resources/upgrade/ddl/"\
      "Ambari-DDL-Postgres-UPGRADE-1.3.0.sql"
    update_ambari_properties_mock.return_value = 0
    check_postgre_up_mock.return_value = 0
    execute_db_script_mock.return_value = 0
    check_db_consistency_mock.return_value = 0

    # Testing call under non-root
    is_root_mock.return_value = False
    try:
      ambari_server.upgrade(args)
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing calls under root
    is_root_mock.return_value = True

    # Testing with undefined custom user
    read_ambari_user_mock.return_value = None
    ambari_server.upgrade(args)
    self.assertTrue(print_warning_msg_mock.called)
    warning_args = print_warning_msg_mock.call_args[0][0]
    self.assertTrue("custom ambari user" in warning_args)

    # Testing with defined custom user
    read_ambari_user_mock.return_value = "ambari-custom-user"
    ambari_server.upgrade(args)
    self.assertTrue(adjust_directory_permissions_mock.called)


  def test_print_info_msg(self):
    out = StringIO.StringIO()
    sys.stdout = out

    ambari_server.VERBOSE = True
    ambari_server.print_info_msg("msg")
    self.assertNotEqual("", out.getvalue())

    sys.stdout = sys.__stdout__



  def test_print_error_msg(self):

    out = StringIO.StringIO()
    sys.stdout = out

    ambari_server.VERBOSE = True
    ambari_server.print_error_msg("msg")
    self.assertNotEqual("", out.getvalue())

    sys.stdout = sys.__stdout__



  def test_print_warning_msg(self):

    out = StringIO.StringIO()
    sys.stdout = out

    ambari_server.VERBOSE = True
    ambari_server.print_warning_msg("msg")
    self.assertNotEqual("", out.getvalue())

    sys.stdout = sys.__stdout__



  @patch.object(ambari_server, "get_choice_string_input")
  def test_get_YN_input(self, get_choice_string_input_mock):

    ambari_server.get_YN_input("prompt", "default")
    self.assertTrue(get_choice_string_input_mock.called)
    self.assertEqual(4, len(get_choice_string_input_mock.call_args_list[0][0]))



  def test_load_default_db_properties(self):
    args = MagicMock()

    ambari_server.load_default_db_properties(args)

    self.assertEquals(args.database, "postgres")
    self.assertEquals(args.database_host, "localhost")
    self.assertEquals(args.database_port, "5432")
    self.assertEquals(args.database_name, "ambari")
    self.assertEquals(args.database_username, "ambari")
    self.assertEquals(args.database_password, "bigdata")

    args = MagicMock()
    ambari_server.DATABASE_INDEX=1
    ambari_server.load_default_db_properties(args)
    self.assertEquals(args.database, "oracle")
    self.assertEquals(args.database_port, "1521")

    failed = False
    args = MagicMock()
    ambari_server.DATABASE_INDEX=2
    try:
      ambari_server.load_default_db_properties(args)
    except:
      failed = True
    self.assertTrue(failed)

  pass

  @patch.object(ambari_server, 'setup')
  def test_main_db_options(self, setup_mock):
    base_args = ["ambari-server.py", "setup"]
    db_args = ["--database", "postgres", "--databasehost", "somehost.net", "--databaseport", "12345",
               "--databasename", "ambari", "--databaseusername", "ambari", "--databasepassword", "bigdata"]

    #test no args
    failed = False
    sys.argv = list(base_args)


    try:
      ambari_server.main()
    except SystemExit:
      failed = True
      pass


    self.assertFalse(failed)
    self.assertTrue(setup_mock.called)

    setup_mock.reset_mock()

    #test full args
    sys.argv = list(base_args)
    sys.argv.extend(db_args)

    try:
      ambari_server.main()
    except SystemExit:
      failed = True
      pass

    self.assertTrue(ambari_server.PROMPT_DATABASE_OPTIONS)
    self.assertFalse(failed)
    self.assertTrue(setup_mock.called)

    setup_mock.reset_mock()

    #test not full args
    sys.argv = list(base_args)
    sys.argv.extend(["--database", "postgres"])

    try:
      ambari_server.main()
    except SystemExit:
      failed = True
      pass

    self.assertFalse(setup_mock.called)
    self.assertTrue(failed)

    setup_mock.reset_mock()

    #test wrong database
    failed = False
    sys.argv = list(base_args)
    sys.argv.extend(["--database", "unknown"])
    sys.argv.extend(db_args[2:])

    try:
      ambari_server.main()
    except SystemExit:
      failed = True
      pass

    self.assertTrue(failed)
    self.assertFalse(setup_mock.called)

    setup_mock.reset_mock()

    #test wrong port check
    failed = False
    sys.argv = list(base_args)
    sys.argv.extend(["--databaseport", "unknown"])
    sys.argv.extend(db_args[:4])
    sys.argv.extend(db_args[6:])

    try:
      ambari_server.main()
    except SystemExit:
      failed = True
      pass

    self.assertTrue(failed)
    self.assertFalse(setup_mock.called)

    setup_mock.reset_mock()
    pass



  @patch.object(ambari_server, "load_default_db_properties")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "get_validated_string_input")
  @patch.object(ambari_server, "setup_master_key")
  @patch.object(ambari_server, "configure_database_password")
  def test_prompt_db_properties(self, configure_database_password_mock, setup_master_key_mock,
                                get_validated_string_input_mock, get_YN_input_mock, load_default_db_properties_mock):
    args = MagicMock()

    #test not prompt
    ambari_server.PROMPT_DATABASE_OPTIONS = False
    ambari_server.prompt_db_properties(args)


    self.assertFalse(load_default_db_properties_mock.called)
    self.assertFalse(get_validated_string_input_mock.called)
    self.assertFalse(get_YN_input_mock.called)

    load_default_db_properties_mock.reset_mock()
    get_validated_string_input_mock.reset_mock()
    get_YN_input_mock.reset_mock()

    #test prompt
    get_YN_input_mock.return_value = False

    ambari_server.PROMPT_DATABASE_OPTIONS = True
    ambari_server.prompt_db_properties(args)
    self.assertTrue(get_YN_input_mock.called)
    self.assertFalse(get_validated_string_input_mock.called)
    self.assertTrue(load_default_db_properties_mock.called)

    load_default_db_properties_mock.reset_mock()
    get_validated_string_input_mock.reset_mock()
    get_YN_input_mock.reset_mock()

    #test prompt advanced
    get_YN_input_mock.return_value = True

    ambari_server.PROMPT_DATABASE_OPTIONS = True
    setup_master_key_mock.return_value = (None, False, True)
    configure_database_password_mock.return_value = ("test", None)

    ambari_server.prompt_db_properties(args)
    self.assertTrue(get_YN_input_mock.called)
    self.assertTrue(get_validated_string_input_mock.called)
    self.assertTrue(load_default_db_properties_mock.called)

    self.assertEquals(args.database, "postgres")

    load_default_db_properties_mock.reset_mock()
    get_validated_string_input_mock.reset_mock()
    get_YN_input_mock.reset_mock()



  pass

  @patch.object(ambari_server, "get_db_cli_tool")
  @patch.object(ambari_server, "run_in_shell")
  def test_execute_remote_script(self, run_in_shell_mock, get_db_cli_tool_mock):
    args = MagicMock()
    script = "script"


    #success
    run_in_shell_mock.return_value=(0, None, None)
    get_db_cli_tool_mock.return_value="tool"
    args.database = "postgres"
    args.database_password = "some_password"

    retcode, out, err = ambari_server.execute_remote_script(args, script)
    self.assertEquals(retcode, 0)
    self.assertTrue(get_db_cli_tool_mock.called)
    self.assertTrue(run_in_shell_mock.called)

    #fail no cli tool
    get_db_cli_tool_mock.return_value = None
    get_db_cli_tool_mock.called = False
    run_in_shell_mock.called = False

    retcode, out, err = ambari_server.execute_remote_script(args, script)
    self.assertEquals(retcode, -1)
    self.assertTrue(get_db_cli_tool_mock.called)
    self.assertFalse(run_in_shell_mock.called)

    #fail execute
    errcode = 1
    get_db_cli_tool_mock.return_value = "tool"
    run_in_shell_mock.return_value=(errcode, None, None)
    get_db_cli_tool_mock.called = False
    run_in_shell_mock.called = False

    retcode, out, err = ambari_server.execute_remote_script(args, script)
    self.assertEquals(retcode, errcode)
    self.assertTrue(get_db_cli_tool_mock.called)
    self.assertTrue(run_in_shell_mock.called)

    #fail wrong database - case should be completely impossible
    get_db_cli_tool_mock.return_value = "tool"
    run_in_shell_mock.return_value=(0, None, None)
    get_db_cli_tool_mock.called = False
    run_in_shell_mock.called = False
    args.database = "unknown"

    retcode, out, err = ambari_server.execute_remote_script(args, script)
    self.assertEquals(retcode, -2)
    self.assertTrue(get_db_cli_tool_mock.called)
    self.assertFalse(run_in_shell_mock.called)
    pass

  @patch.object(ambari_server, "get_conf_dir")
  def test_update_ambari_properties(self, get_conf_dir_mock):

    properties = ["server.jdbc.user.name=ambari-server\n",
      "server.jdbc.user.passwd=/etc/ambari-server/conf/password.dat\n",
      "java.home=/usr/jdk64/jdk1.6.0_31\n",
      "server.os_type=redhat6\n",
      "ambari-server.user=ambari\n",
      "agent.fqdn.service.url=URL\n"]

    NEW_PROPERTY = 'some_new_property=some_value\n'
    CHANGED_VALUE_PROPERTY = 'server.os_type=should_not_overwrite_value\n'

    get_conf_dir_mock.return_value = '/etc/ambari-server/conf'

    (tf1, fn1) = tempfile.mkstemp()
    (tf2, fn2) = tempfile.mkstemp()
    ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE = fn1
    ambari_server.AMBARI_PROPERTIES_FILE = fn2

    with open(ambari_server.AMBARI_PROPERTIES_FILE, "w") as f:
      f.write(NEW_PROPERTY)
      f.write(CHANGED_VALUE_PROPERTY)

    with open(ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE, 'w') as f:
      for line in properties:
        f.write(line)

    #Call tested method
    ambari_server.update_ambari_properties()

    timestamp = datetime.datetime.now()
    #RPMSAVE_FILE wasn't found
    self.assertFalse(os.path.exists(ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE))
    #Renamed RPMSAVE_FILE exists
    self.assertTrue(os.path.exists(ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE
                                   + '.' + timestamp.strftime('%Y%m%d%H%M%S')))

    with open(ambari_server.AMBARI_PROPERTIES_FILE, 'r') as f:
      ambari_properties_content = f.readlines()

    for line in properties:
      if (line == "agent.fqdn.service.url=URL\n"):
        if (not ambari_server.GET_FQDN_SERVICE_URL+"=URL\n" in ambari_properties_content) and (line in ambari_properties_content):
          self.fail()
      else:
        if not line in ambari_properties_content:
          self.fail()



    if not NEW_PROPERTY in ambari_properties_content:
      self.fail()

    if CHANGED_VALUE_PROPERTY in ambari_properties_content:
      self.fail()

    # Command should not fail if *.rpmsave file is missing
    result = ambari_server.update_ambari_properties()
    self.assertEquals(result, 0)

    os.unlink(fn2)

    #if ambari.properties file is absent then "ambari-server upgrade" should
    # fail
    (tf, fn) = tempfile.mkstemp()
    ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE = fn

    result = ambari_server.update_ambari_properties()
    self.assertNotEquals(result, 0)

  @patch.object(ambari_server.Properties, '__init__')
  @patch.object(ambari_server, 'search_file')
  def test_update_ambari_properties_negative_case(self, search_file_mock, properties_mock):
    search_file_mock.return_value = None
    #Call tested method
    self.assertEquals(0, ambari_server.update_ambari_properties())
    self.assertFalse(properties_mock.called)

    search_file_mock.return_value = False
    #Call tested method
    self.assertEquals(0, ambari_server.update_ambari_properties())
    self.assertFalse(properties_mock.called)

    search_file_mock.return_value = ''
    #Call tested method
    self.assertEquals(0, ambari_server.update_ambari_properties())
    self.assertFalse(properties_mock.called)


  @patch.object(ambari_server, "get_conf_dir")
  def test_update_ambari_properties_without_user_property(self, get_conf_dir_mock):
    '''
      Checks: update_ambari_properties call should add ambari-server.user property if
      it's absent
    '''
    properties = ["server.jdbc.user.name=ambari-server\n",
                  "server.jdbc.user.passwd=/etc/ambari-server/conf/password.dat\n",
                  "java.home=/usr/jdk64/jdk1.6.0_31\n",
                  "server.os_type=redhat6\n"]

    get_conf_dir_mock.return_value = '/etc/ambari-server/conf'

    (tf1, fn1) = tempfile.mkstemp()
    (tf2, fn2) = tempfile.mkstemp()
    ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE = fn1
    ambari_server.AMBARI_PROPERTIES_FILE = fn2

    with open(ambari_server.AMBARI_PROPERTIES_RPMSAVE_FILE, 'w') as f:
      for line in properties:
        f.write(line)

    #Call tested method
    ambari_server.update_ambari_properties()

    ambari_properties =  ambari_server.Properties()
    ambari_properties.load(open(fn2))

    self.assertTrue(ambari_server.NR_USER_PROPERTY in ambari_properties.keys())
    value = ambari_properties[ambari_server.NR_USER_PROPERTY]
    self.assertEqual(value, "root")

    os.unlink(fn2)


  @patch.object(ambari_server, 'verify_setup_allowed')
  @patch("sys.exit")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "get_db_cli_tool")
  @patch.object(ambari_server, "store_remote_properties")
  @patch.object(ambari_server, "is_local_database")
  @patch.object(ambari_server, "check_iptables")
  @patch.object(ambari_server, "check_jdbc_drivers")
  @patch.object(ambari_server, "is_root")
  @patch.object(ambari_server, "check_ambari_user")
  @patch.object(ambari_server, "download_jdk")
  @patch.object(ambari_server, "configure_os_settings")
  @patch('__builtin__.raw_input')
  def test_setup_remote_db_wo_client(self,raw_input, configure_os_settings_mock,
        download_jdk_mock, check_ambari_user_mock, is_root_mock,
        check_jdbc_drivers_mock, check_iptables_mock, is_local_db_mock,
        store_remote_properties_mock, get_db_cli_tool_mock, get_YN_input,
        exit_mock, verify_setup_allowed_method):
    args = MagicMock()
    raw_input.return_value =""
    is_root_mock.return_value = True
    is_local_db_mock.return_value = False
    get_YN_input.return_value = False
    check_iptables_mock.return_value = (0, "other")
    store_remote_properties_mock.return_value = 0
    get_db_cli_tool_mock.return_value = None
    check_jdbc_drivers_mock.return_value=0
    check_ambari_user_mock.return_value = 0
    download_jdk_mock.return_value = 0
    configure_os_settings_mock.return_value = 0
    verify_setup_allowed_method.return_value = 0

    try:
      ambari_server.setup(args)
      self.fail("Should throw exception")
    except NonFatalException as fe:
      # Expected
      self.assertTrue("The cli was not found" in fe.reason)

  @patch.object(ambari_server, 'verify_setup_allowed')
  @patch("sys.exit")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "get_db_cli_tool")
  @patch.object(ambari_server, "is_local_database")
  @patch.object(ambari_server, "check_iptables")
  @patch.object(ambari_server, "check_jdbc_drivers")
  @patch.object(ambari_server, "is_root")
  @patch.object(ambari_server, "check_ambari_user")
  @patch.object(ambari_server, "download_jdk")
  @patch.object(ambari_server, "configure_os_settings")
  @patch('__builtin__.raw_input')
  def test_store_remote_properties(self,raw_input, configure_os_settings_mock,
        download_jdk_mock, check_ambari_user_mock, is_root_mock,
        check_jdbc_drivers_mock, check_iptables_mock, is_local_db_mock,
        get_db_cli_tool_mock, get_YN_input, exit_mock, verify_setup_allowed_method):

    raw_input.return_value =""
    is_root_mock.return_value = True
    is_local_db_mock.return_value = False
    get_YN_input.return_value = False
    check_iptables_mock.return_value = (0, "other")
    get_db_cli_tool_mock.return_value = None
    check_jdbc_drivers_mock.return_value=0
    check_ambari_user_mock.return_value = 0
    download_jdk_mock.return_value = 0
    configure_os_settings_mock.return_value = 0
    verify_setup_allowed_method.return_value = 0

    import optparse

    args = optparse.Values()
    args.database = "oracle"
    args.database_host = "localhost"
    args.database_port = "1234"
    args.database_name = "ambari"
    args.sid_or_sname = "foo"
    args.database_username = "foo"
    args.database_password = "foo"

    tempdir = tempfile.gettempdir()

    prop_file = os.path.join(tempdir, "ambari.properties")

    with open(prop_file, "w") as f:
      f.write("dummy=dummy")
    f.close()

    os.environ[ambari_server.AMBARI_CONF_VAR] = tempdir
    ambari_server.DATABASE_INDEX = 1

    ambari_server.store_remote_properties(args)

    properties = ambari_server.get_ambari_properties()

    found = False
    for n in properties.propertyNames():
      if not found and n.startswith("server.jdbc.properties"):
        found = True

    ambari_server.DATABASE_INDEX = 0
    del os.environ[ambari_server.AMBARI_CONF_VAR]
    os.remove(prop_file)

    self.assertTrue(found)

  @patch.object(ambari_server, "parse_properties_file")
  @patch.object(ambari_server, "get_db_cli_tool")
  @patch.object(ambari_server, "print_error_msg")
  @patch.object(ambari_server, "get_YN_input")
  @patch.object(ambari_server, "setup_db")
  @patch.object(ambari_server, "run_os_command")
  @patch.object(ambari_server, "is_root")
  def test_reset_remote_db_wo_client(self, is_root_mock, run_os_command_mock, setup_db_mock,
                                     get_YN_inputMock, print_error_msg_mock, get_db_cli_tool_mock, parse_properties_file_mock):
    args = MagicMock()
    get_YN_inputMock.return_value = True
    run_os_command_mock.return_value = (0, None, None)
    args.persistence_type="remote"
    get_db_cli_tool_mock.return_value = None
    is_root_mock.return_value = True
    try:
      ambari_server.reset(args)
      self.fail("Should throw exception")
    except NonFatalException as fe:
      # Expected
      self.assertTrue("Client wasn't found" in fe.reason)
      pass

  @patch.object(ambari_server, "find_properties_file")
  def test_get_ambari_properties(self, find_properties_file_mock):

    find_properties_file_mock.return_value = None
    rcode = ambari_server.get_ambari_properties()
    self.assertEqual(rcode, -1)
  
    tf1 = tempfile.NamedTemporaryFile()
    find_properties_file_mock.return_value = tf1.name
    prop_name='name'
    prop_value='val'
    
    with open(tf1.name, 'w') as fout:
      fout.write(prop_name + '=' + prop_value)
    fout.close()

    properties = ambari_server.get_ambari_properties()

    self.assertEqual(properties[prop_name], prop_value)


  @patch.object(ambari_server, "get_ambari_properties")
  @patch.object(ambari_server, "find_jdbc_driver")
  @patch.object(ambari_server, "copy_files")
  @patch.object(ambari_server, "print_error_msg")
  @patch.object(ambari_server, "print_warning_msg")
  @patch('__builtin__.raw_input')
  @patch("sys.exit")
  def check_jdbc_drivers(self, exit_mock, raw_input_mock, print_warning_msg, print_error_msg_mock, copy_files_mock,
                              find_jdbc_driver_mock, get_ambari_properties_mock):

    out = StringIO.StringIO()
    sys.stdout = out

    args = MagicMock()

    # Check positive scenario
    drivers_list = ['driver_file']
    resources_dir = '/tmp'

    get_ambari_properties_mock.return_value = {ambari_server.RESOURCES_DIR_PROPERTY : resources_dir}
    find_jdbc_driver_mock.return_value = drivers_list

    args.database = "oracle"

    rcode = ambari_server.check_jdbc_drivers(args)

    self.assertEqual(0, rcode)
    copy_files_mock.assert_called_with(drivers_list, resources_dir)

    # Check negative scenarios
    # Silent option, no drivers
    ambari_server.SILENT = True

    find_jdbc_driver_mock.return_value = -1

    rcode = ambari_server.check_jdbc_drivers(args)

    self.assertTrue(print_error_msg_mock.called)
    self.assertTrue(exit_mock.called)

    # Non-Silent option, no drivers
    ambari_server.SILENT = False

    find_jdbc_driver_mock.return_value = -1

    rcode = ambari_server.check_jdbc_drivers(args)

    self.assertTrue(exit_mock.called)
    self.assertTrue(print_error_msg_mock.called)

    # Non-Silent option, no drivers at first ask, present drivers after that

    find_jdbc_driver_mock.side_effect = [-1, drivers_list]

    rcode = ambari_server.check_jdbc_drivers(args)

    self.assertEqual(0, rcode)
    copy_files_mock.assert_called_with(drivers_list, resources_dir)

    # Non-Silent option, no drivers at first ask, present drivers after that
    find_jdbc_driver_mock.reset()
    find_jdbc_driver_mock.side_effect = [-1, -1]

    rcode = ambari_server.check_jdbc_drivers(args)

    self.assertTrue(exit_mock.called)
    self.assertTrue(print_error_msg_mock.called)


    sys.stdout = sys.__stdout__


  @patch.object(ambari_server, "find_properties_file")
  def test_get_ambari_properties(self, find_properties_file):

    find_properties_file.return_value = None
    rcode = ambari_server.get_ambari_properties()
    self.assertEqual(rcode, -1)

    tf1 = tempfile.NamedTemporaryFile()
    find_properties_file.return_value = tf1.name
    prop_name='name'
    prop_value='val'

    with open(tf1.name, 'w') as fout:
      fout.write(prop_name + '=' + prop_value)
    fout.close()

    properties = ambari_server.get_ambari_properties()

    self.assertEqual(properties[prop_name], prop_value)
    self.assertEqual(properties.fileName, os.path.abspath(tf1.name))

    sys.stdout = sys.__stdout__

  
  @patch("os.path.exists")
  @patch("os.remove")
  @patch.object(ambari_server,"print_warning_msg")
  def test_remove_file(self, printWarningMsgMock, removeMock, pathExistsMock):
    def side_effect():
      raise Exception(-1, "Failed to delete!")
    
    removeMock.side_effect = side_effect
    pathExistsMock.return_value = 1
    
    res = ambari_server.remove_file("/someNonExsistantDir/filename")
    self.assertEquals(res,1)
    
    removeMock.side_effect = None
    res = ambari_server.remove_file("/someExsistantDir/filename")
    self.assertEquals(res, 0)
  
  @patch("shutil.copyfile")
  def test_copy_file(self, shutilCopyfileMock):
    def side_effect():
      raise Exception(-1, "Failed to copy!")
    
    shutilCopyfileMock.side_effect = side_effect
    
    try:
      ambari_server.copy_file("/tmp/psswd","/someNonExsistantDir/filename")
      self.fail("Exception on file not copied has not been thrown!")
    except FatalException:
      # Expected
      pass
    
    self.assertTrue(shutilCopyfileMock.called)
    
    
    shutilCopyfileMock.side_effect = None
    try:
      ambari_server.copy_file("/tmp/psswd","/root/psswd")
    except FatalException:
        self.fail("Exception on file copied should not be thrown!")
        
    self.assertTrue(shutilCopyfileMock.called)

  @patch.object(ambari_server, "get_ambari_properties")
  @patch.object(ambari_server, "find_jdbc_driver")
  @patch.object(ambari_server, "copy_files")
  @patch.object(ambari_server, "print_error_msg")
  @patch.object(ambari_server, "print_warning_msg")
  @patch('__builtin__.raw_input')
  def test_check_jdbc_drivers(self, raw_input_mock, print_warning_msg, print_error_msg_mock, copy_files_mock,
                              find_jdbc_driver_mock, get_ambari_properties_mock):

    out = StringIO.StringIO()
    sys.stdout = out

    args = MagicMock()
    
    # Check positive scenario
    drivers_list = ['driver_file']
    resources_dir = '/tmp'
    
    get_ambari_properties_mock.return_value = {ambari_server.RESOURCES_DIR_PROPERTY : resources_dir}
    find_jdbc_driver_mock.return_value = drivers_list
    copy_files_mock.return_value = 0
    
    args.database = "oracle"
    
    rcode = ambari_server.check_jdbc_drivers(args)
    
    self.assertEqual(0, rcode)
    copy_files_mock.assert_called_with(drivers_list, resources_dir)
    
    get_ambari_properties_mock.reset_mock()
    find_jdbc_driver_mock.reset_mock()
    copy_files_mock.reset_mock()
    print_error_msg_mock.reset_mock()
    print_warning_msg.reset_mock()
    raw_input_mock.reset_mock()
    
    
    
    # Check negative scenarios
    # Silent option, no drivers
    ambari_server.SILENT = True
    
    find_jdbc_driver_mock.return_value = -1
    
    failed = False
    
    try:
      rcode = ambari_server.check_jdbc_drivers(args)
    except FatalException:
      failed = True
    
    self.assertTrue(print_error_msg_mock.called)
    self.assertTrue(failed)
    
    get_ambari_properties_mock.reset_mock()
    find_jdbc_driver_mock.reset_mock()
    copy_files_mock.reset_mock()
    print_error_msg_mock.reset_mock()
    print_warning_msg.reset_mock()
    raw_input_mock.reset_mock()
    
    # Non-Silent option, no drivers
    ambari_server.SILENT = False
    
    find_jdbc_driver_mock.return_value = -1
    
    failed = False
    
    try:
      rcode = ambari_server.check_jdbc_drivers(args)
    except FatalException:
      failed = True

    self.assertTrue(failed)
    self.assertTrue(print_error_msg_mock.called)
    
    get_ambari_properties_mock.reset_mock()
    find_jdbc_driver_mock.reset_mock()
    copy_files_mock.reset_mock()
    print_error_msg_mock.reset_mock()
    print_warning_msg.reset_mock()
    raw_input_mock.reset_mock()
    
    # Non-Silent option, no drivers at first ask, present drivers after that
    
    find_jdbc_driver_mock.side_effect = [-1, drivers_list]
    
    rcode = ambari_server.check_jdbc_drivers(args)
    
    self.assertEqual(0, rcode)
    copy_files_mock.assert_called_with(drivers_list, resources_dir)
    
    get_ambari_properties_mock.reset_mock()
    find_jdbc_driver_mock.reset_mock()
    copy_files_mock.reset_mock()
    print_error_msg_mock.reset_mock()
    print_warning_msg.reset_mock()
    raw_input_mock.reset_mock()
    
    # Non-Silent option, no drivers at first ask, no drivers after that
    find_jdbc_driver_mock.side_effect = [-1, -1]
    
    failed = False
    
    try:
      rcode = ambari_server.check_jdbc_drivers(args)
    except FatalException:
      failed = True
    
    self.assertTrue(failed)
    self.assertTrue(print_error_msg_mock.called)
    
    get_ambari_properties_mock.reset_mock()
    find_jdbc_driver_mock.reset_mock()
    copy_files_mock.reset_mock()
    print_error_msg_mock.reset_mock()
    print_warning_msg.reset_mock()
    raw_input_mock.reset_mock()
    
    
    
    
    # Failed to copy_files    
    
    find_jdbc_driver_mock.side_effect = [drivers_list]
    try:
      rcode = ambari_server.check_jdbc_drivers(args)
    except FatalException:
      failed = True
    
    self.assertTrue(failed)
    
    sys.stdout = sys.__stdout__
    
    
  @patch.object(ambari_server, "find_properties_file")
  def test_get_ambari_properties(self, find_properties_file_mock):

    find_properties_file_mock.return_value = None
    rcode = ambari_server.get_ambari_properties()
    self.assertEqual(rcode, -1)
  
    tf1 = tempfile.NamedTemporaryFile()
    find_properties_file_mock.return_value = tf1.name
    prop_name='name'
    prop_value='val'
    
    with open(tf1.name, 'w') as fout:
      fout.write(prop_name + '=' + prop_value)
    fout.close()

    properties = ambari_server.get_ambari_properties()
    
    self.assertEqual(properties[prop_name], prop_value)
    self.assertEqual(properties.fileName, os.path.abspath(tf1.name))
    
    sys.stdout = sys.__stdout__

  @patch.object(ambari_server, "find_properties_file")
  def test_parse_properties_file(self, find_properties_file_mock):

    tf1 = tempfile.NamedTemporaryFile(mode='r')
    find_properties_file_mock.return_value = tf1.name

    args = MagicMock()
    ambari_server.parse_properties_file(args)
    self.assertEquals(args.persistence_type, "local")


    with open(tf1.name, 'w') as fout:
      fout.write("\n")
      fout.write(ambari_server.PERSISTENCE_TYPE_PROPERTY+"=remote")

    args = MagicMock()

    ambari_server.parse_properties_file(args)
    self.assertEquals(args.persistence_type, "remote")


  @patch.object(ambari_server, 'decrypt_password_for_alias')
  @patch.object(ambari_server, 'is_alias_string')
  @patch.object(ambari_server, 'get_ambari_properties')
  def test_configure_database_username_password_masterkey_persisted(self,
          get_ambari_properties_method, is_alias_string_method,
          decrypt_password_for_alias_method):

    out = StringIO.StringIO()
    sys.stdout = out

    configs = {ambari_server.JDBC_USER_NAME_PROPERTY: "fakeuser",
        ambari_server.JDBC_PASSWORD_PROPERTY: "${alias=somealias}",
        ambari_server.SECURITY_KEY_IS_PERSISTED: "True" }

    get_ambari_properties_method.return_value = configs

    is_alias_string_method.return_value = True
    decrypt_password_for_alias_method.return_value = "falepasswd"
    args = MagicMock()
    args.master_key = None

    ambari_server.configure_database_username_password(args)

    self.assertTrue(decrypt_password_for_alias_method.called)
    self.assertTrue(is_alias_string_method.called)
    self.assertEquals("fakeuser", args.database_username)
    self.assertEquals("falepasswd", args.database_password)

    sys.stdout = sys.__stdout__


  @patch.object(ambari_server, 'read_password')
  def test_configure_database_password(self, read_password_method):

    out = StringIO.StringIO()
    sys.stdout = out

    read_password_method.return_value = "fakepasswd"

    result = ambari_server.configure_database_password(True)
    self.assertTrue(read_password_method.called)
    self.assertEquals("fakepasswd", result)

    result = ambari_server.configure_database_password(True)
    self.assertEquals("fakepasswd", result)

    result = ambari_server.configure_database_password(True)
    self.assertEquals("fakepasswd", result)

    sys.stdout = sys.__stdout__


  @patch("os.path.exists")
  @patch.object(ambari_server, 'get_is_secure')
  @patch.object(ambari_server, 'get_is_persisted')
  @patch.object(ambari_server, 'remove_password_file')
  @patch.object(ambari_server, 'save_passwd_for_alias')
  @patch.object(ambari_server, 'read_master_key')
  @patch.object(ambari_server, 'read_ambari_user')
  @patch.object(ambari_server, 'get_master_key_location')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'save_master_key')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_setup_master_key_not_persist(self, is_root_method,
              get_ambari_properties_method, search_file_message,
              get_YN_input_method, save_master_key_method,
              update_properties_method, get_master_key_location_method,
              read_ambari_user_method, read_master_key_method,
              save_passwd_for_alias_method, remove_password_file_method,
              get_is_persisted_method, get_is_secure_method, exists_mock):

    is_root_method.return_value = True
    p = get_ambari_properties_method.return_value
    p.get_property.side_effect = [ "fakepasswd", "fakepasswd", "fakepasswd", "fakepasswd"]
    read_master_key_method.return_value = "aaa"
    get_YN_input_method.return_value = False
    read_ambari_user_method.return_value = None
    save_passwd_for_alias_method.return_value = 0
    get_is_persisted_method.return_value = (True, "filepath")
    get_is_secure_method.return_value = False
    exists_mock.return_value = False

    ambari_server.setup_master_key()

    self.assertTrue(get_YN_input_method.called)
    self.assertTrue(read_master_key_method.called)
    self.assertTrue(read_ambari_user_method.called)
    self.assertTrue(update_properties_method.called)
    self.assertFalse(save_master_key_method.called)
    self.assertTrue(save_passwd_for_alias_method.called)
    self.assertEquals(3, save_passwd_for_alias_method.call_count)
    self.assertTrue(remove_password_file_method.called)

    result_expected = {ambari_server.JDBC_PASSWORD_PROPERTY :
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.JDBC_RCA_PASSWORD_FILE_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.LDAP_MGR_PASSWORD_PROPERTY :
        ambari_server.get_alias_string(ambari_server.LDAP_MGR_PASSWORD_ALIAS),
        ambari_server.SSL_TRUSTSTORE_PASSWORD_PROPERTY :
        ambari_server.get_alias_string(ambari_server.SSL_TRUSTSTORE_PASSWORD_ALIAS),
        ambari_server.SECURITY_IS_ENCRYPTION_ENABLED : 'true'}

    sorted_x = sorted(result_expected.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)


  @patch.object(ambari_server, 'save_passwd_for_alias')
  @patch("os.path.exists")
  @patch.object(ambari_server, 'get_is_secure')
  @patch.object(ambari_server, 'get_is_persisted')
  @patch.object(ambari_server, 'read_master_key')
  @patch.object(ambari_server, 'read_ambari_user')
  @patch.object(ambari_server, 'get_master_key_location')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'save_master_key')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_setup_master_key_persist(self, is_root_method,
              get_ambari_properties_method, search_file_message,
              get_YN_input_method, save_master_key_method,
              update_properties_method, get_master_key_location_method,
              read_ambari_user_method, read_master_key_method,
              get_is_persisted_method, get_is_secure_method, exists_mock,
              save_passwd_for_alias_method):

    is_root_method.return_value = True
    p = get_ambari_properties_method.return_value
    p.get_property.side_effect = [ "fakepasswd", None, None, None ]
    read_master_key_method.return_value = "aaa"
    get_YN_input_method.side_effect = [True, False]
    read_ambari_user_method.return_value = None
    get_is_persisted_method.return_value = (True, "filepath")
    get_is_secure_method.return_value = False
    exists_mock.return_value = False
    save_passwd_for_alias_method.return_value = 0

    ambari_server.setup_master_key()

    self.assertTrue(get_YN_input_method.called)
    self.assertTrue(read_master_key_method.called)
    self.assertTrue(read_ambari_user_method.called)
    self.assertTrue(update_properties_method.called)
    self.assertTrue(save_master_key_method.called)

    result_expected = {ambari_server.JDBC_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.SECURITY_IS_ENCRYPTION_ENABLED: 'true'}

    sorted_x = sorted(result_expected.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)


  @patch.object(ambari_server, 'read_master_key')
  @patch.object(ambari_server, 'remove_password_file')
  @patch("os.path.exists")
  @patch.object(ambari_server, 'read_ambari_user')
  @patch.object(ambari_server, 'get_master_key_location')
  @patch("ambari-server.Properties")
  @patch.object(ambari_server, 'save_passwd_for_alias')
  @patch.object(ambari_server, 'read_passwd_for_alias')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'save_master_key')
  @patch.object(ambari_server, 'get_validated_string_input')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_reset_master_key_persisted(self, is_root_method,
              get_ambari_properties_method, search_file_message,
              get_YN_input_method, get_validated_string_input_method,
              save_master_key_method, update_properties_method,
              read_passwd_for_alias_method, save_passwd_for_alias_method,
              Properties_mock, get_master_key_location_method,
              read_ambari_user_method, exists_mock,
              remove_password_file_method, read_master_key_method):

    # Testing call under non-root
    is_root_method.return_value = False
    try:
      ambari_server.setup_master_key()
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing call under root
    is_root_method.return_value = True

    search_file_message.return_value = "filepath"
    read_ambari_user_method.return_value = None
    p = get_ambari_properties_method.return_value
    p.get_property.side_effect = [ 'true', '${alias=fakealias}',
                                   '${alias=fakealias}',
                                   '${alias=fakealias}', '${alias=fakealias}']

    get_YN_input_method.side_effect = [ True, True ]
    read_master_key_method.return_value = "aaa"
    read_passwd_for_alias_method.return_value = "fakepassword"
    save_passwd_for_alias_method.return_value = 0
    exists_mock.return_value = False

    ambari_server.setup_master_key()

    self.assertTrue(save_master_key_method.called)
    self.assertTrue(get_YN_input_method.called)
    self.assertTrue(read_master_key_method.called)
    self.assertTrue(update_properties_method.called)
    self.assertTrue(read_passwd_for_alias_method.called)
    self.assertTrue(3, read_passwd_for_alias_method.call_count)
    self.assertTrue(3, save_passwd_for_alias_method.call_count)

    result_expected = {ambari_server.JDBC_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.JDBC_RCA_PASSWORD_FILE_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.LDAP_MGR_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.LDAP_MGR_PASSWORD_ALIAS),
        ambari_server.SSL_TRUSTSTORE_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.SSL_TRUSTSTORE_PASSWORD_ALIAS),
        ambari_server.SECURITY_IS_ENCRYPTION_ENABLED: 'true'}

    sorted_x = sorted(result_expected.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)


  @patch.object(ambari_server, 'get_is_persisted')
  @patch.object(ambari_server, 'get_is_secure')
  @patch.object(ambari_server, 'remove_password_file')
  @patch("os.path.exists")
  @patch.object(ambari_server, 'read_ambari_user')
  @patch.object(ambari_server, 'get_master_key_location')
  @patch("ambari-server.Properties")
  @patch.object(ambari_server, 'save_passwd_for_alias')
  @patch.object(ambari_server, 'read_passwd_for_alias')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'save_master_key')
  @patch.object(ambari_server, 'get_validated_string_input')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_reset_master_key_not_persisted(self, is_root_method,
              get_ambari_properties_method,
              search_file_message, get_YN_input_method,
              get_validated_string_input_method, save_master_key_method,
              update_properties_method, read_passwd_for_alias_method,
              save_passwd_for_alias_method, Properties_mock,
              get_master_key_location_method, read_ambari_user_method,
              exists_mock, remove_password_file_method, get_is_secure_method,
              get_is_persisted_method):

    is_root_method.return_value = True
    search_file_message.return_value = False
    read_ambari_user_method.return_value = None
    p = get_ambari_properties_method.return_value
    p.get_property.side_effect = [ '${alias=fakealias}', '${alias=fakealias}',
                                   '${alias=fakealias}', '${alias=fakealias}']

    get_YN_input_method.side_effect = [ True, False ]
    get_validated_string_input_method.return_value = "aaa"
    read_passwd_for_alias_method.return_value = "fakepassword"
    save_passwd_for_alias_method.return_value = 0
    exists_mock.return_value = False
    get_is_secure_method.return_value = True
    get_is_persisted_method.return_value = (True, "filePath")

    ambari_server.setup_master_key()

    self.assertFalse(save_master_key_method.called)
    self.assertTrue(get_YN_input_method.called)
    self.assertTrue(get_validated_string_input_method.called)
    self.assertTrue(update_properties_method.called)
    self.assertTrue(read_passwd_for_alias_method.called)
    self.assertTrue(3, read_passwd_for_alias_method.call_count)
    self.assertTrue(3, save_passwd_for_alias_method.call_count)
    self.assertFalse(save_master_key_method.called)

    result_expected = {ambari_server.JDBC_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.JDBC_RCA_PASSWORD_FILE_PROPERTY:
        ambari_server.get_alias_string(ambari_server.JDBC_RCA_PASSWORD_ALIAS),
        ambari_server.LDAP_MGR_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.LDAP_MGR_PASSWORD_ALIAS),
        ambari_server.SSL_TRUSTSTORE_PASSWORD_PROPERTY:
        ambari_server.get_alias_string(ambari_server.SSL_TRUSTSTORE_PASSWORD_ALIAS),
        ambari_server.SECURITY_IS_ENCRYPTION_ENABLED: 'true'}

    sorted_x = sorted(result_expected.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)

  @patch('__builtin__.raw_input')
  @patch.object(ambari_server, 'get_is_secure')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_setup_ldap_invalid_input(self, is_root_method, get_ambari_properties_method,
                      search_file_message,
                      update_properties_method,
                      get_YN_input_method,
                      get_is_secure_method,
                      raw_input_mock):
    out = StringIO.StringIO()
    sys.stdout = out
    is_root_method.return_value = True
    search_file_message.return_value = "filepath"

    configs = { ambari_server.SECURITY_MASTER_KEY_LOCATION : "filepath",
                ambari_server.SECURITY_KEYS_DIR : tempfile.gettempdir(),
                ambari_server.SECURITY_IS_ENCRYPTION_ENABLED : "true"
    }

    get_ambari_properties_method.return_value = configs
    raw_input_mock.side_effect = ['a:3', 'b:b', 'host', 'b:2', 'false', 'uid', 'base', 'true']
    ambari_server.SILENT = False
    get_YN_input_method.return_value = True

    ambari_server.setup_ldap()

    ldap_properties_map = \
      {
        "authentication.ldap.primaryUrl" : "a:3",
        "authentication.ldap.secondaryUrl" : "b:2",
        "authentication.ldap.useSSL" : "false",
        "authentication.ldap.usernameAttribute" : "uid",
        "authentication.ldap.baseDn" : "base",
        "authentication.ldap.bindAnonymously" : "true",
        "client.security" : "ldap"
      }

    sorted_x = sorted(ldap_properties_map.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)
    self.assertTrue(get_YN_input_method.called)
    self.assertTrue(8, raw_input_mock.call_count)

    raw_input_mock.reset_mock()
    raw_input_mock.side_effect = ['a:3', '', 'b:2', 'false', 'uid', 'base', 'true']

    ambari_server.setup_ldap()

    ldap_properties_map = \
      {
        "authentication.ldap.primaryUrl" : "a:3",
        "authentication.ldap.useSSL" : "false",
        "authentication.ldap.usernameAttribute" : "uid",
        "authentication.ldap.baseDn" : "base",
        "authentication.ldap.bindAnonymously" : "true",
        "client.security" : "ldap"
      }

    sorted_x = sorted(ldap_properties_map.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)
    self.assertTrue(5, raw_input_mock.call_count)

    sys.stdout = sys.__stdout__

  @patch.object(ambari_server, 'get_is_secure')
  @patch.object(ambari_server, 'encrypt_password')
  @patch.object(ambari_server, 'save_passwd_for_alias')
  @patch.object(ambari_server, 'get_YN_input')
  @patch.object(ambari_server, 'update_properties')
  @patch.object(ambari_server, 'configure_ldap_password')
  @patch.object(ambari_server, 'get_validated_string_input')
  @patch.object(ambari_server, 'setup_master_key')
  @patch.object(ambari_server, 'search_file')
  @patch.object(ambari_server, 'get_ambari_properties')
  @patch.object(ambari_server, 'is_root')
  def test_setup_ldap(self, is_root_method, get_ambari_properties_method,
                search_file_message, setup_master_key_method,
                get_validated_string_input_method,
                configure_ldap_password_method, update_properties_method,
                get_YN_input_method, save_passwd_for_alias_method,
                encrypt_password_method, get_is_secure_method):
    out = StringIO.StringIO()
    sys.stdout = out

    # Testing call under non-root
    is_root_method.return_value = False
    try:
      ambari_server.setup_ldap()
      self.fail("Should throw exception")
    except FatalException as fe:
      # Expected
      self.assertTrue("root-level" in fe.reason)
      pass

    # Testing call under root
    is_root_method.return_value = True

    search_file_message.return_value = "filepath"

    configs = { ambari_server.SECURITY_MASTER_KEY_LOCATION : "filepath",
                ambari_server.SECURITY_KEYS_DIR : tempfile.gettempdir(),
                ambari_server.SECURITY_IS_ENCRYPTION_ENABLED : "true"
              }

    get_ambari_properties_method.return_value = configs
    configure_ldap_password_method.return_value = "password"
    setup_master_key_method.return_value = (None, True, True)
    save_passwd_for_alias_method.return_value = 0
    encrypt_password_method.return_value = ambari_server.get_alias_string(
      ambari_server.LDAP_MGR_PASSWORD_ALIAS)

    def yn_input_side_effect(*args, **kwargs):
      if 'TrustStore' in args[0]:
        return False
      else:
        return True

    #get_YN_input_method.side_effect = yn_input_side_effect()
    get_YN_input_method.side_effect = [ True,  ]

    def valid_input_side_effect(*args, **kwargs):
      if 'Bind anonymously' in args[0]:
        return 'false'
      if args[1] == "true" or args[1] == "false":
        return args[1]
      else:
        return "test"

    get_validated_string_input_method.side_effect = valid_input_side_effect

    ambari_server.setup_ldap()

    ldap_properties_map =\
    {
      "authentication.ldap.primaryUrl" : "test",
      "authentication.ldap.secondaryUrl" : "test",
      "authentication.ldap.useSSL" : "false",
      "authentication.ldap.usernameAttribute" : "test",
      "authentication.ldap.baseDn" : "test",
      "authentication.ldap.bindAnonymously" : "false",
      "authentication.ldap.managerDn" : "test",
      "client.security" : "ldap",\
      ambari_server.LDAP_MGR_PASSWORD_PROPERTY : ambari_server.get_alias_string(\
      ambari_server.LDAP_MGR_PASSWORD_ALIAS)
    }

    sorted_x = sorted(ldap_properties_map.iteritems(), key=operator.itemgetter(0))
    sorted_y = sorted(update_properties_method.call_args[0][1].iteritems(),
                      key=operator.itemgetter(0))
    self.assertEquals(sorted_x, sorted_y)
    self.assertTrue(update_properties_method.called)
    self.assertTrue(configure_ldap_password_method.called)
    self.assertTrue(get_validated_string_input_method.called)
    self.assertTrue(get_YN_input_method.called)

    sys.stdout = sys.__stdout__


  @patch.object(ambari_server, 'read_password')
  def test_configure_ldap_password(self, read_password_method):
    out = StringIO.StringIO()
    sys.stdout = out
    read_password_method.return_value = "blah"

    ambari_server.configure_ldap_password()

    self.assertTrue(read_password_method.called)

    sys.stdout = sys.__stdout__

  @patch.object(ambari_server, 'get_validated_string_input')
  def test_read_password(self, get_validated_string_input_method):
    out = StringIO.StringIO()
    sys.stdout = out

    passwordDefault = ""
    passwordPrompt = 'Enter Manager Password* : '
    passwordPattern = ".*"
    passwordDescr = "Invalid characters in password."

    get_validated_string_input_method.side_effect = ['', 'aaa', 'aaa']
    password = ambari_server.read_password(passwordDefault, passwordPattern,
                                passwordPrompt, passwordDescr)
    self.assertTrue(3, get_validated_string_input_method.call_count)
    self.assertEquals('aaa', password)

    get_validated_string_input_method.reset_mock()
    get_validated_string_input_method.side_effect = ['aaa', 'aaa']
    password = ambari_server.read_password(passwordDefault, passwordPattern,
                                passwordPrompt, passwordDescr)
    self.assertTrue(2, get_validated_string_input_method.call_count)
    self.assertEquals('aaa', password)

    get_validated_string_input_method.reset_mock()
    get_validated_string_input_method.side_effect = ['aaa']
    password = ambari_server.read_password('aaa', passwordPattern,
                                passwordPrompt, passwordDescr)
    self.assertTrue(1, get_validated_string_input_method.call_count)
    self.assertEquals('aaa', password)

    sys.stdout = sys.__stdout__

  def test_generate_random_string(self):
    random_str_len = 100
    str1 = ambari_server.generate_random_string(random_str_len)
    self.assertTrue(len(str1) == random_str_len)
    
    str2 = ambari_server.generate_random_string(random_str_len)
    self.assertTrue(str1 != str2)

  @patch("__builtin__.open")
  @patch.object(ambari_server, "search_file")
  @patch.object(ambari_server, "backup_file_in_temp")
  def test_update_properties(self, backup_file_in_temp_mock, search_file_mock, open_mock):
    conf_file = "ambari.properties"
    propertyMap = {"1":"1", "2":"2"}
    properties = MagicMock()
    f = MagicMock(name = "file")
    # f.__enter__.return_value = f #mimic file behavior
    search_file_mock.return_value = conf_file
    open_mock.return_value = f

    ambari_server.update_properties(properties, propertyMap)

    properties.store.assert_called_with(f.__enter__.return_value)
    backup_file_in_temp_mock.assert_called_with(conf_file)
    self.assertEquals(2, properties.removeOldProp.call_count)
    self.assertEquals(2, properties.process_pair.call_count)

    properties = MagicMock()
    backup_file_in_temp_mock.reset_mock()
    open_mock.reset_mock()

    ambari_server.update_properties(properties, None)
    properties.store.assert_called_with(f.__enter__.return_value)
    backup_file_in_temp_mock.assert_called_with(conf_file)
    self.assertFalse(properties.removeOldProp.called)
    self.assertFalse(properties.process_pair.called)


    pass


  def test_regexps(self):
    res = re.search(ambari_server.REGEX_HOSTNAME_PORT, "")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_HOSTNAME_PORT, "ddd")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_HOSTNAME_PORT, "gg:ff")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_HOSTNAME_PORT, "gg:55444325")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_HOSTNAME_PORT, "gg:555")
    self.assertTrue(res is not None)

    res = re.search(ambari_server.REGEX_TRUE_FALSE, "")
    self.assertTrue(res is not None)
    res = re.search(ambari_server.REGEX_TRUE_FALSE, "t")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_TRUE_FALSE, "trrrr")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_TRUE_FALSE, "true|false")
    self.assertTrue(res is None)
    res = re.search(ambari_server.REGEX_TRUE_FALSE, "true")
    self.assertTrue(res is not None)
    res = re.search(ambari_server.REGEX_TRUE_FALSE, "false")
    self.assertTrue(res is not None)

    res = re.search(ambari_server.REGEX_ANYTHING, "")
    self.assertTrue(res is not None)
    res = re.search(ambari_server.REGEX_ANYTHING, "t")
    self.assertTrue(res is not None)
    res = re.search(ambari_server.REGEX_ANYTHING, "trrrr")
    self.assertTrue(res is not None)


  def get_sample(self, sample):
    """
    Returns sample file content as string with normalized line endings
    """
    path = self.get_samples_dir(sample)
    return self.get_file_string(path)

  def get_file_string(self, file):
    """
    Returns file content as string with normalized line endings
    """
    string = open(file, 'r').read()
    return self.normalize(string)



  def normalize(self, string):
    """
    Normalizes line ending in string according to platform-default encoding
    """
    return string.replace("\n", os.linesep)



  def get_samples_dir(self, sample):
    """
    Returns full file path by sample name
    """
    testdir = os.path.dirname(__file__)
    return os.path.dirname(testdir) + os.sep + "resources" + os.sep \
           + 'TestAmbaryServer.samples/' + sample
