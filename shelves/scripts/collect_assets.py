# This is meant to run inside of Clarisse

import os.path

try:
    import ix
except ImportError:
    ix = None

from libClarisse import libClarisse


# ---------------------------------------------------------------------------
def reformat_names():

    for asset in assets:

        # Split the existing name up
        asset_url = os.path.split(asset.get_full_name())[0]
        name = asset.get_name()
        base, variant = name.rsplit("_", 1)
        type_name, cat, desc = base.split("_", 2)

        # convert from camel case and set capitalizations
        desc_out = ""
        last_char_was_upper = False
        for char in desc:
            if char == char.upper():
                if last_char_was_upper:
                    desc_out += char.lower()
                    last_char_was_upper = True
                else:
                    desc_out += "_" + char.lower()
            else:
                desc_out += char.lower()

        # Build the new name, and replace any double underscores
        new_name = "_".join((type_name, cat, desc_out, variant.upper()))
        while "__" in new_name:
            new_name = new_name.replace("__", "_")

        # Rename the out node and the shading layer and material
        ix.cmds.RenameItem(
            asset.get_full_name() + "/" + asset.get_name() + "_OUT",
            new_name + "_var1_OUT")
        ix.cmds.RenameItem(
            asset.get_full_name() + "/" + asset.get_name() + "_sl",
            new_name + "_sl")
        ix.cmds.RenameItem(
            asset.get_full_name() + "/shading/shaders/" + asset.get_name() + "_MAT",
            new_name + "_MAT")

        sl_url = asset_url + "/" + name + "/" + new_name + "_sl"
        sl = ix.get_item(sl_url)

        # Get a count of the items and contexts in the geo sub-context
        geo_ctx = asset.get_context("geo")
        sub_ctx_count = geo_ctx.get_context_count()
        sub_item_count = geo_ctx.get_object_count()

        if sub_ctx_count == 1:
            abc_ctx = geo_ctx.get_context(0)
        else:
            for i in range(sub_item_count):
                if geo_ctx.get_item(i).get_name() != "geo_gr":
                    abc_ctx = geo_ctx.get_item(i)
                    break
        ix.cmds.RenameItem(abc_ctx.get_full_name(), new_name + "_abc")

        # TODO: Find the referenced alembic files (all of them first) then rename them (take into account lv# values in the name)

        # TODO: If there are multiple alembic references to the same file, collapse them into a single ref.

        var_url = geo_ctx.get_full_name() + "/var1"
        libClarisse.create_context(var_url)
        ix.cmds.MoveItemsTo([geo_ctx.get_full_name() + "/" + new_name + "_abc"], var_url)
        ix.cmds.MoveItemsTo([geo_ctx.get_full_name() + "/geo_gr"], var_url)

        attr = libClarisse.get_attribute_obj(sl, "shading_layer_filters")
        values = libClarisse.get_all_attribute_values(attr)

        for i in range(len(values)):
            old_filter = values[i]
            new_filter = old_filter.replace(name, new_name)
            print old_filter, new_filter
            ix.cmds.SetShadingLayerRulesProperty(sl_url,
                                                 [i],
                                                 "filter",
                                                 [new_filter])

        ix.cmds.RenameItem(asset.get_full_name(), new_name)


assets = list()
for thing in ix.selection:
    assets.append(thing)

reformat_names()