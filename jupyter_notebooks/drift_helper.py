"""
Helper functions to print drift information in a readable manner
"""

import pandas as pd


def friendly_name(entity_type, row, key_columns):
    """
    Returns a readable string as key, value pairs for an entity in a Pandas row.
    """
    return ", ".join([f"{key}={row[key]}" for key in key_columns])


def diff_properties(diff_frame, entity_type, key_columns, properties):
    """
    Prints the content of the diff_frame that is the answer of a differential
    Batfish question, run for the specified entity_type and properties.

    The entity is described using the key_columns parameter.
    """
    if len(diff_frame) == 0:
        print(f"{entity_type} properties are identical across the two snapshot")
        return
    snapshot_only = diff_frame[diff_frame["KeyPresence"] == "Only in Snapshot"]
    reference_only = diff_frame[diff_frame["KeyPresence"] == "Only in Reference"]
    both = diff_frame[diff_frame["KeyPresence"] == "In both"]
    if len(snapshot_only) > 0:
        print(f"\n{entity_type}s only in snapshot")
        for index, row in snapshot_only.iterrows():
            print(f"    {friendly_name(entity_type, row, key_columns)}")
    if len(reference_only) > 0:
        print(f"\n{entity_type}s only in reference")
        for index, row in reference_only.iterrows():
            print(f"    {friendly_name(entity_type, row, key_columns)}")
    for index, row in both.iterrows():
        print(
            "\nDifferences for {}".format(friendly_name(entity_type, row, key_columns))
        )
        for property in properties:
            snapshot_setting = row[f"Snapshot_{property}"]
            reference_setting = row[f"Reference_{property}"]
            if snapshot_setting != reference_setting:
                print(f"    {property}: {reference_setting} -> {snapshot_setting}")


def diff_frames(snapshot_frame, reference_frame, entity_type):
    """
    Prints the differences between snapshot and reference information about entity_type.
    """
    combined = pd.merge(snapshot_frame, reference_frame, how="outer", indicator=True)
    snapshot_only = combined[combined["_merge"] == "left_only"]
    reference_only = combined[combined["_merge"] == "right_only"]
    if len(snapshot_only) > 0:
        print(f"\n{entity_type}s only in snapshot")
        for index, row in snapshot_only.iterrows():
            print(
                "    ",
                friendly_name(entity_type, row, set(combined.columns) - {"_merge"}),
            )
    if len(reference_only) > 0:
        print(f"\n{entity_type}s only in reference")
        for index, row in reference_only.iterrows():
            print(
                "    ",
                friendly_name(entity_type, row, set(combined.columns) - {"_merge"}),
            )
    if len(snapshot_only) == 0 and len(reference_only) == 0:
        print(f"\n{entity_type}s are identical across the two snapshots")
