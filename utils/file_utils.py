import os
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List
from PIL import Image
import re
import streamlit as st


@st.cache_data
def extract_zip_to_tempdir(zip_file) -> str:
    """
    Extracts a zip file uploaded in Streamlit to a temporary directory.
    Shows progress during extraction.
    """
    temp_dir = tempfile.mkdtemp()
    
    with zipfile.ZipFile(zip_file, 'r') as zf:
        file_list = zf.namelist()
        total_files = len(file_list)
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(file_list):
            # Update progress
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"Extracting: {file} ({i+1}/{total_files})")
            
            # Extract file
            zf.extract(file, temp_dir)
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text(f"✅ Extraction complete! {total_files} files extracted.")
        
        # Clear progress indicators after a short delay
        import time
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
    
    return temp_dir


def normalize_key_from_filename(path: str) -> str:
    """
    Normalizes the filename to use as a matching key:
    Removes _receiver, _postcode, _words_extracted, _digits_extracted
    """
    name = Path(path).stem
    for suffix in ['_receiver', '_postcode', '_words_extracted', '_digits_extracted']:
        if name.endswith(suffix):
            name = name.replace(suffix, '')
    return name


def get_all_files_by_type(base_dir: str) -> Dict[str, List[str]]:
    """
    Walks the base_dir and returns a dict grouping files by their folder category.
    Shows progress during file scanning.
    """
    file_groups = {
        "images": [],
        "postcode_raw": [],
        "postcode_preprocessed": [],
        "receiver_raw": [],
        "receiver_preprocessed": [],
        "digits": [],
        "words": []
    }
    
    # Count total files first for progress tracking
    total_files = sum([len(files) for _, _, files in os.walk(base_dir)])
    
    if total_files > 100:  # Only show progress for larger datasets
        progress_bar = st.progress(0)
        status_text = st.empty()
        processed_files = 0
    else:
        progress_bar = None
        status_text = None
        processed_files = 0

    for root, _, files in os.walk(base_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            
            # Update progress for large datasets
            if progress_bar:
                processed_files += 1
                progress = processed_files / total_files
                progress_bar.progress(progress)
                status_text.text(f"Scanning files: {processed_files}/{total_files}")

            # Categorize files
            if "digits" in root:
                file_groups["digits"].append(fpath)
            elif "words" in root:
                file_groups["words"].append(fpath)
            elif "postcode_raw" in root:
                file_groups["postcode_raw"].append(fpath)
            elif "postcode_preprocessed" in root:
                file_groups["postcode_preprocessed"].append(fpath)
            elif "receiver_raw" in root:
                file_groups["receiver_raw"].append(fpath)
            elif "receiver_preprocessed" in root:
                file_groups["receiver_preprocessed"].append(fpath)
            elif "images" in root:
                file_groups["images"].append(fpath)

    # Clean up progress indicators
    if progress_bar:
        progress_bar.progress(1.0)
        status_text.text("✅ File scanning complete!")
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

    return file_groups


def build_image_groups(file_dict: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
    """
    Matches files based on their normalized key.
    Shows progress during group building.
    """
    group_dict = {}
    
    # Calculate total operations for progress
    total_files = sum(len(paths) for paths in file_dict.values())
    
    if total_files > 200:  # Show progress for larger datasets
        progress_bar = st.progress(0)
        status_text = st.empty()
        processed = 0
    else:
        progress_bar = None
        status_text = None
        processed = 0

    for group_key, paths in file_dict.items():
        for path in paths:
            if progress_bar:
                processed += 1
                progress = processed / total_files
                progress_bar.progress(progress)
                status_text.text(f"Building groups: {processed}/{total_files}")
            
            base = normalize_key_from_filename(path)
            if base not in group_dict:
                group_dict[base] = {}
            group_dict[base][group_key] = path

    # Clean up progress indicators
    if progress_bar:
        progress_bar.progress(1.0)
        status_text.text(f"✅ Built {len(group_dict)} image groups!")
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

    return group_dict


@st.cache_data
def load_image(filepath: str) -> Image.Image:
    """
    Loads an image using PIL with caching for better performance.
    Automatically resizes large images for display efficiency.
    """
    try:
        img = Image.open(filepath)
        
        # Resize large images for display efficiency
        # Keep aspect ratio but limit max dimension to 800px
        max_size = 800
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        return img
    except Exception as e:
        st.error(f"Error loading image {filepath}: {e}")
        # Return a placeholder image or re-raise
        raise


@st.cache_data
def parse_digits_from_file(filepath: str) -> List[int]:
    """
    Extracts digits from a digits_extracted.txt file.
    Cached for better performance.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            match = re.search(r"Extracted Digits:\s*\[([^\]]+)\]", text)
            if match:
                digits_str = match.group(1)
                return [int(d.strip()) for d in digits_str.split(',') if d.strip().isdigit()]
    except Exception as e:
        st.error(f"Error reading digits file: {filepath} -> {e}")
    return []


@st.cache_data
def parse_words_from_file(filepath: str) -> List[str]:
    """
    Extracts non-zero words from a words_extracted.txt file.
    Cached for better performance.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            match = re.search(r"Individual Words:\s*(.+)", text)
            if match:
                words_line = match.group(1)
                # Clean and split by commas
                words = [w.strip() for w in words_line.split(',')]
                return [w for w in words if w != '0']
    except Exception as e:
        st.error(f"Error reading words file: {filepath} -> {e}")
    return []