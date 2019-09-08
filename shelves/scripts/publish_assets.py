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

    result = False
    if contexts:
        result = clam_obj.validate_context_names(contexts, None, False)

    published = list()
    if result:
        for context in contexts:
            try:
                clam_obj.publish_context(context)
            except ClamError as e:
                title = clam_obj.resc.message("error")
                libClarisseGui.display_error_dialog(title, e.message)
            published.append(context)

    title = clam_obj.resc.message("publish_success_title")
    body = clam_obj.resc.message("publish_success_body")
    libClarisseGui.display_message_dialog(body, title)


do_it()
