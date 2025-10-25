import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

const app = express();
import 'dotenv/config';

const PORT = process.env.GATEWAY_PORT || 3000;

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Gateway server running' });
});

// Proxy to stage-0 server
app.use('/stage-0', createProxyMiddleware({
  target: 'http://localhost:3001',
  changeOrigin: true,
  pathRewrite: {
    '^/stage-0': '', // Remove /stage-0 prefix when forwarding
  },
  onError: (err, req, res) => {
    console.log(err);
    console.error('Proxy error for stage-0:', err.message);
    res.status(502).json({ error: 'stage-0 server unavailable' });
  }
}));

// Proxy to stage-1 server
app.use('/stage-1', createProxyMiddleware({
  target: 'http://localhost:3002',
  changeOrigin: true,
  pathRewrite: {
    '^/stage-1': '', // Remove /stage-1 prefix when forwarding
  },
  onError: (err, req, res) => {
    console.error('Proxy error for stage-1:', err.message);
    res.status(502).json({ error: 'stage-1 server unavailable' });
  }
}));

app.use('/stage-2', createProxyMiddleware({
  target: 'http://localhost:3003',
  changeOrigin: true,
  pathRewrite: {
    '^/stage-2': '', // Remove /stage-1 prefix when forwarding
  },
  onError: (err, req, res) => {
    console.error('Proxy error for stage-2:', err.message);
    res.status(502).json({ error: 'stage-2 server unavailable' });
  }
}));

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'HNG Backend Gateway',
    endpoints: {
      'stage-0': '/stage-0',
      'stage-1': '/stage-1',
      'health': '/health'
    }
  });
});

app.listen(PORT, () => {
  console.log(`Gateway server running on http://localhost:${PORT}`);
  console.log(`Stage-0 accessible at http://localhost:${PORT}/stage-0`);
  console.log(`Stage-1 accessible at http://localhost:${PORT}/stage-1`);
  console.log(`Stage-2 accessible at http://localhost:${PORT}/stage-2`);
});
