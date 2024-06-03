import json
import pandas as pd

__all__ = [
    "dump",
    "Dumper",
    "DumperJSON",
    "DumperPandas",
    "DumperCSV"

]

class Dumper():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def dump(self, data):
        pass

class DumperJSON(Dumper):

    def dump(self, data):
        output = self.kwargs.get("output", None)
        if output is None:
            return json.dumps(data, **self.kwargs)
        else:
            kwargs = {k:v for k,v in self.kwargs.items() if k != "output"}
            try:
                with open(output, mode="w", encoding="utf-8") as fileOut:
                    json.dump(data, fileOut, **kwargs)
                return True
            except OSError as err:
                print("OS error:", err)
                return False
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                return False

class DumperPandas(Dumper):

    def dump(self, data):        

        metaFields = [
            "id",
            "type"
        ]
        
        recordFields = {
            "names": {"dict": True},
            "addresses": {"dict": True},
            "nationalities": {"dict": True},
            "dates_of_birth": {"dict": True},
            "places_of_birth": {"dict": True},
            "identifications": {"dict": True},
            "programs": {"dict": False}
        }

        df = pd.DataFrame({metafield:[] for metafield in metaFields})

        for recordFieldName, recordFieldInfo in recordFields.items():
            dataNorm = [
                {k:v for k, v in x.items() if k in metaFields + [recordFieldName]}
                for x in data["list_entries"]
            ]
            dataNormUpdate = [
                x.update({recordFieldName: []}) 
                for x in dataNorm if recordFieldName not in x.keys()
            ]
            if recordFieldInfo["dict"]:
                dfRecordField = pd.json_normalize(
                    dataNorm, 
                    recordFieldName, 
                    metaFields,
                    record_prefix = f'{recordFieldName}_'
                )
            else:
                dfRecordField = pd.json_normalize(
                    dataNorm, 
                    recordFieldName, 
                    metaFields                    
                )
                dfRecordField.rename(
                    columns = {0: recordFieldName},
                    inplace=True)
            df = df.merge(dfRecordField, how="outer", on = metaFields)

        return df
    
class DumperCSV(Dumper):
    
    def dump(self, data):
        output = self.kwargs.get("output", None)        
        df = dump(data, dumper=DumperPandas)
        if output is None:
            return df.to_csv(**self.kwargs)
        else:
            kwargs = {k:v for k,v in self.kwargs.items() if k != "output"}
            try:
                df.to_csv(output, **kwargs)
                return True
            except OSError as err:
                print("OS error:", err)
                return False            
            except Exception as err:
                print(f"{err=}, {type(err)=}")
                return False
            
def dump(data, dumper=Dumper, *args, **kwargs):
    return dumper(*args, **kwargs).dump(data)