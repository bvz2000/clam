from libClarisse import libClarisse


def do_it():

    contexts = libClarisse.selection_to_context_list()

    libClarisse.make_contexts_atomic(contexts)


do_it()
