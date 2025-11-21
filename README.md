# 🏦 Mini Banking System

A robust backend for a banking application built with **Python (Flask)** and **MongoDB**. This system handles user authentication, secure transaction processing, savings goals management, and contact management.

## 🛠️ Tech Stack & Modules

### Core Framework
* **Flask**: The main web framework used to build the REST API.
* **Flask-CORS**: Handles Cross-Origin Resource Sharing (CORS) to allow your frontend to communicate with this backend securely.

### Database
* **MongoDB Atlas**: Cloud-based NoSQL database storage.
* **PyMongo**: The official Python driver for working with MongoDB.

### Security & Utilities
* **Werkzeug Security**: Used for hashing passwords (`generate_password_hash`) and verifying them (`check_password_hash`).
* **Python-Dotenv**: Loads environment variables (like database credentials) from a `.env` file.
* **Twilio**: Integrated for sending SMS notifications (e.g., for password resets).

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### 1. Clone the Repository
Open your terminal and run the following command:

```bash
git clone [https://github.com/arpandhara/mini_banking_system.git](https://github.com/arpandhara/mini_banking_system.git)
cd mini_banking_system/backend
