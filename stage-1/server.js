import express from 'express';
import bodyParser from 'body-parser';
import cors from "cors";
import { createServer } from "http";
import rateLimit from "express-rate-limit";
import 'dotenv/config';
import _ from 'lodash';
import crypto from "crypto";
import nlp from 'compromise';

const { BASE_URL, PORT, NAME, EMAIL } = process.env;
const { find, isEqual, uniq, countBy, includes, filter } = _;

const DATABASE = []; // In-memory Database

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '20mb' }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: { status: 429, message: "Too many requests, please try again later." },
});

app.use(limiter);

const server = createServer(app);

server.listen(PORT, () => {
  console.log(PORT);
  console.log("Server started successfully");
});

function hashSha256(text) {
  const hash = crypto.createHash('sha256');
  hash.update(text);
  return hash.digest('hex');
}

const charFrquencyMap = (str) => {
  return countBy(str);
}

const getStringProps = (stringToBeAnalysed) => {
  const string = stringToBeAnalysed.toLowerCase();
  return {
    length: string.length,
    is_palindrome: isEqual(string, string.split('').reverse().join("")),
    unique_characters: uniq(string.split('')).length,
    word_count: string.split(" ").length,
    sha256_hash: hashSha256(string),
    character_frequency_map: charFrquencyMap(string)
  }
}

app.post("/strings", (req, res) => {
  const requestBody = req.body;

  const string = requestBody?.value;

  if (!string) {
    return res.status(400).send("Invalid request body or missing \"value\" field");
  }

  if (typeof string !== "string") {
    return res.status(422).send("Invalid data type for \"value\"(must be string)");
  }

  if (find(DATABASE, (data) => data.value === string)) {
    res.status(409).send("String already exist in the system");
    return;
  }

  const responseData = {
    id: hashSha256(string),
    value: string,
    properties: getStringProps(string),
    created_at: new Date().toISOString(),
  }

  DATABASE.push(responseData);

  res.status(201).send(responseData);
  return;
});

app.get("/string/:string_value", (req, res) => {
  const string = req.params.string_value;

  const stringData = find(DATABASE, (data) => data.value === string);
  if (!stringData) {
    return res.status(404).send("String does not exist in the system");
  }
  return res.status(200).send(stringData);
});

function filterString(params) {
  let {
    is_palindrome,
    min_length,
    max_length,
    word_count,
    contains_character
  } = params;
  if (is_palindrome) {
    if (is_palindrome !== 'true' && is_palindrome !== 'false') {
      return res.status(400).send("is_palindrome must be 'true' or 'false'")
    }
    is_palindrome = is_palindrome === 'true';
  }

  if (min_length) {
    min_length = parseInt(min_length, 10);
    if (isNaN(min_length) || min_length < 0) {
      return res.status(400).send("min_length must be a non-negative integer");
    }
  }

  if (max_length) {
    max_length = parseInt(max_length, 10);
    if (isNaN(max_length) || max_length < 0) {
      return res.status(400).send("max_length must be a non-negative integer");
    }
  }

  if (word_count) {
    word_count = parseInt(word_count, 10);
    if (isNaN(word_count) || word_count < 0) {
      return res.status(400).send("word_count must be a non-negative integer");
    }
  }

  if (contains_character) {
    if (typeof contains_character !== "string" || contains_character.length > 1) {
      return res.status(400).send("contains_character must be a single character");
    }
  }

  const filteredData = filter(DATABASE, (data) => {
    if (is_palindrome && data.is_palindrome !== is_palindrome) {
      return false;
    }

    if (min_length && data.length < min_length) {
      return false;
    }

    if (max_length && data.length > max_length) {
      return false;
    }

    if (word_count && data.word_count < word_count) {
      return false;
    }

    if (contains_character && !includes(data.value, contains_character)) {
      return false;
    }
    return true;
  })
}

app.get("/strings", (req, res) => {
  let {
    is_palindrome,
    min_length,
    max_length,
    word_count,
    contains_character
  } = req.query;

  const params = req.query;

  const filteredData = filterString(params);

  const response = {
    data: filteredData,
    count: filteredData.length,
    filter_applied: {
      ...req.query,
    }
  }

  return res.status(200).send(response);
});

app.get("/strings/filter-by-natural-language", (req, res) => {
  const nlpQuery = req.query.query;

  function parseQueryNLP(query) {
    const doc = nlp(query);
    const filters = {};

    // Word count
    if (doc.match('(single|one) word').found) filters.word_count = 1;
    const wordCount = doc.match('word count #Value').numbers().out('number');
    if (wordCount.length) filters.word_count = wordCount[0];

    // Palindrome
    if (doc.match('palindrom(e|ic)').found) filters.is_palindrome = true;

    // Length filters
    const longer = doc.match('(longer|more|greater) than #Value').numbers().out('number');
    if (longer.length) filters.min_length = longer[0] + 1;

    const shorter = doc.match('(shorter|less|lesser) than #Value').numbers().out('number');
    if (shorter.length) filters.max_length = shorter[0] - 1;

    return filters;
  }

  const filters = parseQueryNLP(nlpQuery);

  const filteredData = filterString(filters);

  const response = {
    data: filteredData,
    count: filteredData.length,
    interpreted_query: {
      original: "",
      parsed_filters: {
        ...filters
      }
    }
  }

  return res.status(200).send(response);
});

app.delete("/string/:string_value", (req, res) => {
  const string = req.params.string_value.toLowerCase();

  const stringToDel = find(DATABASE, (data) => data.value.toLowerCase() === string);
  const index = stringToDel ? DATABASE.indexOf(stringToDel) : -1;
  if (index >= 0) {
    DATABASE.splice(index, 1);
    return res.status(204).send();
  }
  return res.status(404).send("String does not exist in the system");
});