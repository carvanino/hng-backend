import express from 'express';
import axios from "axios"
import cors from "cors";
import { createServer } from "http";
import rateLimit from "express-rate-limit";
import 'dotenv/config';

const { BASE_URL, PORT, NAME, EMAIL } = process.env;

const app = express();
app.use(cors());

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

const makeAPIRequest = async () => {
    try {
        const requestResponse = await axios.get(BASE_URL, {
            timeout: 15000,
        });
        const responseStatus = requestResponse.status;
        const responseData = requestResponse.data;

        const response = {
            status: responseStatus,
            user: {
                email: EMAIL,
                name: NAME,
                stack: "Node.js/Express"
            },
            timestamp: new Date().toISOString(),
            fact: responseData?.fact,
        }
        return response;
    } catch (err) {
        return {
            status: 502,
            message: "Failed to fetch data from external API"
        };
    }
}

app.get("/", async (req, res) => {
    res.send({
        status: 200,
        message: "Welcome Home"
    })
});

app.get("/me", async (req, res) => {
    const response = await makeAPIRequest()
    if (response.status === 200) {
        res.status(200).send(response);
        return;
    }
    if (response.status >= 400 && response.status < 500) {
        res.status(response.status).send({
            status: response.status,
            message: "Bad request, something went wrong and we couldn't process the request correctly",
        })
        return;
    }
    res.status(500).send({
        status: response.status,
        message: "A server error occured"
    })
    return
});

