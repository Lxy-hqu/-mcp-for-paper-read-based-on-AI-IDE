import http from 'http';

export interface LLMResponse {
  text: string;
}

export class LocalLLM {
  private model: string;
  private host: string;
  private port: number;

  constructor(model: string = "llama3", host: string = "127.0.0.1", port: number = 11434) {
    this.model = model;
    this.host = host;
    this.port = port;
  }

  async isAvailable(): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.request({
        hostname: this.host,
        port: this.port,
        path: '/api/tags',
        method: 'GET',
        timeout: 2000
      }, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
      req.end();
    });
  }

  async chat(prompt: string, systemPrompt?: string): Promise<string | null> {
    if (!await this.isAvailable()) {
      return null;
    }

    const payload = JSON.stringify({
      model: this.model,
      prompt: prompt,
      system: systemPrompt,
      stream: false
    });

    return new Promise((resolve, reject) => {
      const req = http.request({
        hostname: this.host,
        port: this.port,
        path: '/api/generate',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload)
        },
        timeout: 60000 // 60s timeout
      }, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          if (res.statusCode === 200) {
            try {
              const json = JSON.parse(data);
              resolve(json.response);
            } catch (e) {
              reject(e);
            }
          } else {
            resolve(null);
          }
        });
      });

      req.on('error', (e) => resolve(null));
      req.write(payload);
      req.end();
    });
  }
}

export const llm = new LocalLLM();
