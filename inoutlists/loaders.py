import lxml.etree as ET
import csv
from pathlib import Path
import requests
import os
from datetime import datetime

__all__ = [
    "load",
    "Loader",
    "LoaderXML",
    "LoaderOFACXML",
    "LoaderEUXML",
    "LoaderUNXML"    
]

_modulePath = Path(os.path.dirname(__file__))

class Loader():

    def __init__(self, *args, **kwargs):        
        self.meta = {
            "description": kwargs.get("description", "")
        }
        self.args = args
        self.kwargs = kwargs
        self.countryNames = {}
        with open(Path(_modulePath, "country_names.csv"), 
                  mode="r", 
                  encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                self.countryNames[row["COUNTRY_NAME"]] = row["ISO2_CODE"]
        self.countryISOCodes = {}
        with open(Path(_modulePath, "country_ISO_codes.csv"),
                    mode="r", 
                    encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                self.countryISOCodes[row["ISO2_CODE"]] = row["COUNTRY_NAME"]

    def load(self, data):
        pass

    def loadListEntry(self, listEntry):
        result = {            
            "id": self.getId(listEntry),
            "type": self.getType(listEntry),
            "names": self.getNames(listEntry)
        }
        addresses = self.getAddresses(listEntry)
        if len(addresses) > 0:
            result["addresses"] = addresses
        nationalities = self.getNationalities(listEntry)
        if len(nationalities) > 0:
            result["nationalities"] = nationalities
        dates_of_birth = self.getDatesOfBirth(listEntry)
        if len(dates_of_birth) > 0:
            result["dates_of_birth"] = dates_of_birth
        places_of_birth = self.getPlacesOfBirth(listEntry)
        if len(places_of_birth) > 0:
            result["places_of_birth"] = places_of_birth
        identifications = self.getIdentifications(listEntry)
        if len(identifications) > 0:
            result["identifications"] = identifications
        programs = self.getPrograms(listEntry)
        if len(programs) > 0:
            result["programs"] = programs
        additionalInformation = self.getAddtionalInformation(listEntry)
        if bool(additionalInformation):
            result["additional_information"] = additionalInformation

        return result
    
    def getId(self, listEntry):
        return ""
    
    def getType(self, listEntry):
        return ""

    def getNames(self, listEntry):
        return []

    def getAddresses(self, listEntry):
        return []

    def getNationalities(self, listEntry):
        return []

    def getDatesOfBirth(self, listEntry):
        return []

    def getPlacesOfBirth(self, listEntry):
        return []

    def getIdentifications(self, listEntry):
        return []
    
    def getPrograms(self, listEntry):
        return []
    
    def getAddtionalInformation(self, listEntry):
        pass
    
    def getISOCodeFromCountryName(self, countryName):
        return self.countryNames.get(countryName, "00")
    
    def getCountryNameFromISOCode(self, ISOCode):
        return self.countryISOCodes.get(ISOCode, "UNKNOWN")
    
    @staticmethod
    def lxmlFindText(element, path: str, ns: dict):
        pathText = element.findtext(path, namespaces = ns)
        return "" if pathText is None else pathText.strip()

    @staticmethod
    def lxmlGetAttribValue(element, attribName: str):
        return element.attrib.get(attribName, "").strip()

    @staticmethod
    def dedupDictsList(dictsList: dict):
        return [i for n, i in enumerate(dictsList) if i not in dictsList[:n]]

    @staticmethod
    def dedupList(dupList: list):
        return list(dict.fromkeys(dupList))
    
    @staticmethod
    def stripAdvance(string: str):
        return " ".join(string.split()).strip()

class LoaderXML(Loader):

    def __init__(self, 
                 description="", 
                 schema=Path(_modulePath, "OFAC_xml.xsd")
        ):
        super().__init__(description=description, schema=schema)
        self.schema = schema

    def load(self, data_source):        
        try:
            if isinstance(data_source, str):
                if data_source.startswith(('https://', 'http://')):
                    r = requests.get(data_source)
                    if r.status_code == 200:
                        self.data = ET.fromstring(r.content)
                        self.meta["source"] = data_source
                    else:
                        r.raise_for_status()
                elif os.path.exists(data_source):                    
                    self.data = ET.parse(data_source).getroot()
                    self.meta["source"] = data_source
                else:
                    self.data = ET.fromstring(data_source)
                    self.meta["source"] = "String flow"
            elif isinstance(data_source, Path):
                self.data = ET.parse(data_source).getroot()
                self.meta["source"] = str(data_source.resolve())
            else:
                raise Exception("Data source not allowed")
        except Exception as err:
            print(f"{err=}, {type(err)=}")        

        if self.schema is None:
            raise Exception("The loader class must provide a path to a schema")
        
        if not isinstance(self.schema, Path):
            raise Exception("The schema must be a Path object")

        if not self.schemaValidation(self.schema):
            raise Exception(f"Data invalid. Schema: {str(self.schema)}")
            
        self.ns = self.data.nsmap

    def schemaValidation(self, xsd):
        xmlschema_doc = ET.parse(xsd)
        xmlschema = ET.XMLSchema(xmlschema_doc)
        return xmlschema.validate(self.data)

class LoaderOFACXML(LoaderXML):

    def __init__(self, 
                 description="", 
                 schema=Path(_modulePath, "OFAC_xml.xsd")
        ):
        super().__init__(description=description, schema=schema)
        self.allowedIdTypes = []
        with open(Path(_modulePath, "./OFAC_id_Types.csv"), 
                  mode="r", 
                  encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.allowedIdTypes.append(row["OFAC_ID_TYPE"])

    def load(self, data_source):        
        super().load(data_source)
        listDateTxt = self.lxmlFindText(
                        self.data, 
                        "publshInformation/Publish_Date",
                        self.ns
                    )
        try:
            listDateDt = datetime.strptime(listDateTxt, '%m/%d/%Y').date()
            self.meta["list_date"] = listDateDt.isoformat()
            listEntries = []
        except Exception as err:
            print(f"{err=}, {type(err)=}")
            self.meta["list_date"] = ""
        for listEntry in self.data.findall(".//sdnEntry", namespaces = self.ns):
            listEntries.append(self.loadListEntry(listEntry))
        return {
            "meta": self.meta,
            "list_entries": listEntries
        }
    
    def getId(self, listEntry):
        return self.lxmlFindText(listEntry, "uid", self.ns)    
    
    def getType(self, listEntry):
        
        sdnType = self.lxmlFindText(listEntry, "sdnType", self.ns)

        if sdnType == "Entity":
            return "O"
        elif sdnType == "Individual":
            return "I"
        elif sdnType == "Vessel":
            return "V"
        elif sdnType == "Aircraft":
            return "A"
        else:
            return "U"
    
    def getNames(self, listEntry):

        names = []

        entityType = self.getType(listEntry)

        # Main Name

        first_nameOFAC = self.lxmlFindText(listEntry, "firstName", self.ns)
        last_nameOFAC = self.lxmlFindText(listEntry, "lastName", self.ns)        
        names.append(self.getNameOFAC("strong", first_nameOFAC, last_nameOFAC, entityType))

        # Aliases
                
        for aliasEl in listEntry.findall("akaList/aka", namespaces = self.ns):            
            category = self.lxmlFindText(aliasEl, "category", self.ns) 
            first_nameOFAC = self.lxmlFindText(aliasEl, "firstName", self.ns)
            last_nameOFAC = self.lxmlFindText(aliasEl, "lastName", self.ns)            
            names.append(self.getNameOFAC(category, first_nameOFAC, last_nameOFAC, entityType))

        return self.dedupDictsList(names)    
    
    def getNameOFAC(self, category, first_nameOFAC, last_nameOFAC, entitytype):
        strong = True if category == "strong" else False
        if entitytype == "I":
            first_name = first_nameOFAC
            last_name = last_nameOFAC
            whole_name = " ".join([first_name, last_name])            
        else:
            first_name = ""
            last_name = ""
            whole_name = last_nameOFAC        
        return {
            "whole_name": self.stripAdvance(whole_name).upper(),
            "strong": strong,
            "first_name": self.stripAdvance(first_name).upper(),
            "last_name": self.stripAdvance(last_name).upper()          
        }
    
    def getAddresses(self, listEntry):

        addresses = []

        for addressEl in listEntry.findall("addressList/address", namespaces = self.ns):            
            
            street1 = self.lxmlFindText(addressEl, "address1", self.ns)
            street2 = self.lxmlFindText(addressEl, "address2", self.ns)
            street3 = self.lxmlFindText(addressEl, "address2", self.ns)
            street = " ".join([street1, street2, street3])            
            city = self.lxmlFindText(addressEl, "city", self.ns)
            country_subdivision = self.lxmlFindText(addressEl, "stateOrProvince", self.ns)
            country_ori = self.lxmlFindText(addressEl, "country", self.ns)
            country_ori= self.stripAdvance(country_ori).upper()
            country_ISO_code = self.getISOCodeFromCountryName(country_ori)
            country_desc = self.getCountryNameFromISOCode(country_ISO_code)
            address = " ".join(
                [
                    street,
                    city,
                    country_subdivision,
                    country_ori   
                ]
            )            
            address = self.stripAdvance(address)
            if len(address) > 0:
                addresses.append(
                    {
                        "address": address.upper(),
                        "street": self.stripAdvance(street).upper(),
                        "city": self.stripAdvance(city).upper(),
                        "country_subdivision": self.stripAdvance(country_subdivision).upper(),
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc 
                    }
                )

        return self.dedupDictsList(addresses)
    
    def getNationalities(self, listEntry):

        nationalitiesPaths = [
            "nationalityList/nationality",
            "citizenshipList/citizenship"
        ]

        nationalities = []

        for nationalitiesPath in nationalitiesPaths:
            for nationalityEL in listEntry.findall(nationalitiesPath, namespaces = self.ns):
                nationality_ori = self.lxmlFindText(nationalityEL, "country", self.ns)
                nationality_ori = self.stripAdvance(nationality_ori).upper()
                if len(nationality_ori) > 0:
                    country_ISO_code = self.getISOCodeFromCountryName(nationality_ori)
                    country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                    nationalities.append(
                        {
                            "country_ori": nationality_ori,
                            "country_ISO_code": country_ISO_code,
                            "country_desc": country_desc
                        }
                    )

        return self.dedupDictsList(nationalities)
    
    def getDatesOfBirth(self, listEntry):

        datesOfBirth = []
        xpath = "dateOfBirthList/dateOfBirthItem"

        for dobEl in listEntry.findall(xpath, namespaces = self.ns):            
            dobOFAC = self.lxmlFindText(dobEl, "dateOfBirth", self.ns)
            dob =  self.getISODateFromOFACDate(dobOFAC)
            if dob is not None:            
                dobParts = dob.split("-")
                datesOfBirth.append(
                    {
                        "date_of_birth": dob if len(dobParts) == 3 else "",
                        "year": dobParts[0],
                        "month": dobParts[1] if len(dobParts) == 3 else "",
                        "day": dobParts[2] if len(dobParts) == 3 else ""
                    }
                )
        
        return self.dedupDictsList(datesOfBirth)

    @staticmethod
    def getISODateFromOFACDate(OFACDate):

        OFACMonths = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",            
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12"
        }
        OFACDateParts = OFACDate.split(" ")
        if len(OFACDateParts) == 0:
            return None
        elif len(OFACDateParts) == 1:
            return f'{OFACDateParts[0]}'
        elif len(OFACDateParts) == 3:
            month = OFACMonths.get(OFACDateParts[1],"")
            if len(month) == 0:
                return f'{OFACDateParts[2]}'                
            else:                
                return f'{OFACDateParts[2]}-{month}-{OFACDateParts[0]}'
        else:
            return None
        
    def getPlacesOfBirth(self, listEntry):

        placesOfBirth = []
        xpath = "placeOfBirthList/placeOfBirthItem"

        for pobEl in listEntry.findall(xpath, namespaces = self.ns):
            pob = self.lxmlFindText(pobEl, "placeOfBirth", self.ns)
            pob =  self.stripAdvance(pob)
            if len(pob) > 0:
                countryOfBirth = self.getCountryOfBirthOFAC(pob)
                placesOfBirth.append(
                    {
                            "place_of_birth": pob.upper(),
                            "street": "",
                            "city": "",
                            "country_subdivision": "",
                            "country_ori": countryOfBirth["country_ori"],
                            "country_ISO_code": countryOfBirth["country_ISO_code"],
                            "country_desc": countryOfBirth["country_desc"]
                    }
                )

        return self.dedupDictsList(placesOfBirth)
    
    def getCountryOfBirthOFAC(self, pob):
        pobParts = pob.split(",")
        country_ori = self.stripAdvance(pobParts[-1]).upper()
        country_ISO_code = self.getISOCodeFromCountryName(country_ori)
        country_desc = self.getCountryNameFromISOCode(country_ISO_code)        
        return {
            "country_ori": "" if country_ISO_code == "00" else country_ori,
            "country_ISO_code": country_ISO_code,
            "country_desc": country_desc
        }        
    
    def getIdentifications(self, listEntry):        
        
        identifications = []

        for IdEl in listEntry.findall("idList/id", namespaces = self.ns):
            idType = self.lxmlFindText(IdEl, "idType", self.ns)
            idNumber = self.lxmlFindText(IdEl, "idNumber", self.ns)
            if idType in self.allowedIdTypes and len(idNumber) > 0:
                country_ori = self.lxmlFindText(IdEl, "idCountry", self.ns)
                country_ori = self.stripAdvance(country_ori).upper()
                country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                identifications.append(
                    {
                        "type": self.stripAdvance(idType).upper(),
                        "id": idNumber,
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )

        return self.dedupDictsList(identifications)
    
    def getPrograms(self, listEntry):
         
         programs = []
         for prEl in listEntry.findall("programList/program", namespaces = self.ns):
             if prEl.text is not None:
                programs.append(self.stripAdvance(prEl.text))

         return self.dedupList(programs)
    
    def getAddtionalInformation(self, listEntry):

        result = {}

        remark = self.stripAdvance(
                self.lxmlFindText(
                    listEntry, 
                    "remarks", 
                    self.ns
                )
            )
        if len(remark) > 0:
            result["remarks"] = remark
        
        for IdEl in listEntry.findall("idList/id", namespaces = self.ns):
            idType = self.lxmlFindText(IdEl, "idType", self.ns)
            idNumber = self.stripAdvance(
                            self.lxmlFindText(
                                IdEl, 
                                "idNumber", 
                                self.ns
                            )
                        )
            if idType not in self.allowedIdTypes and len(idNumber) > 0:                
                idType = self.stripAdvance(idType)
                idType = idType.replace(" ", "_")
                idType = idType.replace(":", "")
                if len(idNumber) > 0:
                    result[idType.lower()] = idNumber
        
        return result

class LoaderEUXML(LoaderXML):

    def __init__(self, 
                 description="", 
                 schema=Path(_modulePath, "EU_20171012-FULL-schema-1_1(xsd).xsd")
        ):
        super().__init__(description=description, schema=schema)

    def load(self, data_source):
        super().load(data_source)
        self.meta["list_date"] = self.lxmlGetAttribValue(self.data, "generationDate")        
        listEntries = []
        for listEntry in self.data.findall(".//sanctionEntity", namespaces = self.ns):
            listEntries.append(self.loadListEntry(listEntry))
        return {
            "meta": self.meta,
            "list_entries": listEntries
        }
    
    def getId(self, listEntry):
        return self.lxmlGetAttribValue(listEntry, "euReferenceNumber")
    
    def getType(self, listEntry):

        euTypeEl = listEntry.find("subjectType", namespaces = self.ns)        
        if euTypeEl is not None:            
            euType = self.lxmlGetAttribValue(euTypeEl, "classificationCode")
        else:
            euType = ""

        if euType == "P":
            return "I"
        elif euType == "E":
            return "O"
        else:
            return "U"
        
    def getNames(self, listEntry):

        names = []

        for nameEl in listEntry.findall("nameAlias", namespaces = self.ns):            
            strong = True if self.lxmlGetAttribValue(nameEl, "strong") == "true" else False
            first_nameEU = self.lxmlGetAttribValue(nameEl, "firstName")
            middle_nameEU = self.lxmlGetAttribValue(nameEl, "middleName")
            last_nameEU = self.lxmlGetAttribValue(nameEl, "lastName")
            whole_nameEU = self.lxmlGetAttribValue(nameEl, "wholeName")
            first_name = " ".join([first_nameEU, middle_nameEU])            
            names.append(
                {                    
                    "whole_name": self.stripAdvance(whole_nameEU).upper(),
                    "strong": strong,
                    "first_name": self.stripAdvance(first_name).upper(),
                    "last_name": self.stripAdvance(last_nameEU).upper()                    
                }
            )

        return self.dedupDictsList(names)
    
    def getAddresses(self, listEntry):

        addresses = []

        for addressEl in listEntry.findall("address", namespaces = self.ns):
            street = self.lxmlGetAttribValue(addressEl, "street")
            city = " ".join(
                [
                    self.lxmlGetAttribValue(addressEl, "place") , 
                    self.lxmlGetAttribValue(addressEl, "city")
                ]
            )            
            country_subdivision = self.lxmlGetAttribValue(addressEl, "region")
            country_ori = self.lxmlGetAttribValue(addressEl, "countryDescription")
            country_ori = self.stripAdvance(country_ori).upper()
            address = " ".join(
                [
                    street,
                    city,
                    country_subdivision,
                    "" if country_ori == "UNKNOWN" else country_ori
                ]
            )
            address = self.stripAdvance(address)
            if len(address) > 0:
                country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                addresses.append(
                    {
                        "address": address.upper(),
                        "street": self.stripAdvance(street).upper(),
                        "city": self.stripAdvance(city).upper(),
                        "country_subdivision": self.stripAdvance(country_subdivision).upper(),
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )

        return self.dedupDictsList(addresses)
    
    def getNationalities(self, listEntry):

        nationalities = []

        for nationalityEl in listEntry.findall("citizenship", namespaces = self.ns):
            nationality_ori = self.lxmlGetAttribValue(nationalityEl, "countryDescription")
            nationality_ori = self.stripAdvance(nationality_ori).upper()
            if len(nationality_ori) > 0 and nationality_ori != "UNKNOWN":
                country_ISO_code = self.getISOCodeFromCountryName(nationality_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                nationalities.append(
                    {
                        "country_ori": nationality_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )

        return self.dedupDictsList(nationalities)
    
    def getDatesOfBirth(self, listEntry):

        datesOfBirth = []

        for dobEl in listEntry.findall("birthdate", namespaces = self.ns):

            yearIni = self.lxmlGetAttribValue(dobEl, "yearRangeFrom")
            yearEnd = self.lxmlGetAttribValue(dobEl, "yearRangeTo")

            if len(yearIni) > 0 and len(yearEnd) > 0:
                for year in range(int(yearIni), int(yearEnd) + 1, 1):
                    datesOfBirth.append(
                        {
                            "date_of_birth": "",
                            "year": str(year),
                            "month": "",
                            "day": ""
                        }
                    )
            else:
                date_of_birth = self.lxmlGetAttribValue(dobEl, "birthdate")
                monthOri = self.lxmlGetAttribValue(dobEl, "monthOfYear")
                month = "{:02d}".format(int(monthOri)) if len(monthOri) > 0 else ""
                dayOri = self.lxmlGetAttribValue(dobEl, "dayOfMonth")
                day = "{:02d}".format(int(dayOri)) if len(dayOri) > 0 else ""
                year = self.lxmlGetAttribValue(dobEl, "year")                

                if len(date_of_birth) > 0 or \
                   len(month) > 0  or \
                   len(day) > 0 or \
                   len(year) > 0:
                    
                    datesOfBirth.append(
                        {
                            "date_of_birth": date_of_birth,
                            "year": year,
                            "month": month,
                            "day": day
                        }
                    )

        return self.dedupDictsList(datesOfBirth)
    
    def getPlacesOfBirth(self, listEntry):

        placesOfBirth = []

        for pobEl in listEntry.findall("birthdate", namespaces = self.ns):
            street = ""
            city = " ".join(
                [
                    self.lxmlGetAttribValue(pobEl, "place"), 
                    self.lxmlGetAttribValue(pobEl, "city")
                ]
            )
            country_subdivision = self.lxmlGetAttribValue(pobEl, "region")            
            country_ori = self.lxmlGetAttribValue(pobEl, "countryDescription")
            country_ori = self.stripAdvance(country_ori).upper()
            pob = " ".join(
                    [
                        street,
                        city,
                        country_subdivision,
                        "" if country_ori == "UNKNOWN"  else country_ori
                    ]
                )               
            pob = self.stripAdvance(pob)
            if len(pob) > 0:
                country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                placesOfBirth.append(
                    {
                        "place_of_birth": pob.upper(),
                        "street": self.stripAdvance(street).upper(),
                        "city": self.stripAdvance(city).upper(),
                        "country_subdivision": self.stripAdvance(country_subdivision).upper(),
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )

        return self.dedupDictsList(placesOfBirth)
    
    def getIdentifications(self, listEntry):

        identifications = []

        for IdEl in listEntry.findall("identification", namespaces = self.ns):
            idNumber =  self.lxmlGetAttribValue(IdEl, "number")
            if len(idNumber) > 0:
                idType = self.lxmlGetAttribValue(IdEl, "identificationTypeDescription")
                country_ori = self.lxmlGetAttribValue(IdEl, "countryDescription")
                country_ori = self.stripAdvance(country_ori).upper()
                country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                identifications.append(
                    {
                        "type": self.stripAdvance(idType).upper(),
                        "id": idNumber,
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )

        return self.dedupDictsList(identifications)
    
    def getPrograms(self, listEntry):
         
        regulationEl = listEntry.find("regulation", namespaces = self.ns)
        if regulationEl is not None:
            program = self.stripAdvance(
                self.lxmlGetAttribValue(regulationEl, "programme")
            )
        else:
            program = ""
        if len(program) > 0:
            return [program]
        else:
            return []
        
    def getAddtionalInformation(self, listEntry):

        result = {}
        
        remarks = []
        for remarkEL in listEntry.findall("remark", namespaces = self.ns):
            if remarkEL is not None:
                remarks.append(remarkEL.text)

        remark = " ".join(remarks)
        remark = self.stripAdvance(remark)
        
        if len(remark) > 0:
            result["remarks"] = remark

        return result
    
class LoaderUNXML(LoaderXML):

    def __init__(self, 
                 description="", 
                 schema=Path(_modulePath, "UN_consolidated.xsd")
        ):
        super().__init__(description=description, schema=schema)
    
    def load(self, data_source):
        super().load(data_source)
        self.listEntryPath = ""
        self.meta["list_date"] = self.lxmlGetAttribValue(self.data, "dateGenerated")
        
        listEntries = []
        listEntryPaths = [
            ".//INDIVIDUALS/INDIVIDUAL",
            ".//ENTITIES/ENTITY"
        ]
        for listEntryPath in listEntryPaths:
            self.listEntryPath = listEntryPath
            for listEntry in self.data.findall(
                listEntryPath,
                namespaces=self.ns):
                listEntries.append(self.loadListEntry(listEntry))

        return {
            "meta": self.meta,
            "list_entries": listEntries
        }
    
    def getId(self, listEntry):
        return self.lxmlFindText(listEntry, "REFERENCE_NUMBER", self.ns)
    
    def getType(self, listEntry):
        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":
            return "I"
        elif self.listEntryPath == ".//ENTITIES/ENTITY":
            return "O"
        else:
            return "U"
        
    def getNames(self, listEntry):
        
        names = []

        entityType = self.getType(listEntry)
        
        # Main Name        

        first_nameUN = self.lxmlFindText(listEntry, "FIRST_NAME", self.ns)
        second_nameUN = self.lxmlFindText(listEntry, "SECOND_NAME", self.ns)
        third_nameUN = self.lxmlFindText(listEntry, "THIRD_NAME", self.ns)
        fourth_nameUN = self.lxmlFindText(listEntry, "FOURTH_NAME", self.ns)

        if entityType == "I":
            whole_name = " ".join(
                [
                    first_nameUN, 
                    second_nameUN, 
                    third_nameUN, 
                    fourth_nameUN
                ]
            )            
            names.append(
                {
                    "whole_name": self.stripAdvance(whole_name).upper(),
                    "strong": True, 
                    "first_name": "", 
                    "last_name": ""
                }
            )
        else:
            names.append(
                {
                    "whole_name": self.stripAdvance(first_nameUN).upper(),
                    "strong": True, 
                    "first_name": "", 
                    "last_name": ""
                }
            )

        # Main Name Original Script
        
        name_original_script = self.lxmlFindText(listEntry, "NAME_ORIGINAL_SCRIPT", self.ns)
        if len(name_original_script) > 0:
            names.append(
                {
                    "whole_name": self.stripAdvance(name_original_script).upper(),
                    "strong": True, 
                    "first_name": "", 
                    "last_name": ""
                }
            )

        # Aliases

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":
            aliasesPath = "INDIVIDUAL_ALIAS"
        else:
            aliasesPath = "ENTITY_ALIAS"

        for alias in listEntry.findall(aliasesPath, namespaces=self.ns):            
            aliasName = self.lxmlFindText(alias, "ALIAS_NAME", self.ns)
            aliasName = self.stripAdvance(aliasName)
            if len(aliasName) > 0:
                quality = self.lxmlFindText(alias, "QUALITY", self.ns)
                strong = False if quality == "Low" else True                
                names.append(
                    {
                        "whole_name": aliasName.upper(),
                        "strong": strong, 
                        "first_name": "", 
                        "last_name": ""
                    }
                )

        return self.dedupDictsList(names)
    
    def getAddresses(self, listEntry):

        addresses = []

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":
            addressesPath = "INDIVIDUAL_ADDRESS"
        else:
            addressesPath = "ENTITY_ADDRESS"

        for address in listEntry.findall(addressesPath, namespaces = self.ns):
            street = self.lxmlFindText(address, "STREET", self.ns)
            city = self.lxmlFindText(address, "CITY", self.ns)
            country_subdivision = self.lxmlFindText(address, "STATE_PROVINCE", self.ns)
            country_ori =  self.lxmlFindText(address, "COUNTRY", self.ns)
            country_ori = self.stripAdvance(country_ori).upper()
            address = " ".join(
                [
                    street,
                    city,
                    country_subdivision,
                    country_ori   
                ]
            )
            address = self.stripAdvance(address)
            if len(address) > 0:
                country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                addresses.append(
                    {
                        "address": address.upper(),
                        "street": self.stripAdvance(street).upper(),
                        "city": self.stripAdvance(city).upper(),
                        "country_subdivision": self.stripAdvance(country_subdivision).upper(),
                        "country_ori": country_ori,
                        "country_ISO_code": country_ISO_code,
                        "country_desc": country_desc
                    }
                )
        return self.dedupDictsList(addresses)
    
    def getNationalities(self, listEntry):

        nationalities = []

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":
            for nationalityEl in listEntry.findall("NATIONALITY/VALUE", namespaces = self.ns):
                if nationalityEl.text is not None:
                    nationality_ori = nationalityEl.text 
                    nationality_ori = self.stripAdvance(nationality_ori).upper()
                else:
                    nationality_ori = ""
                if len(nationality_ori) > 0:
                    country_ISO_code = self.getISOCodeFromCountryName(nationality_ori)
                    country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                    nationalities.append(
                         {
                            "country_ori": nationality_ori,
                            "country_ISO_code": country_ISO_code,
                            "country_desc": country_desc
                        }
                    )

        return self.dedupDictsList(nationalities)

    def getDatesOfBirth(self, listEntry):

        datesOfBirth = []

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":
            for dobEl in listEntry.findall("INDIVIDUAL_DATE_OF_BIRTH", namespaces = self.ns):

                yearIni = self.lxmlFindText(dobEl, "FROM_YEAR", self.ns)
                yearEnd = self.lxmlFindText(dobEl, "TO_YEAR", self.ns)

                if len(yearIni) > 0 and len(yearEnd) > 0:

                    for year in range(int(yearIni), int(yearEnd) + 1, 1):
                        datesOfBirth.append(
                            {
                                "date_of_birth": "",
                                "year": str(year),
                                "month": "",
                                "day": ""
                            }
                        )

                else:

                    date_of_birth = self.lxmlFindText(dobEl, "DATE", self.ns)
                    if len(date_of_birth) > 0:
                        date_of_birthParts = date_of_birth.split("-")
                        day = date_of_birthParts[2]
                        month = date_of_birthParts[1]
                        year = date_of_birthParts[0]
                    else:
                        day = ""
                        month = ""
                        year = self.lxmlFindText(dobEl, "YEAR", self.ns)
                    if len(date_of_birth) > 0 or \
                       len(day) > 0 or \
                       len(month) > 0 or \
                       len(year) > 0:
                        datesOfBirth.append(
                            {
                                "date_of_birth": date_of_birth,
                                "year": year,
                                "month": month,
                                "day": day
                            }
                        )

        return self.dedupDictsList(datesOfBirth)
    
    def getPlacesOfBirth(self, listEntry):

        placesOfBirth = []

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":

            for pobEl in listEntry.findall("INDIVIDUAL_PLACE_OF_BIRTH", namespaces = self.ns):

                street = self.lxmlFindText(pobEl, "STREET", self.ns)
                city = self.lxmlFindText(pobEl, "CITY", self.ns)
                country_subdivision = self.lxmlFindText(pobEl, "STATE_PROVINCE", self.ns)
                country_ori = self.lxmlFindText(pobEl, "COUNTRY", self.ns)
                country_ori = self.stripAdvance(country_ori).upper()
                pob = " ".join(
                    [
                        street,
                        city,
                        country_subdivision,
                        country_ori
                    ]
                )               
                pob = self.stripAdvance(pob)
                if len(pob) > 0:
                    country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                    country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                    placesOfBirth.append(
                        {
                            "place_of_birth": pob.upper(),
                            "street": self.stripAdvance(street).upper(),
                            "city": self.stripAdvance(city).upper(),
                            "country_subdivision": self.stripAdvance(country_subdivision).upper(),
                            "country_ori": country_ori,
                            "country_ISO_code": country_ISO_code,
                            "country_desc": country_desc
                        }
                    )

        return self.dedupDictsList(placesOfBirth)
    
    def getIdentifications(self, listEntry):

        identifications = []

        if self.listEntryPath == ".//INDIVIDUALS/INDIVIDUAL":

            for IdEl in listEntry.findall("INDIVIDUAL_DOCUMENT", namespaces = self.ns):
                idNumber = self.lxmlFindText(IdEl, "NUMBER", self.ns)
                if len(idNumber) > 0:
                    idType = self.lxmlFindText(IdEl, "TYPE_OF_DOCUMENT", self.ns)
                    country1 = self.lxmlFindText(IdEl, "COUNTRY_OF_ISSUE", self.ns)
                    country1 = self.stripAdvance(country1).upper()
                    country2 = self.lxmlFindText(IdEl, "ISSUING_COUNTRY", self.ns)
                    country2 = self.stripAdvance(country2).upper()
                    if country1 == country2:
                        country_ori = country1
                    else:
                        if len(country1) > 0:
                            country_ori = country1
                        else:
                            country_ori = country2
                    country_ISO_code = self.getISOCodeFromCountryName(country_ori)
                    country_desc = self.getCountryNameFromISOCode(country_ISO_code)
                    identifications.append(
                        {
                            "type": self.stripAdvance(idType).upper(),
                            "id": idNumber,
                            "country_ori": country_ori,
                            "country_ISO_code": country_ISO_code,
                            "country_desc": country_desc
                        }
                    )

        return self.dedupDictsList(identifications)
    
    def getPrograms(self, listEntry):

        listType = self.lxmlFindText(listEntry, "UN_LIST_TYPE", ns=self.ns)
        listType = self.stripAdvance(listType)        
        
        if len(listType) > 0:
            return [listType]
        else:
            return []
        
    def getAddtionalInformation(self, listEntry):

        result = {}
        
        remarks = [self.lxmlFindText(listEntry, "COMMENTS1", ns=self.ns)]
        for designationEl in listEntry.findall("DESIGNATION/VALUE", namespaces=self.ns):
            if designationEl.text is not None:
                remarks.append(designationEl.text)

        remark = " ".join(remarks)
        remark = self.stripAdvance(remark)

        if len(remark) > 0:
            result["remarks"] = remark

        gender = self.lxmlFindText(listEntry, "GENDER", ns=self.ns)
        gender = self.stripAdvance(gender)
        if len(gender) > 0:                     
            result["gender"] = gender
        
        return result
    
def load(data, loader=Loader, *args, **kwargs):
    return loader(*args, **kwargs).load(data)