import unittest
import lxml.etree as ET
import requests
import json
from inoutlists import dump, DumperJSON, DumperPandas
from pandas import DataFrame as pdDF
try:
    from .settings import TestFixtures
except:
    from settings import TestFixtures
import inoutlists
from pathlib import Path
import os


class TestInOut(TestFixtures):

    def test_loader_num_list_entries_data_local(self):
        for source, sourceInfo in self.FIXTURES_INFO.items():
            with self.subTest(source=source):
                data = ET.parse(sourceInfo["input"]["localPath"]).getroot()
                listEntries = self.getListsEntries(data, source)
                self.assertEqual(
                    len(listEntries), 
                    len(self.DATA_LOCAL[source]["list_entries"]),
                    f"Source: {source}. Local data. Wrong number of loaded records."
                )

    def test_loader_num_list_entries_data_remote(self):
        for source, sourceInfo in self.FIXTURES_INFO.items():
            with self.subTest(source=source):
                r = requests.get(sourceInfo["input"]["url"])
                if r.status_code == 200:
                    data = ET.fromstring(r.content)            
                else:
                    r.raise_for_status()
                listEntries = self.getListsEntries(data, source)
                self.assertEqual(
                    len(listEntries), 
                    len(self.DATA_REMOTE[source]["list_entries"]),
                    f"Source: {source}. Remote data. Wrong number of loaded records."
                )

    def test_loader_names_whole_name_not_empty(self):
        for source, data in self.DATA_LOCAL.items():
            with self.subTest(source=source):
                for listEntry in data["list_entries"]:
                    with self.subTest(listEntryId=listEntry["id"]):
                        for nameInfo in listEntry["names"]:
                            self.assertNotEqual(
                                len(nameInfo["whole_name"]), 
                                0,
                                f'Source: {source}, List Entry: {listEntry["id"]}. Whole name empty')

    @staticmethod
    def getListsEntries(dataEl, source):
        if source in ["OFACSDN", "OFACCONS"]:
            return dataEl.findall(".//sdnEntry", namespaces=dataEl.nsmap)
        elif source == "EU":
            return dataEl.findall(".//sanctionEntity", namespaces=dataEl.nsmap)
        elif source == "UN":
            listEntriesI = dataEl.findall(".//INDIVIDUALS/INDIVIDUAL", namespaces=dataEl.nsmap)
            listEntriesO = dataEl.findall(".//ENTITIES/ENTITY", namespaces=dataEl.nsmap)
            return listEntriesI + listEntriesO
        else:
            return []
    
    def test_schema_validation_error(self):
        inoutlistsPath =  Path(os.path.dirname(inoutlists.__file__))        
        self.assertRaises(
            Exception,
            inoutlists.load,
            self.FIXTURES_INFO["OFACSDN"]["input"]["localPath"],
            loader=inoutlists.LoaderOFACXML,
            description="Test invalid schema",                
            schema = Path(inoutlistsPath, "EU_20171012-FULL-schema-1_1(xsd).xsd")
        )

    def test_dumper_JSON_num_list_entries(self):
        for source in self.FIXTURES_INFO.keys():
            with self.subTest(source=source):
                dataJSON = dump(
                    self.DATA_LOCAL[source],
                    DumperJSON
                )
                dataDict = json.loads(dataJSON)
                self.assertEqual(
                    len(dataDict["list_entries"]),
                    len(self.DATA_LOCAL[source]["list_entries"]),
                    f"Source: {source}. Wrong number of dumped records to JSON."
                )

    def test_dumper_Pandas(self):
        for source in self.FIXTURES_INFO.keys():
            with self.subTest(source=source):
                df = dump(
                    self.DATA_LOCAL[source], 
                    DumperPandas
                )
                self.assertIsInstance(
                    df,
                    pdDF,
                    f'Source {source}. Dumped object is not a Pandas Data Frame.'
                )

if __name__ == '__main__':
    unittest.main()