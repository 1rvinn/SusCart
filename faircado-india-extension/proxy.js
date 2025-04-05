import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';

const app = express();
app.use(cors());

app.get('/proxy', async (req, res) => {
    const targetUrl = req.query.url;
    if (!targetUrl) return res.status(400).json({ error: 'Missing URL parameter' });

    try {
        const response = await fetch(targetUrl, { headers: { 'User-Agent': 'Mozilla/5.0' } });
        const data = await response.text();
        res.send(data);
    } catch (error) {
        res.status(500).json({ error: error.toString() });
    }
});

app.listen(3000, () => console.log('Proxy server running on port 3000'));
