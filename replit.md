# Overview

This is a Flask-based web application that handles job/program applications with integrated payment processing. The system allows users to submit applications with personal information and resumes, processes payments through Razorpay, and provides an admin dashboard to view and manage submissions. The application uses a simple SQLite database for data persistence and includes file upload functionality for resume submissions.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Technology Stack**: Pure HTML/CSS with minimal JavaScript
- Server-side rendered templates using Flask's Jinja2 templating engine
- Three main views: application form (index.html), success confirmation (success.html), and admin dashboard (admin.html)
- Gradient-based modern UI design with responsive layouts
- No frontend framework dependencies - lightweight vanilla approach

**Design Pattern**: Traditional multi-page application (MPA)
- Each route renders a complete HTML page
- Form submissions use standard HTTP POST requests
- Minimal client-side interactivity, server handles most logic

## Backend Architecture

**Framework**: Flask (Python microframework)
- Lightweight and simple for small-to-medium applications
- Built-in development server and routing
- Easy integration with Python ecosystem

**Application Structure**:
- Single monolithic `app.py` file containing all routes and logic
- Simple and straightforward for this application size
- Environment-based configuration using python-dotenv

**Key Components**:
1. **Application Routes**: Handle form submission, payment processing, and admin views
2. **File Upload Handler**: Secure file upload with validation for resumes (PDF, DOC, DOCX only)
3. **Database Layer**: Direct SQLite3 operations without ORM
4. **Payment Integration**: Razorpay SDK for payment processing

## Data Storage

**Database**: SQLite3
- File-based database (applications.db)
- Suitable for small to medium traffic applications
- No separate database server required
- Schema includes applications table with fields: id, full_name, email, phone, gender, dob, bio, resume_filename, payment_id, payment_status, created_at

**File Storage**: Local filesystem
- Resume uploads stored in 'uploads' directory
- 2MB file size limit enforced
- Filename sanitization using werkzeug.utils.secure_filename

**Design Rationale**:
- SQLite chosen for simplicity and zero-configuration setup
- Suitable for read-heavy workloads with moderate write operations
- Easy backup (single file) and portability
- Trade-off: Not suitable for high-concurrency scenarios or multiple server instances

## Authentication & Authorization

**Current Implementation**: No authentication system implemented
- Admin dashboard appears to be publicly accessible (security consideration)
- No user login/session management
- Application submission is open to public

**Security Measures**:
- File upload validation (type and size restrictions)
- Secure filename handling with path traversal protection
- Resume filename validation and sanitization in payment verification
- Download endpoint protected against directory traversal attacks
- Environment variable usage for sensitive keys (Razorpay credentials)

**Recommendation**: Admin dashboard should be protected with authentication in production

## Payment Processing

**Provider**: Razorpay
- Indian payment gateway supporting multiple payment methods
- Server-side integration using razorpay-python SDK
- Credentials stored in environment variables (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)

**Payment Flow**:
1. User submits application form
2. Payment initiated through Razorpay
3. Payment ID captured and stored with application
4. Payment status tracked (pending/completed)

# External Dependencies

## Payment Gateway
- **Razorpay**: Payment processing service
  - Requires API key and secret
  - Handles payment collection for application fees
  - Returns payment_id for transaction tracking

## Python Packages
- **Flask**: Web framework
- **razorpay**: Payment gateway SDK
- **python-dotenv**: Environment variable management
- **werkzeug**: Utilities for file handling (included with Flask)

## Environment Variables Required
- `RAZORPAY_KEY_ID`: Razorpay API key
- `RAZORPAY_KEY_SECRET`: Razorpay API secret
- `SESSION_SECRET`: Flask session secret key (optional, defaults to 'dev-secret-key')

## File System Dependencies
- Local uploads directory for resume storage
- SQLite database file (applications.db)

## Browser Requirements
- Modern browser with JavaScript enabled (for Razorpay payment modal)
- CSS3 support for gradient backgrounds and modern styling