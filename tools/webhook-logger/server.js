const fs = require('fs');
const http = require('http');

const PORT = Number(process.env.PORT || 8084);
const LOG_FILE = process.env.LOG_FILE || '/logs/requests.log';

function ensureLogPath() {
  fs.mkdirSync('/logs', { recursive: true });
  if (!fs.existsSync(LOG_FILE)) {
    fs.writeFileSync(LOG_FILE, 'Webhook request log\n\n', 'utf8');
  }
}

function appendLog(text) {
  fs.appendFileSync(LOG_FILE, text, 'utf8');
}

ensureLogPath();

const server = http.createServer((req, res) => {
  const path = (req.url || '').split('?')[0];

  // Do not log log-file retrieval requests.
  if (req.method === 'GET' && path === '/logs') {
    try {
      const content = fs.readFileSync(LOG_FILE, 'utf8');
      res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(content);
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(`failed to read log file: ${String(err)}\n`);
    }
    return;
  }

  // Ignore browser favicon requests.
  if (req.method === 'GET' && path === '/favicon.ico') {
    res.writeHead(204);
    res.end();
    return;
  }

  const chunks = [];

  req.on('data', (chunk) => {
    chunks.push(chunk);
  });

  req.on('end', () => {
    const body = Buffer.concat(chunks).toString('utf8');
    const entry = [
      '---',
      `timestamp: ${new Date().toISOString()}`,
      `remote: ${req.socket.remoteAddress || 'unknown'}`,
      `method: ${req.method}`,
      `url: ${req.url}`,
      'headers:',
      JSON.stringify(req.headers, null, 2),
      'body:',
      body || '<empty>',
      '',
    ].join('\n');

    appendLog(entry);

    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('ok\n');
  });

  req.on('error', (err) => {
    appendLog(`request_error: ${new Date().toISOString()} ${String(err)}\n`);
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('error\n');
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Webhook logger listening on 0.0.0.0:${PORT}`);
  console.log(`Writing logs to ${LOG_FILE}`);
});
