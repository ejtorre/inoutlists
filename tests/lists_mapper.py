from pathlib import Path
import os
import context
from inoutlists import load, LoaderOFACXML, LoaderEUXML, LoaderUNXML
from inoutlists import dump, DumperJSON, DumperPandas, DumperCSV


_modulePath = Path(os.path.realpath(__file__)).parent

filesInfo = {
    "OFACSDN": {
        "input": {
            "localPath": Path(_modulePath, "./.data/sdn.xml"),
            "url": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML",            
            "loader": LoaderOFACXML
        },
        "output": {
            "json": Path(_modulePath, "./.data/ofac_sdn.json"),
            "csv": Path(_modulePath, "./.data/ofac_sdn.csv")
        }
    }   ,
    "OFACCONS": {
        "input": {
            "localPath": Path(_modulePath, "./.data/consolidated.xml"),
            "url": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML",
            "loader": LoaderOFACXML
        },
        "output": {
            "json": Path(_modulePath, "./.data/ofac_consolidated.json"),
            "csv": Path(_modulePath, "./.data/ofac_consolidated.csv")
        }
    },
    "EU": {
        "input": {            
            "localPath": Path(_modulePath, "./.data/20240513-FULL-1_1(xsd).xml"),
            "url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",                    
            "loader": LoaderEUXML
        },
        "output": {
            "json": Path(_modulePath, "./.data/eu.json"),
            "csv": Path(_modulePath, "./.data/eu.csv")
        }
    },
    "UN": {
        "input": {
            "localPath": Path(_modulePath, "./.data/un_consolidated.xml"),
            "url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
            "loader": LoaderUNXML
        },
        "output": {
            "json": Path(_modulePath, "./.data/un.json"),
            "csv": Path(_modulePath, "./.data/un.csv")
        }
    }
}

lists = {}
dfs = {}

for description, sourceInfo in filesInfo.items():
    if description in ["EU", "OFACSDN", "OFACCONS", "UN"]:
        list = load(
            #sourceInfo["input"]["localPath"],
            sourceInfo["input"]["url"],
            sourceInfo["input"]["loader"],
            description
        )     
        lists[description] = list
        fileJSON = sourceInfo["output"]["json"]        
        dump(
            list, 
            DumperJSON, 
            output=fileJSON, 
            indent=2, 
            ensure_ascii=False
        )
        dfs[description] = dump(list, DumperPandas)
        fileCSV = sourceInfo["output"]["csv"]
        dump(
            list, 
            DumperCSV, 
            output=fileCSV, 
            index=False, 
            sep="\t", 
            lineterminator = "\n"
        )

    else:
        print(f"Unknown description: {description}. Only allowed EU, OFACSDN and OFACCONS")