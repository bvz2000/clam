import os

from clam import clam
from clam.clamerror import ClamError

if "CLAM_LANGUAGE" in os.environ:
    language = os.environ["CLAM_LANGUAGE"]
else:
    language = "english"

clam_obj = clam.Clam(language)
contexts = clam_obj.selection_to_context_list()

result = False
if contexts:
    result = clam_obj.validate_context_names(contexts, None, False)

published = list()
if result:
    for context in contexts:
        try:
            clam_obj.publish_context(context)
        except ClamError as e:
            print e.message
        published.append(context)

