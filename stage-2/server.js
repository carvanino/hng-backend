import express from 'express';
import bodyParser from 'body-parser';
import cors from "cors";
import { createServer } from "http";
import rateLimit from "express-rate-limit";
import 'dotenv/config';
import _ from 'lodash';
import mysql from "mysql2/promise";
import fs from "fs";
import { getCountries, generateSummaryImage } from './data_api.js';

const { DB, DB_PORT, DB_PASSWORD, DB_USER, PORT, IMAGE_PATH, DB_HOST, DB_SSL_CERT_PATH } = process.env;
const { map, forEach } = _;

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '20mb' }));

let DBconn;

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: { status: 429, message: "Too many requests, please try again later." },
});

app.use(limiter);

const server = createServer(app);


const connectDB = async () => {
  try {
    const DBConfig = {
      host: DB_HOST,
      user: DB_USER,
      password: DB_PASSWORD,
      database: DB,
      port: DB_PORT,
    };
    if (DB_SSL_CERT_PATH) {
      DBConfig['ssl'] = {
        ca: fs.readFileSync(DB_SSL_CERT_PATH)
      }
    }

    DBconn = await mysql.createConnection(DBConfig);

    console.log(`Database Successfully connected on ${DB_PORT}`);
    console.log('CREATING DATABASE TABLE');

    await DBconn.query(`
      CREATE TABLE IF NOT EXISTS countries (
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
      )
  `);
  } catch (error) {
    console.log(error);
  }
}

server.listen(PORT, async () => {
  console.log(PORT);
  console.log(DB)
  console.log("Server started successfully");

  console.log("\n-------------------------------");
  console.log("Connecting to DB");
  await connectDB()
});

app.post("/countries/refresh", async (req, res) => {
  try {
    const countries = await getCountries();

    const countryValues = map(countries, (country) => {
      return [
        country.name,
        country.capital,
        country.region,
        country.population,
        country.currency_code,
        country.exchange_rate,
        country.estimated_gdp,
        country.flag_url,
        country.last_refreshed_at
      ]
    });

    await DBconn.query(`
      CREATE TABLE IF NOT EXISTS refresh_status (
        id INT PRIMARY KEY,
        last_refreshed_at DATETIME
      )`
    );

    const upsertQuery = `
      INSERT INTO countries
        (name, capital, region, population, currency_code, exchange_rate, estimated_gdp, flag_url, last_refreshed_at)
      VALUES ?
      AS new
      ON DUPLICATE KEY UPDATE
        capital = new.capital,
        region = new.region,
        population = new.population,
        currency_code = new.currency_code,
        exchange_rate = new.exchange_rate,
        estimated_gdp = new.estimated_gdp,
        flag_url = new.flag_url,
        last_refreshed_at = new.last_refreshed_at
    `;

    await DBconn.query(`
      INSERT INTO refresh_status (id, last_refreshed_at)
      VALUES (1, NOW())
      ON DUPLICATE KEY UPDATE last_refreshed_at = NOW()
    `);

    await DBconn.query(upsertQuery, [countryValues]);

    const [
      [[{ total: totalCountries }]],
      [top5CountryByGDP],
      [[{ last_refreshed_at: lastRefreshedAt }]]
    ] = await Promise.all([
      DBconn.query(`SELECT COUNT(*) AS total FROM countries`),
      DBconn.query(`
        SELECT name, estimated_gdp 
        FROM countries
        ORDER BY estimated_gdp DESC
        LIMIT 5
      `),
      DBconn.query(`
        SELECT last_refreshed_at FROM refresh_status WHERE id = 1
      `)
    ]);

    res.status(201).send();

    await generateSummaryImage(top5CountryByGDP, totalCountries, lastRefreshedAt);
  } catch (error) {
    console.log("ERRROR ", error);
    return res.status(503).send({
      error: "External data source unavailable",
      details: error.message
    });
  }
});

app.get("/countries/image", (req, res) => {
  // check if image exists first
  if (!fs.existsSync(IMAGE_PATH)) {
    return res.status(404).json({ error: "Summary image not found" });
  }
  // set content type header
  res.setHeader("Content-Type", "image/png");

  // This will read directly and display, if the file is large, problem!
  // This also is in-memory - expensive
  /* const imageStream = fs.readFileSync(IMAGE_PATH);
  return res.status(200).send(imageStream); */

  // This read the file in chunks and render
  const imageStream = fs.createReadStream(IMAGE_PATH);
  imageStream.pipe(res);
});

app.get("/countries", async (req, res) => {
  const { query } = req;
  const { region, sort, currency } = query;

  let filters = [];
  let values = [];

  if (region) {
    filters.push("region = ?");
    values.push(region);
  }
  if (currency) {
    filters.push("currency_code = ?");
    values.push(currency);
  }

  let sqlQuery = "SELECT * FROM countries";
  if (filters.length > 0) {
    sqlQuery += " WHERE " + filters.join(" AND ");
  }

  if (sort) {
    const sortBy = sort.split('_').at(-1);
    sqlQuery += " ORDER BY estimated_gdp " + sortBy.toUpperCase();
  }

  const [countries] = await DBconn.query(sqlQuery, values);

  return res.status(200).json(countries);
})

app.get("/countries/:name", async (req, res) => {
  const countryName = req.params.name;

  const [[country]] = await DBconn.query("SELECT * FROM countries WHERE name=?", [countryName]);

  if (!country) {
    return res.status(404).json({ error: "Country not found" });
  }
  return res.status(200).json(country);
});

app.delete("/countries/:name", async (req, res) => {
  const countryName = req.params.name;

  const [deleteResult] = await DBconn.query(`
      DELETE FROM countries WHERE name = ?
    `,
    [countryName]
  );

  if (!deleteResult.affectedRows) {
    return res.status(404).json({ error: "Country not found" });
  }
  return res.status(204).send();
});

app.get("/status", async (req, res) => {
  const [
    [[{ total: totalCountries }]],
    [[{ last_refreshed_at: lastRefreshedAt }]]
  ] = await Promise.all([
    DBconn.query(`SELECT COUNT(*) AS total FROM countries`),
    DBconn.query(`
      SELECT last_refreshed_at FROM refresh_status WHERE id = 1
    `)
  ]);

  const response = {
    total_countries: totalCountries,
    last_refreshed_at: lastRefreshedAt
  };

  return res.status(200).send(response);
});