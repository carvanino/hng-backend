import axios from "axios";
import fs from "fs";
import path from "path";
import 'dotenv/config';
import _ from 'lodash';
import { createCanvas } from "canvas";

const { map, random } = _;

const { COUNTRY_BASE_URL, EXCHANGE_RATE_BASE_URL } = process.env;


export const getCountries = async () => {
	const countries = (await axios.get(COUNTRY_BASE_URL)).data;
	const exchangeRateData = (await axios.get(EXCHANGE_RATE_BASE_URL)).data;

	const countryData = map(countries, (country) => {
		let countryCurrency = null;
		let exchangeRate = 0;
		let estimatedGDP = 0;

		if (country.currencies && country.currencies.length > 0) {
			countryCurrency = country.currencies[0].code;

			exchangeRate = exchangeRateData.rates[countryCurrency];

			if (exchangeRate) {
				// population × random(1000–2000) ÷ exchange_rate
				const rand = random(1000, 2000, false);
				estimatedGDP = country.population * rand / exchangeRate;
			} else {
				exchangeRate = null;
				estimatedGDP = null;
			}

		}

		const data = {
			name: country.name,
			capital: country.capital,
			region: country.region,
			population: country.population,
			currency_code: countryCurrency,
			exchange_rate: exchangeRate,
			estimated_gdp: estimatedGDP,
			flag_url: country?.flag,
			last_refreshed_at: new Date(),
		}

		return data;
	});
	return countryData;
}

export async function generateSummaryImage(countries, totalCountry, lastRefreshedAt) {
	const width = 1200;
	const height = 600;
	const canvas = createCanvas(width, height);
	const ctx = canvas.getContext("2d");

	// Background
	ctx.fillStyle = "#f4f4f4";
	ctx.fillRect(0, 0, width, height);

	ctx.fillStyle = "#333";
	ctx.font = "28px Sans";
	ctx.fillText("Countries Summary", 20, 50);

	// Total countries
	ctx.font = "24px Sans";
	ctx.fillText(`Total Countries: ${totalCountry}`, 20, 100);

	// Top 5 countries by estimated GDP
	const top5 = [...countries]
		.sort((a, b) => b.estimated_gdp - a.estimated_gdp)
		.slice(0, 5);

	ctx.fillText("Top 5 Countries by Estimated GDP:", 20, 150);

	ctx.font = "20px Sans";
	top5.forEach((c, i) => {
		ctx.fillText(
			`${i + 1}. ${c.name} — $${Number(c.estimated_gdp).toLocaleString()}`,
			40,
			180 + i * 30
		);
	});

	// Last refreshed timestamp
	ctx.font = "22px Sans";
	ctx.fillText(`Last Refreshed At: ${lastRefreshedAt}`, 20, 400);

	// Ensure cache folder exists
	const cacheDir = path.join(process.cwd(), "cache");
	if (!fs.existsSync(cacheDir)) fs.mkdirSync(cacheDir);

	const outputPath = path.join(cacheDir, "summary.png");

	const buffer = canvas.toBuffer("image/png");
	fs.writeFileSync(outputPath, buffer);
}
