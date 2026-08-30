> Here we will put the text for the paper. Later, it will be slightly reformated to meet JOSS's submission criteria. For now, it's mostly copy-paste-edit from the manual or readme.


## Schema Salad: A bridge between document and record oriented data modeling and the Semantic Web

### Summary
Salad is a schema language for describing structured linked data documents in JSON or YAML documents. A Salad schema provides rules for preprocessing, structural validation, and link checking for documents described by a Salad schema. Salad builds on JSON-LD and the Apache Avro data serialization system and extends Avro with features for rich data modeling such as inheritance, template specialization, object identifiers, and object references. Salad was developed to provide a bridge between the record oriented data modeling supported by Apache Avro and the Semantic Web.

### Statement of need
The JSON data model is a popular way to represent structured data. It is attractive because of its relative simplicity and is a natural fit with the standard types of many programming languages. However, this simplicity comes at the cost that basic JSON lacks expressive features useful for working with complex data structures and document formats, such as schemas, object references, and namespaces.

JSON-LD is a W3C standard providing a way to describe how to interpret a JSON document as Linked Data by means of a "context". JSON-LD provides a powerful solution for representing object references and namespaces in JSON based on standard web URIs but is not itself a schema language. Without a schema providing a well-defined structure, it is difficult to process an arbitrary JSON-LD document as idiomatic JSON because there are many ways to express the same data that are logically equivalent but structurally distinct.

### State of the field
>It's better to extend or rework this section as _references should include full names of venues, e.g., journals and conferences, not abbreviations only understood in the context of a specific discipline_

Several schema languages exist for describing and validating JSON data, such as JSON Schema and Apache Avro data serialization system, however, none understand linked data. As a result, to fully take advantage of JSON-LD to build the next generation of linked data applications, one must maintain separate JSON schema, JSON-LD context, RDF schema, and human documentation, despite the significant overlap of content and obvious need for these documents to stay synchronized.

Schema Salad is designed to address this gap. It provides a schema language and processing rules for describing structured JSON content permitting URI resolution and strict document validation. The schema language supports linked data through annotations that describe the linked data interpretation of the content, enables generation of JSON-LD context and RDF schema, and production of RDF triples by applying the JSON-LD context. The schema language also provides for robust support of inline documentation.

### Mentions
> Put here recently submitter CWL paper. The title of this section should be changed into something meaningful.

### Examples
> I think it's would be great to put here some of the schema-salad examples (if we are still within 1000 words limit)
### Acknowledgements
### References
> References are built automatically from the content in the `.bib` file. So this section should be empty.