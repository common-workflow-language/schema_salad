#include "cwl_v1_0.h"
#include <iostream>

using namespace https___w3id_org_cwl_cwl;

int main() {
   auto tool = CommandLineTool{};
   *tool.cwlVersion = CWLVersion::v1_0;
   *tool.id         = "Some id";
   *tool.label      = "some label";
   *tool.doc        = "documentation that is brief";
   *tool.class_     = "CommandLineTool";

   {
       auto input = CommandInputParameter{};
       *input.id = "first";
       auto record = CommandInputRecordSchema{};

       auto fieldEntry = CommandInputRecordField{};
       *fieldEntry.name = "species";

       auto species = CommandInputEnumSchema{};
       species.symbols->push_back("homo_sapiens");
       species.symbols->push_back("mus_musculus");

       using ListType = std::vector<std::variant<CWLType, CommandInputRecordSchema, CommandInputEnumSchema, CommandInputArraySchema, std::string>>;
       *fieldEntry.type = ListType{species, "null"};

       using ListType2 = std::vector<CommandInputRecordField>;
       *record.fields = ListType2{fieldEntry};

       using ListType3 = std::vector<std::variant<CWLType, CommandInputRecordSchema, CommandInputEnumSchema, CommandInputArraySchema, std::string>>;
       *input.type = ListType3{record};

       tool.inputs->push_back(input);
   }


   auto y = toYaml(tool);

   YAML::Emitter out;
   out << y;
   std::cout << out.c_str() << "\n";
}
