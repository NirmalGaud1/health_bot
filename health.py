#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import re
import time
import json

# Configure Gemini
GEMINI_API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"  # Replace with your key
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
        Provide response in VALID JSON format only:
        {{
            "possible_conditions": [],
            "recommended_actions": [],
            "emergency_signs": []
        }}
        Do not include any markdown formatting."""
        
        try:
            response = self.analyze_with_gemini(symptoms, prompt)
            # Clean response
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse medical analysis"}
        except Exception as e:
            return {"error": str(e)}

    def medication_analyzer(self, medications):
        prompt = f"""Analyze these medications: {medications}
        Provide response in VALID JSON format:
        {{
            "interactions": [],
            "side_effects": [],
            "guidelines": []
        }}
        No markdown, only pure JSON:"""
        
        try:
            response = self.analyze_with_gemini(medications, prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse medication analysis"}
        except Exception as e:
            return {"error": str(e)}

# Streamlit UI
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
            
            if "error" in result:
                st.error(f"Analysis failed: {result['error']}")
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("Possible Conditions")
                    for condition in result.get("possible_conditions", [])[:3]:
                        st.markdown(f"- {condition}")
                
                with col2:
                    st.subheader("Recommended Actions")
                    for action in result.get("recommended_actions", []):
                        st.markdown(f"- {action}")
                
                with col3:
                    st.subheader("Emergency Signs")
                    for sign in result.get("emergency_signs", []):
                        st.markdown(f"⚠️ {sign}")

with tab2:
    st.subheader("Medical Report Analysis")
    uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=['pdf'], key="report")
    
    if uploaded_file:
        agent = HealthcareAgent()
        with st.spinner('Processing report...'):
            try:
                report_data = agent.extract_medical_data(uploaded_file)
                analysis = agent.analyze_with_gemini(str(report_data), 
                    "Analyze this medical report and highlight key findings:")
                
                st.subheader("Report Summary")
                st.markdown(analysis)
                
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
            
            if "error" in result:
                st.error(f"Analysis failed: {result['error']}")
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("Interactions")
                    for interaction in result.get("interactions", []):
                        st.markdown(f"- {interaction}")
                
                with col2:
                    st.subheader("Side Effects")
                    for effect in result.get("side_effects", []):
                        st.markdown(f"- {effect}")
                
                with col3:
                    st.subheader("Guidelines")
                    for guideline in result.get("guidelines", []):
                        st.markdown(f"- {guideline}")

st.divider()
st.caption("Note: This AI agent provides informational support only and does not replace professional medical advice.")

