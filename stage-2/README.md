# Backend Stage 2 - Countries API

A RESTful API that fetches country data from external APIs, stores it in a MySQL database, and provides CRUD operations with caching and image generation capabilities.

## Features

- Fetch and cache country data from external APIs
- Exchange rate integration for GDP estimation
- Filter and sort countries by region, currency, and GDP
- Auto-generated summary images with top countries
- Rate limiting and error handling
- MySQL database persistence

## Tech Stack

- **Runtime:** Node.js
- **Framework:** Express.js
- **Database:** MySQL
- **Key Dependencies:**
  - `mysql2` - MySQL database driver
  - `axios` - HTTP client for external APIs
  - `canvas` - Image generation
  - `lodash` - Utility functions
  - `express-rate-limit` - API rate limiting
  - `dotenv` - Environment configuration
  - `cors` - Cross-origin resource sharing

## Prerequisites

- Node.js (v18 or higher)
- MySQL database
- SSL certificate file for database connection (if using SSL)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/carvanino/hng-backend.git
cd hng-backend/stage-2
```

2. **Install dependencies:**
```bash
npm install
```

3. **Set up environment variables:**

Create a `.env` file in the root directory with the following variables:
```env
# Server Configuration
PORT=3000

# Database Configuration
DB=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=3306
DB_SSL_CERT_PATH=./HNG-TEST-DB-ssl-public-cert.cert  # Optional: Remove if SSL not required

# External APIs
COUNTRY_BASE_URL=https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies
EXCHANGE_RATE_BASE_URL=https://open.er-api.com/v6/latest/USD

# Image Configuration
IMAGE_PATH=./cache/summary.png
```

4. **Place SSL certificate (if required):**

If your MySQL connection requires SSL, place your certificate file in the project root:
```
HNG-TEST-DB-ssl-public-cert.cert
```

## Running the Application

**Development mode:**
```bash
npm start
```

The server will start on the port specified in your `.env` file (default: 3000).

## API Endpoints

### 1. Refresh Countries Data
**POST** `/countries/refresh`

Fetches latest country data and exchange rates, then caches them in the database.

**Response:**
```json
{
  "success": true
}
```

---

### 2. Get All Countries
**GET** `/countries`

Retrieve all countries from the database with optional filtering and sorting.

**Query Parameters:**
- `region` (optional) - Filter by region (e.g., `Africa`, `Europe`)
- `currency` (optional) - Filter by currency code (e.g., `NGN`, `USD`)
- `sort` (optional) - Sort by GDP (`gdp_desc` or `gdp_asc`)

**Example:**
```bash
GET /countries?region=Africa&sort=gdp_desc
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-22T18:00:00Z"
  }
]
```

---

### 3. Get Single Country
**GET** `/countries/:name`

Retrieve a specific country by name.

**Example:**
```bash
GET /countries/Nigeria
```

**Response:**
```json
{
  "id": 1,
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 206139589,
  "currency_code": "NGN",
  "exchange_rate": 1600.23,
  "estimated_gdp": 25767448125.2,
  "flag_url": "https://flagcdn.com/ng.svg",
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

**Error Response (404):**
```json
{
  "error": "Country not found"
}
```

---

### 4. Delete Country
**DELETE** `/countries/:name`

Delete a country record from the database.

**Example:**
```bash
DELETE /countries/Nigeria
```

**Response:** `204 No Content`

**Error Response (404):**
```json
{
  "error": "Country not found"
}
```

---

### 5. Get Status
**GET** `/status`

Get total countries count and last refresh timestamp.

**Response:**
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-22T18:00:00Z"
}
```

---

### 6. Get Summary Image
**GET** `/countries/image`

Retrieve the generated summary image showing top 5 countries by GDP.

**Response:** PNG image file

**Error Response (404):**
```json
{
  "error": "Summary image not found"
}
```

## Rate Limiting

The API implements rate limiting:
- **Limit:** 100 requests per 15 minutes per IP
- **Response (429):**
```json
{
  "status": 429,
  "message": "Too many requests, please try again later."
}
```

## Error Handling

The API returns consistent error responses:

- **400 Bad Request** - Validation failed
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - External API unavailable

## Database Schema

### Countries Table
```sql
CREATE TABLE countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  capital VARCHAR(255),
  region VARCHAR(255),
  population BIGINT NOT NULL,
  currency_code VARCHAR(10),
  exchange_rate DOUBLE,
  estimated_gdp DOUBLE,
  flag_url VARCHAR(255),
  last_refreshed_at DATETIME,
  UNIQUE KEY unique_name (name)
);
```

### Refresh Status Table
```sql
CREATE TABLE refresh_status (
  id INT PRIMARY KEY,
  last_refreshed_at DATETIME
);
```

## Testing

### Manual Testing Steps

1. **Start the server**
```bash
npm start
```

2. **Test refresh endpoint**
```bash
curl -X POST http://localhost:3000/countries/refresh
```

3. **Test get all countries**
```bash
curl http://localhost:3000/countries
```

4. **Test filtering**
```bash
curl "http://localhost:3000/countries?region=Africa&sort=gdp_desc"
```

5. **Test get single country**
```bash
curl http://localhost:3000/countries/Nigeria
```

6. **Test status endpoint**
```bash
curl http://localhost:3000/status
```

7. **Test image endpoint**
```bash
curl http://localhost:3000/countries/image --output summary.png
```

8. **Test delete endpoint**
```bash
curl -X DELETE http://localhost:3000/countries/Nigeria
```

## Dependencies
```json
{
  "dependencies": {
    "express": "^4.18.0",
    "body-parser": "^1.20.0",
    "cors": "^2.8.5",
    "mysql2": "^3.0.0",
    "axios": "^1.6.0",
    "canvas": "^2.11.0",
    "lodash": "^4.17.21",
    "express-rate-limit": "^7.0.0",
    "dotenv": "^16.0.0"
  }
}
```

## Notes

- The `estimated_gdp` is calculated using: `population × random(1000-2000) ÷ exchange_rate`
- Countries without currency data are stored with `null` values for `currency_code`, `exchange_rate`, and `estimated_gdp`
- The refresh operation updates existing countries and inserts new ones
- Summary images are regenerated after each successful refresh
- SSL certificate is optional - only required if your MySQL server requires SSL connections