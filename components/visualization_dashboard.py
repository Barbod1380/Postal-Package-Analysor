import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.export_utils import generate_annotation_csv
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os


def find_persian_font():
    """
    Try to find a Persian-compatible font on the system.
    """
    # Common Persian fonts across different systems
    persian_fonts = [
        # Windows
        'B Nazanin', 'Tahoma', 'Arial Unicode MS', 'Times New Roman',
        # macOS  
        'Damascus', 'Geeza Pro', 'Arial Unicode MS',
        # Linux
        'DejaVu Sans', 'Liberation Sans', 'Noto Sans Arabic', 'Vazir',
        # Universal fallbacks
        'Arial', 'Helvetica'
    ]
    
    try:
        # Get system fonts
        system_fonts = {f.name for f in fm.fontManager.ttflist}
        
        # Find first available Persian font
        for font in persian_fonts:
            if font in system_fonts:
                return font
                
        # If no specific Persian font found, try to find any font with Arabic support
        for font_obj in fm.fontManager.ttflist:
            if any(keyword in font_obj.name.lower() for keyword in ['arab', 'farsi', 'persian', 'noto']):
                return font_obj.fname
                
    except Exception as e:
        print(f"Font detection error: {e}")
    
    # Fallback to None (system default)
    return None


def extract_confusion_matrix_data():
    """
    Extract predicted vs actual digit pairs for confusion matrix.
    """
    digit_labels = dict(st.session_state.get("digit_labels", {}))
    predicted_actual_pairs = []
    
    for group_key, positions in digit_labels.items():
        for pos, data in positions.items():
            if isinstance(data, dict) and data.get("label") == "False":
                predicted = data.get("predicted")
                actual = data.get("correct_value")
                if predicted is not None and actual is not None:
                    predicted_actual_pairs.append((predicted, actual))
    
    return predicted_actual_pairs


def create_confusion_matrix():
    """
    Create a confusion matrix for digit predictions.
    """
    pairs = extract_confusion_matrix_data()
    
    if not pairs:
        return None
    
    # Create 10x10 matrix (digits 0-9)
    confusion_matrix = np.zeros((10, 10), dtype=int)
    
    for predicted, actual in pairs:
        confusion_matrix[actual][predicted] += 1
    
    return confusion_matrix


def show_visualization_dashboard():
    st.header("📊 Visualization Dashboard")

    df = generate_annotation_csv()
    if df.empty:
        st.warning("No annotations found. Please label some groups first.")
        return

    # Pie Chart: Group Label Distribution
    with st.expander("📌 Error Category Distribution (Group Labels)", expanded=True):
        # Handle multiple labels per group (semicolon-separated)
        all_labels = []
        for group_label in df["group_label"]:
            if group_label and group_label.strip():
                # Split by semicolon for multiple labels
                labels = [label.strip() for label in group_label.split(";") if label.strip()]
                all_labels.extend(labels)
        
        if all_labels:
            label_counts = pd.Series(all_labels).value_counts().reset_index()
            label_counts.columns = ["group_label", "count"]
            
            fig = px.pie(label_counts, names="group_label", values="count",
                        title="Distribution of Error Categories (Multiple labels allowed)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show summary statistics
            total_groups = len(df)
            labeled_groups = len(df[df["group_label"].str.len() > 0])
            total_labels = len(all_labels)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Groups", total_groups)
            with col2:
                st.metric("Labeled Groups", labeled_groups)
            with col3:
                st.metric("Total Labels Applied", total_labels)
                
        else:
            st.info("No group labels found. Please label some groups first.")

    # Digit Analysis Section - Two Columns
    with st.expander("🔢 Digit Analysis", expanded=True):
        digit_col1, digit_col2 = st.columns(2)
        
        with digit_col1:
            st.markdown("#### Digit Label Accuracy")
            digit_cols = [col for col in df.columns if col.startswith("digit_") and not col.endswith(("_predicted", "_correct"))]
            digit_labels = df[digit_cols].values.flatten()
            counts = Counter([str(v) for v in digit_labels if v in ["True", "False", "Unknown"]])
            
            if counts:
                pie_df = pd.DataFrame({"label": list(counts.keys()), "count": list(counts.values())})
                fig = px.pie(pie_df, names="label", values="count", title="Digit Prediction Accuracy")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No digit labels found.")
        
        with digit_col2:
            st.markdown("#### Confusion Matrix (Predicted vs Actual)")
            confusion_matrix = create_confusion_matrix()
            
            if confusion_matrix is not None and np.sum(confusion_matrix) > 0:
                # Create heatmap using plotly
                fig = go.Figure(data=go.Heatmap(
                    z=confusion_matrix,
                    x=[f"Predicted {i}" for i in range(10)],
                    y=[f"Actual {i}" for i in range(10)],
                    colorscale='Blues',
                    text=confusion_matrix,
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hoverongaps=False
                ))
                
                fig.update_layout(
                    title="Confusion Matrix: Predicted vs Actual Digits",
                    xaxis_title="Predicted Digit",
                    yaxis_title="Actual Digit",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show some statistics
                total_errors = np.sum(confusion_matrix)
                if total_errors > 0:
                    st.metric("Total Incorrect Digits Analyzed", total_errors)
            else:
                st.info("No incorrect digits with corrections found yet. Mark some digits as incorrect and provide correct values to see the confusion matrix.")

    # Bar Chart: Word Label Accuracy
    with st.expander("📝 Word Prediction Accuracy", expanded=True):
        word_cols = [col for col in df.columns if col.startswith("word_")]
        if word_cols:
            word_data = df[word_cols].melt(var_name="word", value_name="label")
            word_data["word"] = word_data["word"].str.replace("word_", "", regex=False)
            word_summary = word_data.groupby(["word", "label"]).size().reset_index(name="count")

            fig = px.bar(word_summary, x="word", y="count", color="label",
                         title="Word Label Breakdown",
                         barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No word labels found.")

    # Histogram: Missed Word Count per Group
    with st.expander("❌ Missed Word Count per Group", expanded=False):
        df["missed_word_count"] = df["missed_words"].fillna("").apply(lambda x: len(x.split(",")) if x else 0)
        fig = px.histogram(df, x="missed_word_count",
                           nbins=10,
                           title="Distribution of Missed Words per Group")
        st.plotly_chart(fig, use_container_width=True)

    # Persian-Compatible Word Cloud
    with st.expander("🌥️ Missed Word Cloud (Persian Compatible)", expanded=False):
        try:
            # Get all missed words and filter out empty ones
            missed_words_series = df["missed_words"].dropna()
            missed_words_list = []
            
            for words_str in missed_words_series:
                if words_str and words_str.strip():
                    words = [w.strip() for w in words_str.split(",") if w.strip()]
                    missed_words_list.extend(words)
            
            if missed_words_list:
                missed_text = " ".join(missed_words_list)
                
                # Try different approaches for Persian text
                try:
                    # Method 1: Find and use a Persian-compatible font
                    persian_font = find_persian_font()
                    wc = WordCloud(
                        width=800, 
                        height=400, 
                        background_color='white',
                        font_path=persian_font,  # Use found Persian font
                        prefer_horizontal=0.7,
                        max_words=100,
                        colormap='viridis'
                    ).generate(missed_text)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc.to_array(), interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    plt.close()
                    
                except Exception as font_error:
                    # Method 2: Fallback - show as text frequency instead
                    st.warning("Word cloud display issue detected. Showing text frequency instead:")
                    word_freq = Counter(missed_words_list)
                    freq_df = pd.DataFrame(word_freq.items(), columns=['Word', 'Frequency'])
                    freq_df = freq_df.sort_values('Frequency', ascending=False)
                    st.dataframe(freq_df, use_container_width=True)
                    
            else:
                st.info("No missed words found to display in word cloud.")
                
        except ImportError:
            st.error("Install `wordcloud` and `matplotlib` to view this chart: `pip install wordcloud matplotlib`")
        except Exception as e:
            st.error(f"Error generating word cloud: {str(e)}")
            
            # Alternative display: Show missed words as a simple list
            st.info("Showing missed words as frequency table instead:")
            try:
                missed_words_series = df["missed_words"].dropna()
                all_words = []
                for words_str in missed_words_series:
                    if words_str and words_str.strip():
                        words = [w.strip() for w in words_str.split(",") if w.strip()]
                        all_words.extend(words)
                
                if all_words:
                    word_freq = Counter(all_words)
                    freq_df = pd.DataFrame(word_freq.items(), columns=['کلمه (Word)', 'تعداد (Count)'])
                    freq_df = freq_df.sort_values('تعداد (Count)', ascending=False)
                    st.dataframe(freq_df, use_container_width=True)
                    
            except Exception:
                st.error("Unable to display word data.")