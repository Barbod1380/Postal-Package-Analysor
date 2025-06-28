import streamlit as st
from utils.file_utils import parse_digits_from_file, parse_words_from_file


def label_digits(group_key: str, digits: list[int]):
    """
    Display improved digit labeling UI with batch selection and confirmation button.
    """
    st.markdown("### 🔢 Digit Labeling")

    if "digit_labels" not in st.session_state:
        st.session_state["digit_labels"] = {}

    # Display digits in a nice format
    st.markdown("**Detected Digits:**")
    digits_display = " - ".join([f"**{i}**: {digit}" for i, digit in enumerate(digits)])
    st.markdown(digits_display)
    
    # Get current labels for this group
    group_labels = st.session_state["digit_labels"].get(group_key, {})
    
    # Get currently saved incorrect and unknown digits
    currently_incorrect = [i for i, data in group_labels.items() 
                          if isinstance(data, dict) and data.get("label") == "False" 
                          or data == "False"]
    currently_unknown = [i for i, data in group_labels.items() 
                        if isinstance(data, dict) and data.get("label") == "Unknown" 
                        or data == "Unknown"]

    # Create form for batch selection
    with st.form(key=f"digit_form_{group_key}"):
        st.markdown("#### Select Digits to Label:")
        
        # Create checkboxes for each digit in a grid layout
        cols = st.columns(5)  # 5 columns for better layout
        
        incorrect_selections = []
        unknown_selections = []
        
        for i, digit in enumerate(digits):
            col_idx = i % 5
            with cols[col_idx]:
                st.markdown(f"**Position {i}: {digit}**")
                
                # Determine current status
                current_status = "Correct"
                if i in currently_incorrect:
                    current_status = "Incorrect"
                elif i in currently_unknown:
                    current_status = "Unknown"
                
                # Radio button for each digit
                status = st.radio(
                    f"Status for digit {digit}:",
                    options=["Correct", "Incorrect", "Unknown"],
                    index=["Correct", "Incorrect", "Unknown"].index(current_status),
                    key=f"digit_status_{group_key}_{i}",
                    label_visibility="collapsed"
                )
                
                if status == "Incorrect":
                    incorrect_selections.append(i)
                elif status == "Unknown":
                    unknown_selections.append(i)
        
        st.markdown("---")
        
        # Collect correct values for incorrect digits
        correct_values = {}
        if incorrect_selections:
            st.markdown("#### ✏️ Enter Correct Values for Incorrect Digits:")
            correct_cols = st.columns(min(len(incorrect_selections), 5))
            
            for idx, pos in enumerate(incorrect_selections):
                col_idx = idx % 5
                with correct_cols[col_idx]:
                    predicted_digit = digits[pos]
                    
                    # Get current correct value if it exists
                    current_correct = 0
                    if pos in group_labels and isinstance(group_labels[pos], dict):
                        current_correct = group_labels[pos].get("correct_value", 0)
                    
                    correct_value = st.selectbox(
                        f"Pos {pos} ({predicted_digit}) →",
                        options=list(range(10)),
                        index=current_correct,
                        key=f"correct_value_{group_key}_{pos}"
                    )
                    correct_values[pos] = correct_value

        # Submit button
        submitted = st.form_submit_button("✅ Apply Digit Labels", use_container_width=True)
        
        if submitted:
            # Update labels based on selections
            new_labels = {}
            for i in range(len(digits)):
                if i in incorrect_selections:
                    new_labels[i] = {
                        "label": "False",
                        "predicted": digits[i],
                        "correct_value": correct_values.get(i, 0)
                    }
                elif i in unknown_selections:
                    new_labels[i] = {"label": "Unknown", "predicted": digits[i]}
                else:
                    new_labels[i] = {"label": "True", "predicted": digits[i]}
            
            st.session_state["digit_labels"][group_key] = new_labels
            st.success("✅ Digit labels updated successfully!")
            st.rerun()

    # Show current summary outside the form
    if group_labels:
        correct_count = len([i for i, data in group_labels.items() 
                           if isinstance(data, dict) and data.get("label") == "True" 
                           or data == "True"])
        incorrect_count = len([i for i, data in group_labels.items() 
                             if isinstance(data, dict) and data.get("label") == "False" 
                             or data == "False"])
        unknown_count = len([i for i, data in group_labels.items() 
                           if isinstance(data, dict) and data.get("label") == "Unknown" 
                           or data == "Unknown"])
        
        st.info(f"Current Status: ✅ {correct_count} correct  |  ❌ {incorrect_count} incorrect  |  ❓ {unknown_count} unclear")


def label_words(group_key: str, words: list[str]):
    """
    Display word labeling UI with batch updates for better performance.
    """
    st.markdown("### 📝 Word Labeling")

    if "word_labels" not in st.session_state:
        st.session_state["word_labels"] = {}
    if "missed_words" not in st.session_state:
        st.session_state["missed_words"] = {}

    # Get current labels for this group
    word_labels = st.session_state["word_labels"].get(group_key, {})
    
    # Display detected words
    st.markdown("**Detected Words:**")
    words_display = "`, `".join(words)
    st.markdown(f"`{words_display}`")
    
    # Get currently marked incorrect words
    currently_incorrect = [word for word, label in word_labels.items() if label == "False"]
    
    # Create a form for batch updates
    with st.form(f"word_form_{group_key}"):
        # Multiselect for incorrect words (won't trigger immediate updates)
        incorrect_words = st.multiselect(
            "⚠️ Select words that are INCORRECTLY detected:",
            options=words,
            default=currently_incorrect,
            help="Select all incorrect words, then click 'Apply Changes' below"
        )
        
        # Submit button for batch update
        submitted = st.form_submit_button("✅ Apply Word Labels", type="primary")
        
        if submitted:
            # Update word labels based on selection
            new_word_labels = {}
            for word in words:
                if word in incorrect_words:
                    new_word_labels[word] = "False"
                else:
                    new_word_labels[word] = "True"
            
            st.session_state["word_labels"][group_key] = new_word_labels
            st.success(f"Updated labels for {len(words)} words!")
    
    # Show current status (outside form to avoid conflicts)
    if word_labels:  # Only show if labels exist
        correct_count = len([w for w, label in word_labels.items() if label == "True"])
        incorrect_count = len([w for w, label in word_labels.items() if label == "False"])
        st.info(f"✅ {correct_count} correct, ❌ {incorrect_count} incorrect")

    # Add missed words section
    st.markdown("#### ➕ Add Missed Words")
    with st.form(f"missed_words_form_{group_key}"):
        missed_input = st.text_area(
            "Enter missed words (کلمات از دست رفته را وارد کنید):",
            placeholder="word1, word2, word3",
            help="Separate multiple words with commas"
        )
        
        missed_submitted = st.form_submit_button("💾 Save Missed Words")
        
        if missed_submitted and missed_input:
            missed_list = [w.strip() for w in missed_input.split(",") if w.strip()]
            st.session_state["missed_words"][group_key] = missed_list
            st.success(f"Saved {len(missed_list)} missed words!")
    
    # Display current missed words
    if group_key in st.session_state["missed_words"]:
        missed_list = st.session_state["missed_words"][group_key]
        if missed_list:
            st.markdown(f"**Current Missed Words:** `{', '.join(missed_list)}`")