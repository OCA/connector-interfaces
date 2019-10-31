# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from .common import FakeModelTestCase
from .fake_models import FakeSourceConsumer


class TestSourceCSV(FakeModelTestCase):

    TEST_MODELS_KLASSES = [FakeSourceConsumer]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_models()
        cls.source = cls._create_source()
        cls.consumer = cls._create_consumer()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_models()
        super().tearDownClass()

    @classmethod
    def _create_source(cls):
        filecontent = cls.load_filecontent(
            "connector_importer", "tests/fixtures/csv_source_test1.csv", mode="rb"
        )
        source = cls.env["import.source.csv"].create(
            {"csv_file": base64.encodestring(filecontent)}
        )
        source._onchance_csv_file()
        return source

    @classmethod
    def _create_consumer(cls):
        return cls.env["fake.source.consumer"].create({"name": "Foo", "version": "1.0"})

    extra_fields = [
        "chunk_size",
        "csv_filesize",
        "csv_filename",
        "csv_delimiter",
        "csv_quotechar",
    ]

    def test_source_basic(self):
        source = self.source
        self.assertEqual(source.name, "csv")
        self.assertItemsEqual(source._config_summary_fields, self.extra_fields)
        self.assertEqual(source.csv_delimiter, ",")
        self.assertEqual(source.csv_quotechar, '"')

    def test_source_get_lines(self):
        source = self.source
        # call private method to skip chunking, pointless here
        lines = list(source._get_lines())
        self.assertEqual(len(lines), 5)
        self.assertDictEqual(
            lines[0], {"id": "1", "fullname": "Marty McFly", "_line_nr": 2}
        )
        self.assertDictEqual(
            lines[1], {"id": "2", "fullname": "Biff Tannen", "_line_nr": 3}
        )
        self.assertDictEqual(
            lines[2], {"id": "3", "fullname": "Emmet Brown", "_line_nr": 4}
        )
        self.assertDictEqual(
            lines[3], {"id": "4", "fullname": "Clara Clayton", "_line_nr": 5}
        )
        self.assertDictEqual(
            lines[4], {"id": "5", "fullname": "George McFly", "_line_nr": 6}
        )

    def test_source_summary_data(self):
        source = self.source
        data = source._config_summary_data()
        self.assertEqual(data["source"], source)
        self.assertItemsEqual(data["summary_fields"], self.extra_fields)
        self.assertItemsEqual(
            sorted(self.extra_fields), sorted(data["fields_info"].keys())
        )
