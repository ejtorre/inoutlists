# inoutlists

inoutlists is a python package to parse and normalize different sources of lists (OFAC, EU, UN, etc) to a common dictionary interface. 

Once the lists are parsed and normalized, the user can dump the information to other formats such as JSON, CSV or a Pandas data frame for further research or transfer to other systems. 

Moreover, the package can be extended to parse any kind of source creating specific Loaders classes or to dump the information to any kind of formats creating specific Dumpers classes. 

## Basic Usage

inoutlists main entry points are the functions load and dump:

### inoutlists.load(data, loader=Loader, *args, **kwargs)

Parameters:

- data: The data to parse. The type of the data parameter depends on the Loader chosen. It could be a url, a file, a string, etc.
- loader: Loader class. The loader class must inherit from the class Loader. It defines the logic of the transformation from the data to the common dictionary interface implementing the methods defined in the class Loader, specially the function load.
- *args, **kwargs. Positional arguments and keyword arguments passed to the loader class.

Returns: Dictionary. The list in the dictionary common interface.

### inoutlists.dump(data, dumper=Dumper, *args, **kwargs)

Parameters:

- data: An python dictionary based on the common interface.
- dumper. Dumper class. The dumper class must inherit from the class Dumper. It defines the logic of the transformation from the dictionary common interface to the target format implementing the method dump.
- *args, **kwargs. Positional arguments and keyword arguments passed to the dumper class.

Returns: Any. It depends on the Dumper class.

```python
>>> from inoutlists import load, dump, LoaderOFACXML, DumperPandas, DumperJSON
>>> from pprint import pprint 
>>> OFAC_SDN_URL = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"
>>> OFAC_SDN = load(OFAC_SDN_URL, loader=LoaderOFACXML, description="OFAC SDN list")
>>> pprint(OFAC_SDN.keys())
dict_keys(['meta', 'list_entries'])
>>> pprint(OFAC_SDN["meta"])
{'description': 'OFAC SDN list',
 'list_date': '2024-05-24',
 'source': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML'}
>>> pprint(f'# list entries: {len(OFAC_SDN["list_entries"])}')
 '# list entries: 14978'
>>> pprint(f'{OFAC_SDN["list_entries"][0]}')
 ("{'id': '36', 'type': 'O', 'names': [{'whole_name': 'AEROCARIBBEAN AIRLINES', "
 "'strong': True, 'first_name': '', 'last_name': ''}, {'whole_name': "
 "'AERO-CARIBBEAN', 'strong': True, 'first_name': '', 'last_name': ''}], "
 "'addresses': [{'address': 'HAVANA CUBA', 'street': '', 'city': 'HAVANA', "
 "'country_subdivision': '', 'country_ori': 'CUBA', 'country_ISO_code': 'CU', "
 "'country_desc': 'CUBA'}], 'programs': ['CUBA']}")
>>> df = dump(OFAC_SDN, dumper=DumperPandas)
>>> pprint(df[df.type=="O"].iloc[0].T)
id                                                                                 10001
type                                                                                   O
names_whole_name                                INVERSIONES MACARNIC PATINO Y CIA S.C.S.
names_strong                                                                        True
names_first_name                                                                        
names_last_name                                                                         
addresses_address                      CALLE 19 NO. 9-50 OFC. 505 OFC. 505 PEREIRA RI...
addresses_street                                     CALLE 19 NO. 9-50 OFC. 505 OFC. 505
addresses_city                                                                   PEREIRA
addresses_country_subdivision                                                  RISARALDA
addresses_country_ori                                                           COLOMBIA
addresses_country_ISO_code                                                            CO
addresses_country_desc                                                          COLOMBIA
nationalities_country_ori                                                            NaN
nationalities_country_ISO_code                                                       NaN
nationalities_country_desc                                                           NaN
dates_of_birth_date_of_birth                                                         NaN
dates_of_birth_year                                                                  NaN
dates_of_birth_month                                                                 NaN
dates_of_birth_day                                                                   NaN
places_of_birth_place_of_birth                                                       NaN
places_of_birth_street                                                               NaN
places_of_birth_city                                                                 NaN
places_of_birth_country_subdivision                                                  NaN
places_of_birth_country_ori                                                          NaN
places_of_birth_country_ISO_code                                                     NaN
places_of_birth_country_desc                                                         NaN
identifications_type                                                               NIT #
identifications_id                                                           816005011-4
identifications_country_ori                                                     COLOMBIA
identifications_country_ISO_code                                                      CO
identifications_country_desc                                                    COLOMBIA
programs                                                                            SDNT
source                                                                          OFAC SDN
Name: 32, dtype: object
>>> OFAC_SDN_JSON = dump(OFAC_SDN, dumper=DumperJSON)
>>> pprint(OFAC_SDN_JSON[0:200])
('{"meta": {"description": "OFAC SDN list", "source": '
 '"https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML", '
 '"list_date": "2024-05-24"}, "list_entries": [{"id": "36", "typ')
```

## Installing inoutlists

```console
$ python -m pip install inoutlists
```

## Current loaders distributed with inoutlists

- Loader. Generic loader class. All the loader classes must inherit and implement the methods defined in this class.

- LoaderXML. Generic class for loading lists based on XML. The data parameter of the load function can be the url of the xml file, a OS path to the file or a string. Parameters:
    - description: string for informative purposes. Default: ""
    - schema: Path object to the schema. Used to validate the data. Default: OFAC_xml.xsd. The OFAC schema distributed with the package.

- LoaderOFACXML. Class for parsing lists distributed by OFAC [SDN list](https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML) and [OFAC Consolidated](https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONSOLIDATED.XML). It inherits from class LoaderXML. Parameters:
    - description: string for informative purposes. Default: ""
    - schema: Path object to the schema. Used to validate the data. Default: OFAC_xml.xsd. The OFAC schema distributed with the package.

- LoaderEUXML. Class for parsing lists distributed by EU on [EU sanctions list source](https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw). It inherits from class LoaderXML. Parameters:
    - description: string for informative purposes. Default: ""
    - schema: Path object to the schema. Used to validate the data. Default: EU_20171012-FULL-schema-1_1(xsd).xsd. The EU schema distributed with the package.

- LoaderUNXML. Class for parsing lists distributed by UN on [UN sanctions list source](https://scsanctions.un.org/resources/xml/en/consolidated.xml). It inherits from class LoaderXML. Parameters:
    - description: string for informative purposes. Default: ""
    - schema: Path object to the schema. Used to validate the data. Default: UN_consolidated.xsd. The UN schema distributed with the package.


## Current dumpers distributed with inoutlists

- Dumper. Generic dumper class. All the dumper classes must inherit and implement the methods defined in this class.

- DumperJSON. Dumper class for dumping the parsed list as a dictionary common interface to JSON. The parameter output of the dump method can be a string or path representing a file. If that parameter is not provided then returns a data as a string. It accepts all the keyword arguments of the functions dump and dumps of the JSON package.

- DumperPandas: Dumper class for dumping the parsed list as a dictionary common interface to a Pandas data frame. Because the dictionary common interface there one to many relations (several names, several addresses, etc) the returned data frame represents the cartesian product of those relations. 

- DumperCSV: Dumper class for dumping the parsed list as a dictionary common interface to csv. The data is dumped following the same rules of the DumperPandas class. The parameter output of the dump method can be a string or path representing a file. If that parameter is not provided then returns a the data as a string. It accepts all the keywords arguments of the method to_csv of a Pandas data frame.