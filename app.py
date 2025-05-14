import streamlit as st
import google.generativeai as genai
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
from PyPDF2 import PdfReader
import os
import tempfile
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Headers */
    h1 {
        color: #00FF9F !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 700 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        text-shadow: 0 0 10px rgba(0,255,159,0.5) !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #2D2D2D !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        border: 1px solid #00FF9F !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #00FF9F !important;
        color: #1E1E1E !important;
        font-weight: bold !important;
        border-radius: 25px !important;
        padding: 10px 25px !important;
        border: none !important;
        box-shadow: 0 0 15px rgba(0,255,159,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px rgba(0,255,159,0.5) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #2D2D2D !important;
        border-radius: 10px !important;
        padding: 20px !important;
        border: 2px dashed #00FF9F !important;
    }
    
    /* Select box */
    .stSelectbox {
        background-color: #2D2D2D !important;
        border-radius: 10px !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #2D2D2D !important;
        color: #00FF9F !important;
        border: 1px solid #00FF9F !important;
    }
</style>
""", unsafe_allow_html=True)

# Configure Gemini API
genai.configure(api_key="AIzaSyDAQPG-t6jhNTLKUtNzVLhmaz3rSq8LBDs")
model = genai.GenerativeModel("models/gemini-1.5-flash-8b")

# Initialize Whisper model
whisper_model = whisper.load_model("base")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'domain' not in st.session_state:
    st.session_state.domain = ""
if 'interview_ended' not in st.session_state:
    st.session_state.interview_ended = False
if 'performance_analysis' not in st.session_state:
    st.session_state.performance_analysis = None

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def record_audio(duration=10):
    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    with st.status("🎙️ Recording in progress...", expanded=True) as status:
        st.write(f"Recording for {duration} seconds...")
        progress_bar = st.progress(0)
        for i in range(duration * 10):
            time.sleep(0.1)
            progress_bar.progress((i + 1) / (duration * 10))
        sd.wait()
        status.update(label="✅ Recording complete!", state="complete")
    return recording, fs

def get_ai_response(prompt, resume_text, domain):
    context = f"""You are an expert interviewer conducting a technical interview. 
    Resume: {resume_text}
    Domain: {domain}
    Based on this information, respond to: {prompt}
    Keep your responses focused and professional."""
    
    response = model.generate_content(context)
    return response.text

def analyze_interview_performance(messages, domain):
    # Prepare the conversation history for analysis
    conversation = "\n".join([f"{'AI' if msg['role'] == 'assistant' else 'Candidate'}: {msg['content']}" 
                            for msg in messages if msg['role'] != 'system'])
    
    analysis_prompt = f"""As an expert technical interviewer, analyze the following interview conversation for a {domain} position.
    Provide a detailed evaluation including:
    1. Overall Performance (Score out of 100)
    2. Key Strengths
    3. Areas for Improvement
    4. Communication Skills
    5. Technical Proficiency
    6. Specific Recommendations for Growth

    Then, based on the candidate's responses and demonstrated skills, analyze their potential fit for other technical domains.
    Consider their:
    - Technical knowledge breadth
    - Problem-solving approach
    - Learning ability
    - Communication style
    - Transferable skills

    For each potential alternative domain, provide:
    - Domain name
    - Fit percentage
    - Key reasons for the fit
    - Required upskilling areas

    Interview Conversation:
    {conversation}

    Format the response in a clear, structured manner with emoji indicators for each section.
    Use the following format for domain suggestions:
    
    🔄 Domain Suitability Analysis:
    [Domain 1]
    - Fit: XX%
    - Strengths: [list]
    - Areas to Develop: [list]
    
    [Domain 2]
    - Fit: XX%
    - Strengths: [list]
    - Areas to Develop: [list]
    """
    
    response = model.generate_content(analysis_prompt)
    return response.text

def generate_pdf_report(analysis, domain, resume_text):
    # Create a buffer to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    elements.append(Paragraph("Interview Performance Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Add date and domain
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=1
    )
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", date_style))
    elements.append(Paragraph(f"Domain: {domain}", date_style))
    elements.append(Spacer(1, 20))
    
    # Add analysis content
    content_style = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceAfter=16
    )
    
    # Split analysis into sections and format them
    sections = analysis.split('\n\n')
    for section in sections:
        elements.append(Paragraph(section, content_style))
        elements.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    # Create two columns for layout
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        st.markdown("<h1>🤖 AI Interview Assistant</h1>", unsafe_allow_html=True)
        
        # Domain selection with custom styling
        st.markdown("### 🎯 Select Your Domain")
        domains = ["Software Development", "Data Science", "DevOps", "Machine Learning", 
                  "Web Development", "Cloud Computing", "Cybersecurity"]
        selected_domain = st.selectbox("", domains, 
                                     help="Choose your area of expertise")
        st.session_state.domain = selected_domain
        
        # Resume upload with custom styling
        st.markdown("### 📄 Upload Your Resume")
        uploaded_file = st.file_uploader("", type="pdf",
                                       help="Upload your resume in PDF format")
        
        if uploaded_file and not st.session_state.resume_text:
            with st.spinner("📝 Analyzing your resume..."):
                st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
                initial_prompt = "Based on the resume, generate an appropriate first interview question."
                first_question = get_ai_response(initial_prompt, st.session_state.resume_text, st.session_state.domain)
                st.session_state.messages.append({"role": "assistant", "content": first_question})
        
        # End Interview Button (only show if interview has started)
        if st.session_state.messages and not st.session_state.interview_ended:
            if st.button("🎯 End Interview & Get Analysis", use_container_width=True,
                        help="Click to end the interview and get detailed performance analysis"):
                with st.spinner("🔄 Analyzing interview performance..."):
                    analysis = analyze_interview_performance(
                        st.session_state.messages,
                        st.session_state.domain
                    )
                    st.session_state.performance_analysis = analysis
                    st.session_state.interview_ended = True
                    st.rerun()
    
    with right_col:
        if st.session_state.interview_ended:
            st.markdown("### 📊 Interview Analysis")
            st.markdown(st.session_state.performance_analysis)
            
            col1, col2 = st.columns(2)
            
            # Option to start new interview
            with col1:
                if st.button("📝 Start New Interview", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.interview_ended = False
                    st.session_state.performance_analysis = None
                    st.rerun()
            
            # Download PDF Report
            with col2:
                if st.button("📥 Download Report", use_container_width=True):
                    pdf_buffer = generate_pdf_report(
                        st.session_state.performance_analysis,
                        st.session_state.domain,
                        st.session_state.resume_text
                    )
                    st.download_button(
                        label="📄 Save PDF Report",
                        data=pdf_buffer,
                        file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.markdown("### 💬 Interview Session")
            # Chat container with custom styling
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                        st.write(message["content"])
            
            # Audio recording interface (only show if interview hasn't ended)
            if not st.session_state.interview_ended:
                st.markdown("### 🎙️ Your Response")
                if st.button("Start Recording (10s)", use_container_width=True):
                    if st.session_state.resume_text:
                        recording, fs = record_audio()
                        
                        try:
                            with st.spinner("🔄 Processing your response..."):
                                # Create temporary file
                                temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                                temp_audio_path = temp_audio.name
                                temp_audio.close()
                                
                                # Save the recording
                                sf.write(temp_audio_path, recording, fs)
                                
                                # Transcribe audio using Whisper
                                result = whisper_model.transcribe(temp_audio_path)
                                user_response = result["text"]
                                
                                # Add user message to chat
                                st.session_state.messages.append({"role": "user", "content": user_response})
                                
                                # Generate AI response
                                ai_response = get_ai_response(user_response, st.session_state.resume_text, st.session_state.domain)
                                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                                
                        finally:
                            time.sleep(0.1)
                            try:
                                if os.path.exists(temp_audio_path):
                                    os.unlink(temp_audio_path)
                            except Exception as e:
                                st.warning(f"Note: Could not delete temporary file: {str(e)}")
                        
                        st.rerun()
                    else:
                        st.error("⚠️ Please upload your resume first!")

    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Powered by Gemini AI & Whisper | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 