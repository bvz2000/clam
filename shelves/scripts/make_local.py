from libClarisse import libClarisse


def do_it():

    contexts = libClarisse.selection_to_context_list()

    libClarisse.localize(contexts)


do_it()
