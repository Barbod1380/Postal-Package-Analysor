import streamlit as st
from PIL import Image
from typing import Dict
from utils.file_utils import load_image, parse_digits_from_file, parse_words_from_file
import os


@st.cache_data
def get_image_info(filepath: str) -> Dict:
    """
    Get basic image information without loading the full image.
    Cached for performance.
    """
    try:
        if os.path.exists(filepath):
            # Get file size
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            # Get image dimensions without loading full image
            with Image.open(filepath) as img:
                width, height = img.size
                format_type = img.format
            
            return {
                "exists": True,
                "size_kb": file_size,
                "width": width,
                "height": height,
                "format": format_type
            }
        else:
            return {"exists": False}
    except Exception as e:
        return {"exists": False, "error": str(e)}


def display_image_group(group_key: str, group_data: Dict[str, str]):
    """
    Display a group of 5 related images with enhanced loading and performance optimization.
    """
    st.markdown(f"### 📦 Image Group: `{group_key}`")
    
    # Define the display order
    image_slots = [
        ("images", "🖼️ Original", "blue"),
        ("postcode_raw", "📮 Postcode (Raw)", "orange"), 
        ("postcode_preprocessed", "⚙️ Postcode (Processed)", "green"),
        ("receiver_raw", "📋 Receiver (Raw)", "orange"),
        ("receiver_preprocessed", "⚙️ Receiver (Processed)", "green"),
    ]

    # Create columns for images
    cols = st.columns(5)
    
    # Track loading status
    images_loaded = 0
    total_images = len([key for key, _, _ in image_slots if key in group_data])
    
    if total_images > 0:
        # Show overall loading progress for this group
        progress_container = st.container()
        
        # Display images with individual loading states
        for i, (key, label, color) in enumerate(image_slots):
            with cols[i]:
                st.markdown(f"**{label}**")
                
                if key in group_data:
                    # Get image info first (cached, fast)
                    img_info = get_image_info(group_data[key])
                    
                    if img_info["exists"]:
                        # Show image metadata
                        if img_info.get("size_kb", 0) > 500:  # Large file warning
                            st.caption(f"⚠️ Large file: {img_info['size_kb']:.1f} KB")
                        else:
                            st.caption(f"📏 {img_info.get('width', '?')}×{img_info.get('height', '?')}")
                        
                        # Create a placeholder for the image
                        image_placeholder = st.empty()
                        
                        # Load image with caching (this is the potentially slow operation)
                        try:
                            with st.spinner(f"Loading {label.lower()}..."):
                                img = load_image(group_data[key])
                                images_loaded += 1
                                
                            # Display the loaded image
                            image_placeholder.image(
                                img, 
                                caption=f"{label} ✅", 
                                use_container_width=True # type: ignore
                            )
                            
                        except Exception as e:
                            image_placeholder.error(f"❌ Failed to load image: {str(e)[:50]}...")
                    else:
                        st.error(f"❌ File not found")
                        if "error" in img_info:
                            st.caption(f"Error: {img_info['error'][:30]}...")
                else:
                    st.warning(f"⚠️ {label} missing")
        
        # Update progress
        with progress_container:
            if images_loaded == total_images:
                st.success(f"✅ All {total_images} images loaded successfully!")
            elif images_loaded > 0:
                st.info(f"🔄 Loaded {images_loaded}/{total_images} images...")

    # === TEXT DATA SECTION ===
    st.markdown("---")
    
    # Create two columns for text data
    text_col1, text_col2 = st.columns(2)
    
    with text_col1:
        # Show extracted digits with loading state
        st.markdown("#### 🔢 Extracted Digits")
        if "digits" in group_data:
            try:
                with st.spinner("Loading digits..."):
                    digits = parse_digits_from_file(group_data["digits"])
                
                if digits:
                    digits_str = " ".join(map(str, digits))
                    st.code(digits_str, language=None)
                    st.caption(f"✅ {len(digits)} digits found")
                else:
                    st.info("📭 No digits extracted")
                    
            except Exception as e:
                st.error(f"❌ Error loading digits: {str(e)[:50]}...")
        else:
            st.warning("⚠️ No digits file found")

    with text_col2:
        # Show extracted words with loading state  
        st.markdown("#### 📝 Extracted Words")
        if "words" in group_data:
            try:
                with st.spinner("Loading words..."):
                    words = parse_words_from_file(group_data["words"])
                
                if words:
                    # Display words with better formatting
                    words_display = []
                    for word in words:
                        if word.isdigit():
                            words_display.append(f"`{word}`")  # Numbers in code format
                        else:
                            words_display.append(f"**{word}**")  # Words in bold
                    
                    st.markdown(" • ".join(words_display))
                    st.caption(f"✅ {len(words)} words found")
                else:
                    st.info("📭 No words extracted")
                    
            except Exception as e:
                st.error(f"❌ Error loading words: {str(e)[:50]}...")
        else:
            st.warning("⚠️ No words file found")

    st.divider()