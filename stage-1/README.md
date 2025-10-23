# Backend Stage 1 – String Analysis API

Node.js/Express RESTful API that analyzes strings, computes their properties (length, palindrome status, hash, etc.), and allows filtering through query parameters or natural language queries.
Built for the HNGx DevOps Stage 1 challenge

---

## Features

- Compute multiple string properties:
    - Length
    - Palindrome check (case-insensitive)
    - Unique characters
    - Word count
    - SHA-256 hash
    - Character frequency map
- Store analyzed strings in an in-memory database
- Retrieve specific strings or filter by query parameters
- Delete analyzed strings
- Interpret natural-language filters using NLP
- Basic input validation and error handling
- Rate limiting applied

---

## 📦 Dependencies

- [Express](https://expressjs.com/)
- [Cors](https://www.npmjs.com/package/cors)
- [Body-Parser](https://www.npmjs.com/package/body-parser)
- [Dotenv](https://www.npmjs.com/package/dotenv)
- [Cors](https://www.npmjs.com/package/cors)
- [Express-rate-limit](https://www.npmjs.com/package/express-rate-limit)
- [Compromise](https://www.npmjs.com/package/compromise)
- [Crypto]()

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/carvanino/hng-backend.git
cd hng-backend/stage-1
```

### 2. Install Depencies
```
npm install 
```

### 3.  Create .env file
```
PORT=80
```

### 4. Start the server
```
npm start
```

## 📂 Available Routes
```POST /strings```
Analyze and store a string.

**Request Body:**
```json
{
  "value": "string to analyze"
}
```
**Response (201 Created):**
```json
{
  "id": "sha256_hash_value",
  "value": "string to analyze",
  "properties": {
    "length": 16,
    "is_palindrome": false,
    "unique_characters": 12,
    "word_count": 3,
    "sha256_hash": "abc123...",
    "character_frequency_map": {
      "s": 2,
      "t": 3
    }
  },
  "created_at": "2025-10-23T10:00:00Z"
}
```

**Errors**:
    * 400 `– Missing or invalid "value" field`
    * 409 – String already exists
    * 422 – Invalid type for "value"


```GET /strings```
Retrieve strings with optional filters.
**Query Parameter**
| Parameter            | Type    | Description             |
| -------------------- | ------- | ----------------------- |
| `is_palindrome`      | boolean | true / false            |
| `min_length`         | integer | Minimum string length   |
| `max_length`         | integer | Maximum string length   |
| `word_count`         | integer | Exact number of words   |
| `contains_character` | string  | Single character filter |

**Example**
`GET /strings?is_palindrome=true&min_length=5`

`GET /strings/filter-by-natural-language`
Filter using natural language queries (powered by NLP).

```GET /strings/filter-by-natural-language?query=all single word palindromic strings```


```json
{
  "data": [/* matching results */],
  "count": 3,
  "interpreted_query": {
    "original": "all single word palindromic strings",
    "parsed_filters": {
      "word_count": 1,
      "is_palindrome": true
    }
  }
}
```

`DELETE /string/:string_value`
Delete a string from the system.

**Example**:
```
DELETE /string/hello
```

**Response**:
* 204 No Content – Successfully deleted
* 404 Not Found – String not found



## 📌 NOTES
* All data is stored in-memory (resets on server restart)
* NLP queries are handled with Compromise
* Error responses follow REST conventions
* CORS and Rate Limiting are enabled globally
