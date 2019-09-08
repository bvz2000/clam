import os

from clam import clam
from clam.clamerror import ClamError

from libClarisse import libClarisse
from libClarisse import libClarisseGui


def do_it():

    if "CLAM_LANGUAGE" in os.environ:
        language = os.environ["CLAM_LANGUAGE"]
    else:
        language = "english"

    clam_obj = clam.Clam(language)
    contexts = libClarisse.selection_to_context_list()

    body = clam_obj.resc.message("get_gather_path_body")
    dest = libClarisseGui.display_get_path_dialog(body)

    for context in contexts:
        try:
            clam_obj.gather_context(context, dest)
        except ClamError as e:
            libClarisseGui.display_error_dialog(e.message, "Error")
            return

    title = clam_obj.resc.message("done_gathering_title")
    body = clam_obj.resc.message("done_gathering_body")
    libClarisseGui.display_message_dialog(body, title)


do_it()
