import streamlit as st

# Define your 6 error categories
ERROR_CATEGORIES = [
    "Wrong receiver",
    "Wrong postcode",
    "Bad image quality",
    "Poor preprocessing",
    "Postcode digit detection error",
    "Receiver word detection error"
]

def classify_group(group_key: str):
    """ظ
    Renders a classification multiselect for the given image group.
    Allows multiple labels per group. Saves the selected labels in Streamlit session state.
    """
    st.markdown("### 🏷️ Classify This Image Group")

    # Define session storage
    if "group_labels" not in st.session_state:
        st.session_state["group_labels"] = {}

    # Get current values (if already labeled) - handle both old single values and new lists
    current_values = st.session_state["group_labels"].get(group_key, [])
    
    # Handle backward compatibility: convert single string to list
    if isinstance(current_values, str):
        current_values = [current_values] if current_values else []

    # Show UI with multiselect
    selected = st.multiselect(
        "Select one or more labels for this group:",
        options=ERROR_CATEGORIES,
        default=current_values,
        help="You can select multiple error types if they apply to this group"
    )

    # Save to session state
    st.session_state["group_labels"][group_key] = selected
    
    # Display current status
    if selected:
        if len(selected) == 1:
            st.success(f"Labeled as: {selected[0]}")
        else:
            labels_str = ", ".join(selected)
            st.success(f"Labeled as: {labels_str}")
    else:
        st.info("This group has not been labeled yet.")