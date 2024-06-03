from pathlib import Path
import os
from inoutlists import load, LoaderEUXML, LoaderOFACXML, LoaderUNXML
import unittest

class TestFixtures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.FIXTURES_PATH = Path(
            Path(os.path.realpath(__file__)).parent,
            Path("./fixtures")
        )
        cls.FIXTURES_INFO = {
            "OFACSDN": {
                "input": {
                    "localPath": Path(cls.FIXTURES_PATH, "sdn.xml"),
                    "url": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML",
                    "loader": LoaderOFACXML
                },
                "output": {
                    "json": Path(cls.FIXTURES_PATH, "ofac_sdn.json"),
                    "csv": Path(cls.FIXTURES_PATH, "ofac_sdn.csv")
                }
            },
            "OFACCONS": {
                "input": {
                    "localPath": Path(cls.FIXTURES_PATH, "consolidated.xml"),
                    "url": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML",
                    "loader": LoaderOFACXML
                },
                "output": {
                    "json": Path(cls.FIXTURES_PATH, "ofac_consolidated.json"),
                    "csv": Path(cls.FIXTURES_PATH, "ofac_consolidated.csv")
                }
            },
            "EU": {
                "input": {            
                    "localPath": Path(cls.FIXTURES_PATH, "20240513-FULL-1_1(xsd).xml"),
                    "url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",                    
                    "loader": LoaderEUXML
                },
                "output": {
                    "json": Path(cls.FIXTURES_PATH, "eu.json"),
                    "csv": Path(cls.FIXTURES_PATH, "eu.csv")
                }
            },
            "UN": {
                "input": {
                    "localPath": Path(cls.FIXTURES_PATH, "un_consolidated.xml"),
                    "url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
                    "loader": LoaderUNXML
                },
                "output": {
                    "json": Path(cls.FIXTURES_PATH, "un.json"),
                    "csv": Path(cls.FIXTURES_PATH, "un.csv")
                }
            }
        }        
        cls.DATA_LOCAL = {}
        cls.DATA_REMOTE = {}
        for source, sourceInfo in cls.FIXTURES_INFO.items():
            cls.DATA_LOCAL[source] = load(
                sourceInfo["input"]["localPath"], 
                sourceInfo["input"]["loader"], 
                f"Test {source} Local Path"
            )
            cls.DATA_REMOTE[source] = load(
                sourceInfo["input"]["url"], 
                sourceInfo["input"]["loader"], 
                f"Test {source} url"
            )