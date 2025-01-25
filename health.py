#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import re
import time

GEMINI_API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

class HealthcareAgent:
    def __init__(self):
        self.medical_terms = {
            'vitals': ['temperature', 'blood pressure', 'heart rate', 'respiratory rate'],
            'blood_tests': ['hemoglobin', 'wbc', 'rbc', 'platelets', 'glucose'],
            'imaging': ['x-ray', 'mri', 'ct scan', 'ultrasound']
        }
        
    def analyze_with_gemini(self, text, prompt, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt + text)
                return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"API Error: {str(e)}"
        return "API Error: Maximum retries exceeded"

    def extract_medical_data(self, uploaded_file):
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = '\n'.join([page.extract_text() for page in reader.pages])
            return self._process_medical_report(text)
        else:
            raise ValueError("Only PDF medical reports are supported")

    def _process_medical_report(self, text):
        findings = {}
        for category, terms in self.medical_terms.items():
            pattern = r'(?i)({}):?\s*([\d\.]+)'.format('|'.join(terms))
            matches = re.findall(pattern, text)
            if matches:
                findings[category] = {match[0].lower(): match[1] for match in matches}
        return findings

    def symptom_checker(self, symptoms):
        prompt = f"""Analyze these symptoms: {symptoms}
        Provide:
        1. Possible conditions (list top 3)
        2. Recommended next steps
        3. Emergency warning signs
        Format as JSON:"""
        return self.analyze_with_gemini(symptoms, prompt)

    def medication_analyzer(self, medications):
        prompt = f"""Analyze these medications: {medications}
        Provide:
        1. Potential interactions
        2. Common side effects
        3. Administration guidelines
        Format as JSON:"""
        return self.analyze_with_gemini(medications, prompt)

st.set_page_config(page_title="Healthcare AI Agent", layout="wide")
st.title("🏥 AI Healthcare Assistant")

tab1, tab2, tab3 = st.tabs(["Symptom Checker", "Report Analysis", "Medication Manager"])

with tab1:
    st.subheader("Symptom Analysis")
    symptoms = st.text_area("Describe your symptoms (e.g., fever, headache):")
    if st.button("Analyze Symptoms"):
        agent = HealthcareAgent()
        with st.spinner('Analyzing symptoms...'):
            result = agent.symptom_checker(symptoms)
            st.subheader("Analysis Results")
            st.json(result)

with tab2:
    st.subheader("Medical Report Analysis")
    uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=['pdf'])
    if uploaded_file:
        agent = HealthcareAgent()
        with st.spinner('Processing report...'):
            try:
                report_data = agent.extract_medical_data(uploaded_file)
                analysis = agent.analyze_with_gemini(str(report_data), 
                    "Analyze this medical report and highlight key findings:")
                
                st.subheader("Report Summary")
                st.write(analysis)
                
                st.subheader("Key Metrics")
                for category, values in report_data.items():
                    with st.expander(category.replace('_', ' ').title()):
                        st.json(values)
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab3:
    st.subheader("Medication Analysis")
    meds = st.text_input("Enter medications (comma-separated):")
    if st.button("Analyze Medications"):
        agent = HealthcareAgent()
        with st.spinner('Checking interactions...'):
            result = agent.medication_analyzer(meds)
            st.subheader("Medication Safety Report")
            st.json(result)

st.divider()
st.caption("Note: This AI agent provides informational support only and does not replace professional medical advice.")

