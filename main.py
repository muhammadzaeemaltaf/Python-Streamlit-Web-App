import streamlit as st
import pandas as pd
import os
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai
from key import GEMINI_API_KEY

# Set up Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Streamlit App Setup
st.set_page_config(page_title="Data Sweeper", layout="wide")
st.title("Data Sweeper")
st.write(
    "Transform your file between multiple formats with built-in data cleaning, visualization, and AI-powered Q&A!"
)

uploaded_file = st.file_uploader(
    "Upload your files (CSV, Excel, JSON):",
    type=["csv", "xlsx", "json"],
    accept_multiple_files=True,
)

if uploaded_file:
    for file in uploaded_file:
        file_ext = os.path.splitext(file.name)[-1].lower()

        if file_ext == ".csv":
            df = pd.read_csv(file)
        elif file_ext == ".xlsx":
            try:
                df = pd.read_excel(file)
            except ImportError:
                st.error("Missing 'openpyxl' library. Please install it using pip.")
                continue
        elif file_ext == ".json":
            df = pd.read_json(file)
        else:
            st.error(f"Unsupported file format: {file_ext}")
            continue

        # Display file details
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")
        st.write("Preview of Dataframe")
        st.dataframe(df.head())

        # Data Cleaning
        st.subheader("Data Cleaning")
        if st.checkbox(f"Clean Data for {file.name}"):
            if st.button(f"Remove Duplicates from {file.name}"):
                df.drop_duplicates(inplace=True)
                st.write("Duplicates removed successfully!")
            if st.button(f"Fill Missing Values in {file.name}"):
                numeric_cols = df.select_dtypes(include=["number"]).columns
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                st.write("Missing values filled successfully!")

        # Column Selection
        st.subheader("Select Columns")
        columns = st.multiselect(
            f"Choose Columns for {file.name}", df.columns, default=df.columns
        )
        df = df[columns]

        # Data Visualization
        st.subheader("Data Visualization")
        if st.checkbox(f"Show Visualizations for {file.name}"):
            chart_type = st.selectbox(
                f"Select Chart Type for {file.name}",
                ["Area Chart", "Bar Chart", "Line Chart"],
            )
            numerical_columns = df.select_dtypes(include=["number"]).columns

            if len(numerical_columns) < 1:
                st.warning("No numerical columns available for visualization.")
            else:
                if chart_type == "Area Chart":
                    st.area_chart(df[numerical_columns])
                elif chart_type == "Bar Chart":
                    st.bar_chart(df[numerical_columns])
                elif chart_type == "Line Chart":
                    st.line_chart(df[numerical_columns])

        # AI Q&A Feature Fix
        st.subheader("AI-Powered Data Q&A")
        user_question = st.text_input(
            f"Ask about {file.name} (e.g., 'What is the average of column X?'):"
        )
        if st.button("Get AI Answer"):
            response = model.generate_content(
                user_question + "\n" + df.describe().to_string()
            )
            st.write(response.text)

        # File Conversion & Download Fix
        st.subheader("Conversion Options")
        conversion_type = st.radio(
            f"Convert {file.name} to:", ["CSV", "Excel", "JSON", "PDF"], key=file.name
        )

        # Define extension mapping for correct file naming
        extension_map = {
            "CSV": ".csv",
            "Excel": ".xlsx",
            "JSON": ".json",
            "PDF": ".pdf",
        }

        if st.button(f"Convert {file.name}"):
            buffer = BytesIO()
            # Use the extension map to ensure correct file extension
            file_name = file.name.replace(file_ext, extension_map[conversion_type])

            if conversion_type == "CSV":
                df.to_csv(buffer, index=False)
                mime_type = "text/csv"
            elif conversion_type == "Excel":
                # Use 'openpyxl' engine (consistent with reading check)
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                mime_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif conversion_type == "JSON":
                buffer.write(df.to_json(orient="records").encode())
                mime_type = "application/json"
            elif conversion_type == "PDF":
              num_rows, num_cols = df.shape
              fig_height = max(3, min(11, num_rows * 0.2))
              fig_width = max(5, min(8.5, num_cols * 0.5))
              fig, ax = plt.subplots(figsize=(fig_width, fig_height))
              ax.axis("off")
              ax.text(0.01, 0.99, df.to_string(), fontsize=6, verticalalignment="top", horizontalalignment="left")
              fig.tight_layout()
              fig.savefig(buffer, format="pdf")
              mime_type = "application/pdf"

            buffer.seek(0)
            st.download_button(
                label=f"Download {file.name} as {conversion_type}",
                data=buffer,
                file_name=file_name,
                mime=mime_type,
            )
            st.success("File conversion completed! 🎉")
