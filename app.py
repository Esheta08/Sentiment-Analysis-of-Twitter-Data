from keras.models import load_model
from flask import Flask, request, render_template
import numpy as np
import pickle
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# Download stopwords only once
nltk.download('stopwords')

app = Flask(__name__)

@app.route('/')
def home():
    # Default page (no prediction yet)
    return render_template('index.html', image=False, image2=False)

@app.route('/y_predict', methods=['POST'])
def y_predict():
    # Load vectorizer
    with open('cv.pkl', 'rb') as file:
        cv = pickle.load(file)

    # Load model
    model = load_model('model.h5')

    # Get input text from user
    sentence = request.form['Sentence']

    # Transform the input using the loaded vectorizer
    input_data = cv.transform([sentence]).toarray()

    # Predict sentiment
    prediction = model.predict(input_data)
    output = prediction[0][0] if isinstance(prediction[0], (np.ndarray, list)) else prediction[0]

    # Determine sentiment and return appropriate response
    if output < 0.5:
        return render_template(
            'index.html',
            prediction_text="😞 The tweet has Negative Emotions",
            image=False,
            image2=True
        )
    else:
        return render_template(
            'index.html',
            prediction_text="😊 The tweet has Positive Emotions",
            image=True,
            image2=False
        )

if __name__ == "__main__":
    app.run(debug=True, port=8000)
