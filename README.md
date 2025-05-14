# AI Mock Interview Chatbot

This application is an AI-powered mock interview chatbot that conducts technical interviews based on your resume and selected domain. It uses Gemini AI for generating questions and Whisper for speech-to-text conversion.

## Features

- PDF resume upload and analysis
- Domain-specific technical interviews
- Voice-based responses using Whisper speech-to-text
- Real-time AI-generated follow-up questions
- Interactive chat interface

## Prerequisites

- Python 3.8 or higher
- FFmpeg (required for Whisper)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
2. Select your technical domain from the dropdown menu
3. Upload your resume in PDF format
4. The chatbot will start the interview with an initial question
5. Click the "Record Response" button to answer questions using your voice
6. The conversation will continue with follow-up questions based on your responses

## Note

- Make sure your microphone is properly configured
- Each voice recording session is limited to 10 seconds
- Ensure your PDF resume is properly formatted for text extraction

## Technologies Used

- Streamlit - Web interface
- Google Gemini AI - Question generation
- OpenAI Whisper - Speech-to-text conversion
- PyPDF2 - PDF processing 