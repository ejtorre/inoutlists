import unittest
import inoutlists
from pathlib import Path
import os
import pandas as pd

class TestResFiles(unittest.TestCase):

    def setUp(self):
        filePath = Path(os.path.abspath(inoutlists.__file__)).parent
        self.df_ISO_Codes = pd.read_csv(
            Path(filePath, "country_ISO_codes.csv"),
            sep="\t",
            encoding="utf-8"
        )
        self.df_Country_Names = pd.read_csv(
            Path(filePath, "country_names.csv"),
            sep="\t",
            encoding="utf-8"
        )

    def test_country_ISO_codes_file_duplicates_ISO_code(self):        
        dfDup = self.df_ISO_Codes[
            self.df_ISO_Codes.duplicated("ISO2_CODE", keep="first")
        ]
        self.assertEqual(len(dfDup), 0)

    def test_country_names_file_duplicates_country_name(self):
        dfDup = self.df_Country_Names[
            self.df_Country_Names.duplicated("COUNTRY_NAME", keep="first")
        ]
        self.assertEqual(len(dfDup), 0)

    def test_country_names_ISO_Code_orphans(self):
        df_Country_Names_ISO_Codes = self.df_Country_Names.drop_duplicates(
            "ISO2_CODE", keep="first"
        )
        df_ISO_Codes_no_dup = self.df_ISO_Codes.drop_duplicates(
            "ISO2_CODE", 
            keep="first"
        )
        df = df_Country_Names_ISO_Codes.merge(
            df_ISO_Codes_no_dup[["ISO2_CODE", "ISO3_CODE"]], 
            how="outer", 
            on="ISO2_CODE",
            indicator=True
        )
        with self.subTest(test="Country names not in ISO Codes file"):
            self.assertEqual(
                len(df[df._merge == "left_only"]), 
                0,
                f'{df[df._merge == "left_only"]}'
            )
        with self.subTest(test="ISO codes not in country names file"):
            self.assertEqual(
                len(df[df._merge == "right_only"]), 
                0,
                f'{df[df._merge == "right_only"]}'
            )

if __name__ == '__main__':
    unittest.main()