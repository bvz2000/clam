import os

try:
    import ix
except ImportError:
    ix = None

from libClarisse import libClarisse

from clam import clam


def do_it():

    if "CLAM_LANGUAGE" in os.environ:
        language = os.environ["CLAM_LANGUAGE"]
    else:
        language = "english"

    clam_obj = clam.Clam(language)
    contexts = clam_obj.selection_to_context_list()

    libClarisse.make_contexts_atomic(contexts)


do_it()
