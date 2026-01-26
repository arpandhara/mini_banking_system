# Mini Banking System - Backend

A robust and scalable RESTful API backend for a comprehensive banking system built with Flask and MongoDB. This system provides core banking functionalities including user authentication, transaction management, savings goals, and contact management.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Security](#security)
- [Contributing](#contributing)

## Overview

The Mini Banking System backend is a Flask-based REST API that enables secure financial transactions, user account management, and savings tracking. The system leverages MongoDB Atlas for data persistence and integrates with Twilio for SMS-based password recovery.

## System Architecture

### Component Architecture

![Architecture Diagram](./docs/architecture_diagram.png)

The system follows a modular blueprint-based architecture with clearly separated concerns:

- **Application Layer**: Flask application with CORS support
- **Route Modules**: Organized blueprints for authentication, transactions, savings, and people management
- **Database Layer**: MongoDB collections with optimized queries
- **External Services**: Twilio SMS integration for secure password recovery

### System Flow

![System Flow Diagram](./docs/system_flow_diagram.png)

The application handles user requests through a well-defined flow including authentication, authorization, business logic processing, and data persistence.

### Sequence Diagram

![Sequence Diagram](./docs/sequence_diagram.png)

Detailed interaction flows between client, server, and database for various operations.

## Key Features

### Authentication & Security
- Secure user registration with password hashing (Werkzeug)
- Session-based authentication
- Password recovery via SMS (Twilio integration)
- Password change functionality with validation

### Transaction Management
- **Deposits**: Add funds to user account
- **Withdrawals**: Secure fund withdrawals with balance validation
- **Bank Transfers**: Peer-to-peer transfers between users
- **Saving Deposits**: Allocate funds to savings goals
- Comprehensive transaction history tracking
- Real-time balance updates

### Savings Goals
- Create custom savings goals with target amounts
- Track progress toward savings targets
- Color-coded categorization
- Automatic refunds on deletion

### Contact Management
- Add verified bank users as contacts
- Edit contact information and relationships
- Delete contacts
- Validate account numbers before adding

### Dashboard Analytics
- Real-time balance overview
- Monthly income and expense tracking
- Recent transactions display
- Savings progress visualization
- Quick access to frequent contacts

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | Flask 2.x |
| **Database** | MongoDB Atlas |
| **Authentication** | Werkzeug Security, Flask Sessions |
| **SMS Service** | Twilio API |
| **CORS** | Flask-CORS |
| **Environment Management** | python-dotenv |

## Project Structure

```
backend/
├── app.py                      # Application entry point
├── database.py                 # MongoDB connection and collections
├── utils.py                    # Utility functions and helpers
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Authentication endpoints
│   ├── transactions.py         # Transaction processing
│   ├── savings.py              # Savings management
│   └── people.py               # Contact management
├── .env                        # Environment variables (not in VCS)
├── example.env                 # Environment template
├── requirement.txt             # Python dependencies
└── README.md                   # Documentation
```

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account
- Twilio account (optional, for SMS features)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mini-banking-system.git
   cd mini-banking-system/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   
   # Windows
   .\env\Scripts\activate
   
   # macOS/Linux
   source env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirement.txt
   ```

4. **Configure environment variables**
   ```bash
   cp example.env .env
   # Edit .env with your credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000` by default.

## Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/

# Twilio Configuration (Optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

> **Note**: The application will function without Twilio credentials, but SMS-based password recovery will be unavailable.

## API Documentation

### Authentication Endpoints

#### Sign Up
```http
POST /api/signup
Content-Type: application/json

{
  "username": "John Doe",
  "password": "securePassword",
  "age": 25,
  "gender": "male",
  "phoneNumber": "9876543210"
}
```

**Response**: `201 Created`
```json
{
  "message": "User John Doe created successfully",
  "user_id": 1000,
  "signUp": true
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "user_id": 1000,
  "username": "John Doe",
  "password": "securePassword"
}
```

**Response**: `200 OK`
```json
{
  "message": "Welcome back, John Doe!",
  "loggedIn": true
}
```

#### Forgot Password
```http
POST /api/forgotPass
Content-Type: application/json

{
  "phoneNumber": "9876543210"
}
```

**Response**: `200 OK`
```json
{
  "message": "Temporary password sent via SMS.",
  "isSMSSent": true
}
```

#### Change Password
```http
POST /api/change-password
Content-Type: application/json

{
  "oldPassword": "currentPassword",
  "newPassword": "newSecurePassword",
  "confirmNewPassword": "newSecurePassword"
}
```

#### Get Profile Data
```http
GET /api/profile-data
```

**Response**: `200 OK`
```json
{
  "user_id": 1000,
  "username": "John Doe",
  "balance": 5000.00,
  "age": 25,
  "gender": "male",
  "phoneNumber": 9876543210
}
```

### Transaction Endpoints

#### Get Dashboard Data
```http
GET /api/dashboard-data
```

**Response**: `200 OK`
```json
{
  "username": "John Doe",
  "total_balance": 5000.00,
  "monthly_income": 10000.00,
  "monthly_outcome": -5000.00,
  "all_transactions": [...],
  "last_4_savings": [...],
  "last_4_people": [...],
  "userAccountNumber": "1000"
}
```

#### Process Payment
```http
POST /api/process-payment
Content-Type: application/json

{
  "password": "userPassword",
  "amount": 1000,
  "transaction_type": "deposit|withdraw|bank_transfer|saving_deposit",
  "note": "Optional description",
  "recipient_account": 1001,  // for bank_transfer
  "saving_id": "sid_123456"   // for saving_deposit
}
```

**Response**: `200 OK`
```json
{
  "message": "Transaction successful!",
  "new_balance": 6000.00
}
```

#### Get Transactions
```http
GET /api/transactions-data
```

### Savings Endpoints

#### Get All Savings
```http
GET /api/savings
```

**Response**: `200 OK`
```json
[
  {
    "user_id": 1000,
    "saving_id": "sid_1234567890",
    "name": "Vacation Fund",
    "target_amount": 50000,
    "saved_amount": 15000,
    "color_code": "#FF5733",
    "description": "Summer vacation savings",
    "created_at": "2026-01-15"
  }
]
```

#### Create Savings Goal
```http
POST /api/savings
Content-Type: application/json

{
  "itemName": "New Laptop",
  "targetAmount": 80000,
  "colorCode": "#3498db",
  "description": "Saving for MacBook Pro"
}
```

#### Delete Savings Goal
```http
POST /api/savingsDelete
Content-Type: application/json

{
  "savingsId": "1234567890"
}
```

**Response**: `200 OK`
```json
{
  "message": "Deleted. Refunded: 15000.00"
}
```

### People (Contacts) Endpoints

#### Get All Contacts
```http
GET /api/people
```

**Response**: `200 OK`
```json
[
  {
    "user_id": 1000,
    "people_id": "pid_1234567890",
    "name": "Jane Smith",
    "phone": "9876543211",
    "account_id": 1001,
    "relation": "Friend",
    "full_account_number": "3594 1899 3455 1001"
  }
]
```

#### Add Contact
```http
POST /api/people
Content-Type: application/json

{
  "contactName": "Jane Smith",
  "contactAccount": 1001,
  "contactRelation": "Friend"
}
```

#### Update Contact
```http
PUT /api/people/{people_id}
Content-Type: application/json

{
  "contactName": "Jane Doe",
  "contactRelation": "Sister"
}
```

#### Delete Contact
```http
DELETE /api/people/{people_id}
```

## Database Schema

### Collections

#### users
```javascript
{
  user_id: Number,          // Auto-incrementing, starts at 1000
  username: String,
  password_hash: String,    // Hashed with Werkzeug
  balance: Number,
  age: Number,
  gender: String,
  phoneNumber: Number
}
```

#### transactions
```javascript
{
  user_id: Number,
  transaction_id: String,   // Format: "tid_[timestamp]"
  name: String,
  type: String,             // Deposit, Withdrawal, Bank Transfer, etc.
  amount: Number,           // Positive for credit, negative for debit
  date: String,             // Format: YYYY-MM-DD
  description: String,
  status: String
}
```

#### savings
```javascript
{
  user_id: Number,
  saving_id: String,        // Format: "sid_[timestamp]"
  name: String,
  target_amount: Number,
  saved_amount: Number,
  color_code: String,       // Hex color code
  description: String,
  created_at: String        // Format: YYYY-MM-DD
}
```

#### people
```javascript
{
  user_id: Number,
  people_id: String,        // Format: "pid_[timestamp]"
  name: String,
  phone: String,
  account_id: Number,       // References users.user_id
  relation: String
}
```

## Security

### Implemented Security Measures

- **Password Security**: All passwords are hashed using Werkzeug's `generate_password_hash` with default parameters (PBKDF2 with SHA-256)
- **Session Management**: Flask sessions with secure secret key for user authentication
- **Input Validation**: Server-side validation for all user inputs
- **Age Verification**: Users must be 18+ to create accounts
- **Balance Checks**: Prevents overdrafts and invalid transactions
- **Self-Transfer Prevention**: Users cannot transfer funds to themselves
- **Duplicate Prevention**: Checks for existing phone numbers and contacts

### Recommendations for Production

- [ ] Use environment-based secret key (not hardcoded)
- [ ] Implement rate limiting for API endpoints
- [ ] Add JWT-based authentication for stateless operations
- [ ] Enable HTTPS/TLS encryption
- [ ] Implement request logging and monitoring
- [ ] Add input sanitization for XSS prevention
- [ ] Set up MongoDB user roles and permissions
- [ ] Implement API versioning
- [ ] Add comprehensive error logging

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Add docstrings to all functions and classes
- Write unit tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

---

**Version**: 1.0.0  
**License**: MIT  
**Author**: Your Name  
**Last Updated**: January 2026

For questions or support, please open an issue on GitHub.
