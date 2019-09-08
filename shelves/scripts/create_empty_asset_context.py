import os

try:
    import ix
except ImportError:
    ix = None

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

    if not libClarisse.save_snapshot():
        title = clam_obj.resc.message("error")
        body = clam_obj.resc.error(104).msg
        libClarisseGui.display_error_dialog(body, title)
        return

    if ix.selection.get_count() == 0 or not ix.selection[0].is_context():
        title = clam_obj.resc.message("Select_context_title")
        body = clam_obj.resc.message("Select_context_body")
        libClarisseGui.display_error_dialog(body, title)
        return

    if ix.selection.get_count() > 1:
        existing_geo = libClarisse.clarisse_array_to_python_list(ix.selection)
        existing_geo = existing_geo[1:]
        variant_count = len(existing_geo)
    else:
        existing_geo = None
        variant_count = 1

    # TODO: Get a name from the user via a GUI
    try:
        clam_obj.create_empty_asset_structure(name="asset_veh_bob_A",
                                              parent_context=ix.selection[0],
                                              existing_geo=existing_geo,
                                              variant_count=variant_count)
    except ClamError as e:
        title = clam_obj.resc.message("error")
        body = str(e.message)
        libClarisseGui.display_error_dialog(body, title)
        return


do_it()
