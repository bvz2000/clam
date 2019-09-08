import os

from clam import clam

from libClarisse import libClarisse
from libClarisse import libClarisseGui


def do_it():

    if "CLAM_LANGUAGE" in os.environ:
        language = os.environ["CLAM_LANGUAGE"]
    else:
        language = "english"

    clam_obj = clam.Clam(language)
    contexts = libClarisse.selection_to_context_list()

    if contexts:
        if not clam_obj.validate_context_names(contexts, None, True):
            title = clam_obj.resc.message("failed_name_title")
            failed = ""
            for invalid_name in clam_obj.invalid_asset_names:
                failed += "\n    \""
                failed += invalid_name
                failed += "\" - "
                failed += clam_obj.invalid_asset_names[invalid_name]
            body = clam_obj.resc.message("failed_name_body")
            body = body.format(failed=failed)
            libClarisseGui.display_message_dialog(body, title)
        else:
            title = clam_obj.resc.message("name_success_title")
            body = clam_obj.resc.message("name_success_body")
            libClarisseGui.display_message_dialog(body, title)


do_it()
