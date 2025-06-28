import pandas as pd
from typing import Dict, Any
from collections import defaultdict
import streamlit as st

def generate_annotation_csv() -> pd.DataFrame:
    """
    Combines group labels, digit labels, word labels, and missed words
    into a flat CSV-compatible DataFrame.
    Now handles multiple group labels per group.
    """
    group_labels = dict(st.session_state.get("group_labels", {}))
    digit_labels = dict(st.session_state.get("digit_labels", {}))
    word_labels = dict(st.session_state.get("word_labels", {}))
    missed_words = dict(st.session_state.get("missed_words", {}))

    # Collect all keys (groups)
    all_keys = set(group_labels.keys()) | set(digit_labels.keys()) | set(word_labels.keys())

    rows = []

    for group_key in sorted(all_keys):
        row = {
            "group_key": group_key,
        }
        
        # Handle group labels - can be string (old format) or list (new format)
        group_label = group_labels.get(group_key, "")
        if isinstance(group_label, list):
            row["group_label"] = "; ".join(group_label)  # Join multiple labels with semicolon
        else:
            row["group_label"] = group_label  # Keep single label as is

        # Digits: handle both old and new format
        digit_data = digit_labels.get(group_key, {})
        for i, data in digit_data.items():
            if isinstance(data, dict):
                # New format with detailed info
                row[f"digit_{i}"] = data.get("label", "")
                row[f"digit_{i}_predicted"] = data.get("predicted", "")
                if data.get("label") == "False":
                    row[f"digit_{i}_correct"] = data.get("correct_value", "")
            else:
                # Old format (backward compatibility)
                row[f"digit_{i}"] = data

        # Words: flatten word_W
        for word, label in word_labels.get(group_key, {}).items():
            row[f"word_{word}"] = label

        # Missed Words
        missed = missed_words.get(group_key, [])
        row["missed_words"] = ", ".join(missed)

        rows.append(row)

    return pd.DataFrame(rows)