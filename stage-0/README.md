# Backend Stage 0 – Express API

A simple Node.js/Express server that fetches data from an external API and returns user-specific information, built for the HNGx DevOps Stage 0 challenge.

---

## Features

- Environment-based configuration
- Uses Axios to fetch data from an external API
- `/me` endpoint returns user info and a random fact
- Basic error handling and timeout logic
- CORS enabled
- Rate limiting applied

---

## 📦 Dependencies

- [Express](https://expressjs.com/)
- [Axios](https://axios-http.com/)
- [Dotenv](https://www.npmjs.com/package/dotenv)
- [Cors](https://www.npmjs.com/package/cors)
- [Express-rate-limit](https://www.npmjs.com/package/express-rate-limit)

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/carvanino/hng-backend.git
cd hng-backend
```

### 2. Install Depencies
```
npm install 
```

### 3.  Create .env file
```
PORT=80
BASE_URL=https://catfact.ninja/fact
NAME=Oluwatofunmi Akinola
EMAIL=akinolatofunmi.tech@gmail.com
```

### 4. Start the server
```
npm start
```

## 📂 Available Routes
```GET /```
Returns a welcmome message

```Get /me```
Returns:
* Your name and email (from environment variables)
* Stack information
* A random fact fetched from an external API
* A UTC timestamp

```json
Example Response from /me
{
  "status": 200,
  "user": {
    "email": "your-email@example.com",
    "name": "Oluwatofunmi Akinola",
    "stack": "Node.js/Express"
  },
  "timestamp": "2025-10-20T16:41:38.418Z",
  "fact": "Cats sleep 70% of their lives."
}
```


## 📌 NOTES
* If the external API fails, proper error status codes are returned.
* Rate limiting is enabled to prevent abuse (100 requests per 15 minutes per IP).
* CORS is enabled by default for all origins.
