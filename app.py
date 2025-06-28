import streamlit as st
from utils.file_utils import extract_zip_to_tempdir, get_all_files_by_type, build_image_groups
from components.image_group_viewer import display_image_group
from utils.export_utils import generate_annotation_csv
from components.group_classifier import classify_group
from components.word_digit_labeler import label_digits, label_words
from utils.file_utils import parse_digits_from_file, parse_words_from_file
from components.visualization_dashboard import show_visualization_dashboard
import time


st.set_page_config(
    layout="wide", 
    page_title="Postal Image Viewer",
    page_icon="📬"
)

st.title("📬 Postal Package Image Analyzer")
st.markdown("*Efficient analysis and labeling of postal package images*")

# === FILE UPLOAD SECTION ===
st.markdown("### 📁 Upload Data")
uploaded_zip = st.file_uploader(
    "Upload zipped data folder:", 
    type="zip",
    help="Upload a ZIP file containing your image folders (images, postcode_raw, receiver_raw, etc.)"
)

if uploaded_zip:
    # Show file info
    file_size = uploaded_zip.size / (1024 * 1024)  # Convert to MB
    st.info(f"📦 Uploaded: **{uploaded_zip.name}** ({file_size:.1f} MB)")
    
    # Processing with enhanced loading states
    with st.container():
        st.markdown("### ⚙️ Processing Data")
        
        # Create placeholder for processing steps
        step_container = st.container()
        
        with step_container:
            # Step 1: Extraction
            with st.status("🔄 Extracting ZIP file...", expanded=True) as status:
                temp_dir = extract_zip_to_tempdir(uploaded_zip)
                status.update(label="✅ ZIP extraction complete!", state="complete")
            
            # Step 2: File scanning
            with st.status("🔍 Scanning and organizing files...", expanded=True) as status:
                file_dict = get_all_files_by_type(temp_dir)
                
                # Show file summary
                total_files = sum(len(files) for files in file_dict.values())
                st.write(f"📊 **Found {total_files} files across {len(file_dict)} categories:**")
                
                # Display file counts by category
                cols = st.columns(4)
                for i, (category, files) in enumerate(file_dict.items()):
                    with cols[i % 4]:
                        st.metric(category.replace("_", " ").title(), len(files))
                
                status.update(label="✅ File scanning complete!", state="complete")
            
            # Step 3: Group building
            with st.status("🏗️ Building image groups...", expanded=True) as status:
                groups = build_image_groups(file_dict)
                
                st.write(f"🎯 **Successfully created {len(groups)} image groups**")
                
                if len(groups) > 100:
                    st.warning(f"⚠️ Large dataset detected ({len(groups)} groups). Navigation and loading optimized for performance.")
                
                status.update(label="✅ Image groups ready!", state="complete")

    # === MAIN APPLICATION ===
    st.markdown("---")
    
    if not groups:
        st.error("⚠️ No valid image groups were found. Please check your upload structure.")
        st.markdown("""
        **Expected folder structure:**
        - `images/` - Original postal package images
        - `postcode_raw/` - Raw postcode region images  
        - `postcode_preprocessed/` - Processed postcode images
        - `receiver_raw/` - Raw receiver region images
        - `receiver_preprocessed/` - Processed receiver images
        - `digits/` - Text files with extracted digits
        - `words/` - Text files with extracted words
        """)
        st.stop()

    # Initialize current index in session state
    if "current_group_index" not in st.session_state:
        st.session_state.current_group_index = 0

    # === NAVIGATION SECTION ===
    st.markdown("### 🧭 Navigation")
    
    group_keys = list(groups.keys())
    total_groups = len(group_keys)
    current_index = st.session_state.current_group_index

    # Create navigation layout
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 2, 1, 1])

    with nav_col1:
        if st.button("⬅️ Previous", disabled=(current_index == 0)):
            st.session_state.current_group_index -= 1
            st.rerun()

    with nav_col2:
        # Jump to specific group
        jump_to = st.number_input(
            "Go to group:", 
            min_value=1, 
            max_value=total_groups, 
            value=current_index + 1,
            key="jump_input"
        )
        if st.button("🎯 Jump"):
            st.session_state.current_group_index = jump_to - 1
            st.rerun()

    with nav_col3:
        # Progress bar
        progress = (current_index + 1) / total_groups
        st.progress(progress)
        st.markdown(f"<h3 style='text-align: center;'>Group {current_index + 1} of {total_groups}</h3>", 
                    unsafe_allow_html=True)

    with nav_col4:
        # Quick stats
        labeled_groups = len([k for k in group_keys if k in st.session_state.get("group_labels", {})])
        st.metric("Progress", f"{labeled_groups}/{total_groups}")

    with nav_col5:
        if st.button("Next ➡️", disabled=(current_index == total_groups - 1)):
            st.session_state.current_group_index += 1
            st.rerun()

    # === CURRENT GROUP DISPLAY ===
    selected_key = group_keys[current_index]
    
    # Loading state for images
    with st.spinner("🖼️ Loading images..."):
        display_image_group(selected_key, groups[selected_key])

    # === IMPROVED LAYOUT ORGANIZATION ===
    st.markdown("---")
    classify_group(selected_key)

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("### 📋 Extracted Data")
        
        # Digits section with loading
        with st.container():
            if "digits" in groups[selected_key]:
                with st.spinner("Loading digits..."):
                    digits = parse_digits_from_file(groups[selected_key]["digits"])
                digits_str = " ".join(map(str, digits)) if digits else "(empty)"
                st.markdown("**🔢 Extracted Digits:**")
                st.code(digits_str, language=None)
            else:
                st.warning("No digits file found.")
        
        # Words section with loading
        with st.container():
            if "words" in groups[selected_key]:
                with st.spinner("Loading words..."):
                    words = parse_words_from_file(groups[selected_key]["words"])
                words_str = ", ".join(words) if words else "(empty)"
                st.markdown("**📝 Extracted Words:**")
                st.code(words_str, language=None)
            else:
                st.warning("No words file found.")

    with col2:
        # Word Labeling with loading state
        if "words" in groups[selected_key]:
            words = parse_words_from_file(groups[selected_key]["words"])
            if words:
                label_words(selected_key, words)
            else:
                st.info("No words detected to label.")
        else:
            st.info("No words file available.")

    with col3:
        # Digit Labeling with loading state
        if "digits" in groups[selected_key]:
            digits = parse_digits_from_file(groups[selected_key]["digits"])
            if digits:
                label_digits(selected_key, digits)
            else:
                st.info("No digits detected to label.")
        else:
            st.info("No digits file available.")

    # === EXPORT SECTION ===
    st.markdown("---")
    st.markdown("## 💾 Export Annotations")

    export_col1, export_col2 = st.columns([1, 1])
    
    with export_col1:
        if st.button("📊 Generate CSV", type="primary"):
            with st.spinner("Generating annotation data..."):
                df = generate_annotation_csv()
            st.success(f"✅ Generated CSV with {len(df)} rows")
            st.dataframe(df, use_container_width=True)

    with export_col2:
        # Quick export without preview
        if st.button("⚡ Quick Export"):
            with st.spinner("Preparing download..."):
                df = generate_annotation_csv()
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"postal_annotations_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

    # === VISUALIZATION DASHBOARD ===
    st.markdown("---")
    st.markdown("## 📊 Analytics Dashboard")
    with st.spinner("Loading analytics..."):
        show_visualization_dashboard()

else:
    # Welcome screen when no file is uploaded
    st.markdown("""
    ## 👋 Welcome to the Postal Package Image Analyzer
    
    This application helps you efficiently analyze and label postal package images and their extracted data.
    
    ### 🚀 Getting Started
    1. **Upload** your ZIP file containing organized image folders
    2. **Navigate** through image groups using the controls
    3. **Classify** each group with error categories
    4. **Label** individual digits and words as correct/incorrect
    5. **Export** your annotations and view analytics
    
    ### 📁 Expected Folder Structure
    Your ZIP file should contain these folders:
    - `images/` - Original postal package images
    - `postcode_raw/` & `postcode_preprocessed/` - Postcode region images
    - `receiver_raw/` & `receiver_preprocessed/` - Receiver region images  
    - `digits/` - Text files with extracted digit sequences
    - `words/` - Text files with extracted word lists
    
    ### ⚡ Performance Optimized
    - **Smart caching** for faster image loading
    - **Progress indicators** for large datasets
    - **Optimized navigation** for thousands of groups
    """)
    
    # Show some example metrics/stats if available
    if "group_labels" in st.session_state:
        st.markdown("### 📈 Current Session Stats")
        total_labeled = len(st.session_state.get("group_labels", {}))
        st.metric("Groups Labeled", total_labeled)