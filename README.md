# 🏦 Mini Banking System (Backend)

> **A robust, secure, and scalable backend API for personal banking operations.**

This project serves as the core infrastructure for a personal banking application. Built with **Python (Flask)** and **MongoDB**, it facilitates secure user authentication, real-time transaction processing, financial goal tracking, and contact management. It features SMS notification integration via Twilio and ensures data security through hashed credentials and environment-based configuration.

## 🌟 Key Features

*   **🔐 Secure Authentication:** User registration, login, and password management using Werkzeug security hashing.
    
*   **💸 Transaction Management:** Real-time processing of deposits, withdrawals, and transfers between accounts.
    
*   **📈 Dashboard Analytics:** Aggregated views of balances, income vs. expenses, and transaction history.
    
*   **🎯 Savings Goals:** Create, track, and liquidate custom savings goals.
    
*   **👥 Contact Management:** Manage a list of payees (contacts) for quick transfers.
    
*   **📱 SMS Notifications:** Integrated Twilio support for OTPs and temporary passwords.
    

## 🛠️ Tech Stack

| Component | Technology | Description |
| --- | --- | --- |
| Core Framework | Flask | Lightweight WSGI web application framework. |
| Middleware | Flask-CORS | Handles Cross-Origin Resource Sharing for frontend communication. |
| Database | MongoDB Atlas | Cloud-hosted NoSQL database for scalable data storage. |
| Driver | PyMongo | Official Python driver for MongoDB. |
| Security | Werkzeug | Secure password hashing (generate_password_hash, check_password_hash). |
| Utilities | Python-Dotenv | Management of sensitive environment variables. |
| Notifications | Twilio | SMS gateway integration. |

## 📂 Project Structure

    mini_banking_system/
    ├── app.py               # Application entry point & API route definitions
    ├── database.py          # Database connection logic & schema handlers
    ├── requirement.txt      # Python dependency manifest
    ├── .env                 # Environment variables (Excluded from version control)
    └── README.md            # Project documentation
    

## 🚀 Getting Started

Follow these steps to set up the development environment on your local machine.

### Prerequisites

*   **Python 3.6+** installed.
    
*   A **MongoDB Atlas** account (Free Tier M0 is sufficient).
    
*   _(Optional)_ A **Twilio** account for SMS features.
    

### 1\. Clone the Repository

    git clone [https://github.com/arpandhara/mini_banking_system.git](https://github.com/arpandhara/mini_banking_system.git)
    cd mini_banking_system
    

### 2\. Initialize Virtual Environment

Isolate your dependencies by creating a virtual environment.

**Windows:**

    python -m venv venv
    venv\Scripts\activate
    

**macOS / Linux:**

    python3 -m venv venv
    source venv/bin/activate
    

### 3\. Install Dependencies

    pip install -r requirement.txt
    

## ⚙️ Database Setup (MongoDB Atlas)

This application requires a cloud database connection. Follow these steps to configure MongoDB Atlas:

1.  **Create a Cluster:** Log in to MongoDB Atlas, create a project, and deploy a database (Select **M0 Sandbox** for free tier).
    
2.  **Create Database User:**
    
    *   Navigate to **Database Access**.
        
    *   Click **Add New Database User**.
        
    *   Set a Username (e.g., `admin`) and a **Strong Password**.
        
    *   Set Privileges to **"Read and write to any database"**.
        
3.  **Whitelist IP Address:**
    
    *   Navigate to **Network Access**.
        
    *   Click **Add IP Address** -> **Add Current IP Address**.
        
4.  **Get Connection String:**
    
    *   Go to **Database** -> **Connect** -> **Drivers**.
        
    *   Select **Python** (Version 3.6+).
        
    *   Copy the connection string provided.
        

## 🔑 Configuration

Create a `.env` file in the root directory to store sensitive credentials. You can use the template below:

    # --- MongoDB Connection ---
    # Replace <username> and <password> with your Atlas credentials.
    # NOTE: Ensure '/MiniBankingSystem' is specified before the '?' to auto-create the DB.
    MONGO_URI=mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/MiniBankingSystem?retryWrites=true&w=majority
    
    # --- Twilio Configuration (Optional) ---
    # Leave these blank if SMS functionality is not required.
    TWILIO_ACCOUNT_SID=your_twilio_sid_here
    TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
    TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
    

## 🏃‍♂️ Running the Application

Start the Flask development server:

    python app.py
    

You should see the following output confirming the server is active:

> `Running on http://127.0.0.1:5000`

## 📡 API Documentation

### 1\. Authentication

Endpoints for user identity and session management.

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | /api/signup | Register a new user account. |
| POST | /api/login | Authenticate user and initiate session. |
| POST | /api/forgotPass | Trigger temporary password via SMS (Requires Twilio). |
| POST | /api/change-password | Securely update the current user's password. |
| GET | /api/profile-data | Retrieve basic user profile information. |

### 2\. Banking Operations

Core financial transaction handling.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /api/dashboard-data | Fetch user balance, income, expenses, and recent activity. |
| GET | /api/transactions-data | Retrieve full transaction history log. |
| POST | /api/process-payment | Execute Deposits, Withdrawals, and Peer-to-Peer transfers. |

### 3\. Savings Goals

Management of separate savings buckets.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /api/savings | Retrieve all active savings goals. |
| POST | /api/savings | Initialize a new savings goal. |
| POST | /api/savingsDelete | Delete a goal and refund the balance to the main account. |

### 4\. Contacts (Payees)

Management of saved beneficiaries.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /api/people | List all saved contacts. |
| POST | /api/people | Add a new contact using their Account ID. |
| PUT | /api/people/<id> | Update details for an existing contact. |
| DELETE | /api/people/<id> | Remove a contact from the list. |
