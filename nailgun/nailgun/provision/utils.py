from __future__ import absolute_import

import cobbler.item_distro as item_distro
import cobbler.item_profile as item_profile
import cobbler.item_system as item_system
import cobbler.item_repo as item_repo
import cobbler.item_image as item_image
import cobbler.item_mgmtclass as item_mgmtclass
import cobbler.item_package as item_package
import cobbler.item_file as item_file


def get_fields(what='system'):
    if what == "distro":
        field_data = item_distro.FIELDS
    if what == "profile":
        field_data = item_profile.FIELDS
    if what == "system":
        field_data = item_system.FIELDS

    elements = {}
    fields = []
    interface_fields = []

    for row in field_data:

        elem = {
            "name": row[0],
            "dname": row[0].replace("*", ""),
            "caption": row[3],
            "editable": row[4],
            "tooltip": row[5],
            "choices": row[6],
        }

        elements[elem["name"]] = elem

        if not elem.get("editable", False):
            continue

        # widgets are not real fields
        if elem["name"].find("_widget") != -1:
            continue

        if elem["name"].startswith("*"):
            interface_fields.append(elem["dname"])
        else:
            fields.append(elem["dname"])

    return {
        'fields': fields,
        'interface_fields': interface_fields,
        'elements': elements,
    }
