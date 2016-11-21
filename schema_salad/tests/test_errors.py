from typing import cast
from schema_salad.schema import load_schema, load_and_validate
from avro.schema import Names

document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
    u"test_schema/CommonWorkflowLanguage.yml")
avsc_names = cast(Names, avsc_names)

for t in ("test_schema/test1.cwl",
          "test_schema/test2.cwl",
          "test_schema/test3.cwl",
          "test_schema/test4.cwl",
          "test_schema/test5.cwl",
          "test_schema/test6.cwl",
          "test_schema/test7.cwl",
          "test_schema/test8.cwl",
          "test_schema/test9.cwl",
          "test_schema/test10.cwl",
          "test_schema/test11.cwl"):
    try:
        load_and_validate(document_loader, avsc_names, unicode(t), True)
    except Exception as e:
        print e, "\n"
    else:
        print t, "Should have thrown an error but did not"
