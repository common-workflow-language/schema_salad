import cg_metaschema
import unittest
import logging

class TestGeneratedMetaschema(unittest.TestCase):
    def test_load(self):
        doc = {
            "type": "record",
            "fields": [{
                "name": "hello",
                "doc": "Hello test case",
                "type": "string"
            }]
        }
        rs = cg_metaschema.RecordSchema(doc, "")
        self.assertEqual("record", rs.type)
        self.assertEqual("hello", rs.fields[0].name)
        self.assertEqual("Hello test case", rs.fields[0].doc)
        self.assertEqual("string", rs.fields[0].type)
        self.assertEqual(doc, rs.save())

    def test_err(self):
        doc = {
            "doc": "Hello test case",
            "type": "string"
        }
        with self.assertRaises(cg_metaschema.ValidationException):
            rf = cg_metaschema.RecordField(doc, "")

    def test_err2(self):
        doc = {
            "type": "rucord",
            "fields": [{
                "name": "hello",
                "doc": "Hello test case",
                "type": "string"
            }]
        }
        with self.assertRaises(cg_metaschema.ValidationException):
            rs = cg_metaschema.RecordSchema(doc, "")

    def test_idmap(self):
        doc = {
            "type": "record",
            "fields": {
                "hello": {
                    "doc": "Hello test case",
                    "type": "string"
                }
            }
        }
        rs = cg_metaschema.RecordSchema(doc, "")
        self.assertEqual("record", rs.type)
        self.assertEqual("hello", rs.fields[0].name)
        self.assertEqual("Hello test case", rs.fields[0].doc)
        self.assertEqual("string", rs.fields[0].type)
        self.assertEqual(doc, rs.save())

    def test_idmap2(self):
        doc = {
            "type": "record",
            "fields": {
                "hello": "string"
            }
        }
        rs = cg_metaschema.RecordSchema(doc, "")
        self.assertEqual("record", rs.type)
        self.assertEqual("hello", rs.fields[0].name)
        self.assertEqual(None, rs.fields[0].doc)
        self.assertEqual("string", rs.fields[0].type)
        self.assertEqual(doc, rs.save())


if __name__ == '__main__':
    unittest.main()
