import os

from libClarisse import libClarisseGui

from clam import clam
from clam.clamerror import ClamError


def do_it():

    if "CLAM_LANGUAGE" in os.environ:
        language = os.environ["CLAM_LANGUAGE"]
    else:
        language = "english"

    # TODO: Switch to reading this from the .ini resources file
    dest = libClarisseGui.display_get_path_dialog("Enter Path Where Gathered Files Should Live")

    clam_obj = clam.Clam(language)
    contexts = clam_obj.selection_to_context_list()

    for context in contexts:
        try:
            clam_obj.gather_context(context, dest)
        except ClamError as e:
            print e.message
            return


do_it()
