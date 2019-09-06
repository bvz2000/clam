import os

from clam import clam

if "CLAM_LANGUAGE" in os.environ:
    language = os.environ["CLAM_LANGUAGE"]
else:
    language = "english"

clam_obj = clam.Clam(language)
contexts = clam_obj.selection_to_context_list()

if contexts:
    clam_obj.validate_context_names(contexts, None, True)
