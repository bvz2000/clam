import os

try:
    import ix
except ImportError:
    ix = None

from clam import clam

if "CLAM_LANGUAGE" in os.environ:
    language = os.environ["CLAM_LANGUAGE"]
else:
    language = "english"

clam_obj = clam.Clam(language)
clam_obj.create_empty_asset_structure("asset_bldg_test_A",
                                      ix.selection[0])
