import unittest

import mock

from autodiscovery.exceptions import ReportableException
from autodiscovery.reports import AbstractReport
from autodiscovery.reports import Entry


class TestAbstractReport(unittest.TestCase):
    def setUp(self):
        class TestedClass(AbstractReport):
            pass

        self.tested_instance = TestedClass()

    @mock.patch("autodiscovery.reports.base.Entry")
    def test_add_entry(self, entry_class):
        """Check that method will add entry into the entries list and return given entry"""
        entry = mock.MagicMock()
        ip = "test IP"
        domain = "test domain"
        offline = False
        entry_class.return_value = entry
        # act
        result = self.tested_instance.add_entry(ip=ip, domain=domain, offline=offline)
        # verify
        self.assertEqual(result, entry)
        self.assertIn(result, self.tested_instance._entries)
        entry_class.assert_called_once_with(ip=ip, domain=domain, status=entry_class.SUCCESS_STATUS)

    def test_edit_entry(self):
        """Check that method will add entry into the entries list and return given entry"""
        entry = mock.MagicMock()
        # act
        result = self.tested_instance.edit_entry(entry)
        # verify
        self.assertEqual(result, entry)
        self.assertIn(result, self.tested_instance._entries)

    def test_get_current_entry_no_entries(self):
        """Check that method will return None if there is no any entries"""
        # act
        result = self.tested_instance.get_current_entry()
        # verify
        self.assertIsNone(result)

    def test_get_current_entry(self):
        """Check that method will return last entry in the entries list"""
        self.tested_instance._entries = [mock.MagicMock(), mock.MagicMock()]
        # act
        result = self.tested_instance.get_current_entry()
        # verify
        self.assertEqual(result, self.tested_instance._entries[-1])

    def test_generate(self):
        """Check that method will raise exception if it wasn't implemented in the child class"""
        with self.assertRaises(NotImplementedError):
            self.tested_instance.generate()

    def parse_entries_from_file(self):
        """Check that method will raise exception if it wasn't implemented in the child class"""
        with self.assertRaises(NotImplementedError):
            self.tested_instance.parse_entries_from_file(report_file="report.xlsx")


class TestEntry(unittest.TestCase):
    def setUp(self):
        self.entry = Entry(ip="test_ip", status=Entry.SUCCESS_STATUS, domain="Tets domain")

    def test_enter_with_statement(self):
        """Check that with statement will return same entry"""
        with self.entry as entry:
            self.assertEqual(self.entry, entry)

    def test_exit_with_statement(self):
        """Check that entry status will be changed to the failed one"""
        with self.assertRaisesRegexp(Exception, "Test Exception"):
            with self.entry as entry:
                self.assertEqual(self.entry, entry)
                raise ReportableException("Test Exception")

        self.assertEqual(self.entry.status, Entry.FAILED_STATUS)
        self.assertEqual(self.entry.comment, "Test Exception")
