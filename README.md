# SmartVisitAI

An intelligent, Gen AI-powered Gemini Based web application that generates hospital visiting cards effortlessly, minimizing patient hassle by eliminating manual form filling.

## 🚀 Features

* **AI-powered Data Extraction**: Automatically extracts patient data from Aadhaar and discharge summary images using Google Cloud Vision and NLP APIs.
* **Instant Visiting Cards**: Generates clean, ready-to-print hospital visiting cards.
* **Interactive Chatbot Interface**: Simplified communication with patients to capture information smoothly.
* **Save Time**: Saves almost 30 min of effort.

## 🛠️ Technology Stack

* **Frontend**: HTML, CSS, JavaScript
* **Backend**: Python (Flask)
* **AI Services**: Google Gemini and Cloud Services & NLP 
* **Containerization**: Docker

## 📂 Project Structure

```
SMARTVISITAI
├── Dockerfile
├── app.py
├── config.py
├── few_shot_examples.py
├── requirements.txt
├── static
│   ├── index.html
│   ├── main.js
│   └── styles.css
└── utils
    ├── image_utils.py
    ├── validators.py
    └── visiting_card.py
```

## 🚧 Getting Started

### Prerequisites

* Python 3.8 or higher
* Google Cloud account and Vision & NLP APIs enabled
* Docker (optional)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/SmartVisitAI.git
cd SmartVisitAI
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the App

* Run the Flask application:

```bash
python app.py
```

* Visit `http://127.0.0.1:5000` in your browser.

### Docker

Alternatively, you can run it as a Docker container:

```bash
docker build -t smartvisitai .
docker run -p 5000:5000 smartvisitai
```

## 🤝 In partnership with

![Google Cloud](https://logos-world.net/wp-content/uploads/2021/02/Google-Cloud-Logo.png)

## 🚀 Powered by

![Hack2Skill](https://hack2skill.com/new/H2S-Gradient.png)

---
