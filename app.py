import os
import re
from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+\s*', ' ', text)  # remove URLs
    text = re.sub(r'[^\w\s]', ' ', text)     # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip() # remove extra whitespace
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files or 'jd' not in request.form:
        return jsonify({"error": "Missing data"}), 400
    
    file = request.files['resume']
    jd_text = request.form['jd']
    
    # 1. Extract and Clean Text
    reader = PdfReader(file)
    resume_text = clean_text(" ".join([page.extract_text() for page in reader.pages]))
    clean_jd = clean_text(jd_text)

    # 2. Calculate Match Score (TF-IDF + Cosine Similarity)
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([clean_jd, resume_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    score = round(similarity * 100, 1)

    # 3. Identify "What to Fix" (Keyword Gap Analysis)
    # Get top 15 keywords from JD that aren't in Resume
    jd_keywords = set(re.findall(r'\b\w{3,}\b', clean_jd))
    resume_keywords = set(re.findall(r'\b\w{3,}\b', resume_text))
    
    missing = list(jd_keywords - resume_keywords)
    # Filter for common impact words/skills (Top 6)
    fixes = [word.capitalize() for word in missing if len(word) > 3][:6]

    # 4. Logical Suggestions
    suggestion = "Add more industry-specific keywords."
    if score < 40: suggestion = "Heavy tailoring required. Focus on matching technical skills."
    elif score < 70: suggestion = "Good match! Add the missing keywords below to hit 85%+"

    return jsonify({
        "score": score,
        "fixes": fixes,
        "suggestion": suggestion
    })

if __name__ == '__main__':
    app.run(debug=True)