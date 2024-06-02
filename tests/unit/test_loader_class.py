import unittest
from inoutlists import Loader

class TestLoaderClass(unittest.TestCase):

    def setUp(self):
        self.loader = Loader("test")

    def test_getISOCodeFromCountryName(self):        
        countryNames = {
            "XXXXXXXXXX": "00",
            "USSR": "SU",
            "WEST BANK (PALESTINIAN AUTHORITY)": "PS"
        }
        for countryName, ISOCode in countryNames.items():
            with self.subTest(countryName=countryName):
                self.assertEqual(
                    self.loader.getISOCodeFromCountryName(countryName), 
                    ISOCode,
                    f'Wrong ISO Code for country name {countryName}'
                )
    
    def test_getCountryNameFromISOCode(self):
        ISOCodes = {
            "XX": "UNKNOWN",
            "PS": "PALESTINE",
            "00": "UNKNOWN",
            "CS": "SERBIA AND MONTENEGRO"
        }
        for ISOCode, countryName in ISOCodes.items():
            with self.subTest(ISOCode=ISOCode):
                self.assertEqual(
                    self.loader.getCountryNameFromISOCode(ISOCode), 
                    countryName,
                    f'Wrong country name for ISO Code {ISOCode}'
                )

if __name__ == '__main__':
    unittest.main()