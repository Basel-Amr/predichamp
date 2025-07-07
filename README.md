# ⚽ Match Predictor - Premier League Edition

[![Streamlit App](https://img.shields.io/badge/Launch%20App-Streamlit-ff4b4b?logo=streamlit&logoColor=white)](https://matchpredictor.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Welcome to **Match Predictor**, a fun and competitive Premier League match prediction platform. Predict upcoming games, compete with friends, and climb the leaderboard as the season unfolds!

🌐 **Live App**: [matchpredictor.streamlit.app](https://matchpredictor.streamlit.app/)

---

## 🎯 Features

- 🔒 **Secure Login** – Sign in with your unique username.
- 📅 **Upcoming Matches** – View all fixtures for the next game week.
- 📊 **Make Predictions** – Submit your score predictions with a simple and intuitive interface.
- ⏰ **Automated Email Reminders** – Get notified 2 days, 1 day, and 2 hours before each deadline.
- 🏆 **Leaderboard** – Compete against friends and see who’s the best predictor!
- 🛠️ **Admin Panel** – Easily manage players, matches, and rounds (with a secret code 😉).
- ✉️ **Personalized Emails** – Friendly reminders sent with your username.
- 🚀 **Deployed on Streamlit Community Cloud** – Fast, free, and easy to use!

---

## 📸 Screenshots

| Home Page | Prediction Form | Leaderboard |
|-----------|------------------|--------------|
| ![home](assets/home.png) | ![predict](assets/predict.png) | ![leaderboard](assets/leaderboard.png) |

---

## 🧠 How It Works

1. **Users** log in with their unique username.
2. Each **round** has a set of matches and a deadline (2 hours before the first match).
3. Users can **submit or update** predictions before the deadline.
4. Friendly **email reminders** are sent automatically before every round:
   - 2 days before
   - 1 day before
   - 2 hours before (final call!)
5. Scores are calculated and **rankings updated** after matches are played.

---

## 📦 Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/)
- **Backend**: Python (controllers & business logic)
- **Database**: SQLite
- **Email Service**: SMTP via Gmail
- **Deployment**: Streamlit Community Cloud

---

## 🧪 Local Development

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/match-predictor.git
   cd match-predictor
