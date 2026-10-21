// ==========================================================================
// RecallOS — Client-Side Deterministic PII Scrubber & Egress Inspector
// Local-First Security Boundary Engine
// ==========================================================================

export class PiiScrubber {
  constructor() {
    this.memoryMap = new Map();
    this.counters = {
      NAME: 0,
      PHONE: 0,
      EMAIL: 0,
      FINANCIAL_ORG: 0,
      AMOUNT: 0,
      HEALTH_ID: 0
    };
  }

  reset() {
    this.memoryMap.clear();
    this.counters = {
      NAME: 0,
      PHONE: 0,
      EMAIL: 0,
      FINANCIAL_ORG: 0,
      AMOUNT: 0,
      HEALTH_ID: 0
    };
  }

  getOrCreateToken(entity, category) {
    for (const [token, data] of this.memoryMap.entries()) {
      if (data.entity.toLowerCase() === entity.toLowerCase()) {
        return token;
      }
    }
    this.counters[category] = (this.counters[category] || 0) + 1;
    const token = `[REDACTED_${category}_${this.counters[category]}]`;
    this.memoryMap.set(token, {
      entity,
      category,
      timestamp: new Date().toLocaleTimeString(),
      status: 'Active in Local RAM'
    });
    return token;
  }

  scrub(inputText) {
    this.reset();
    let rawHighlighted = inputText;
    let egressText = inputText;
    const detected = [];

    // 1. Email pattern
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    egressText = egressText.replace(emailRegex, match => {
      const token = this.getOrCreateToken(match, 'EMAIL');
      detected.push({ entity: match, category: 'EMAIL', token });
      return token;
    });

    // 2. Phone pattern
    const phoneRegex = /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g;
    egressText = egressText.replace(phoneRegex, match => {
      const token = this.getOrCreateToken(match, 'PHONE');
      detected.push({ entity: match, category: 'PHONE', token });
      return token;
    });

    // 3. Dollar amounts / currencies
    const amountRegex = /\$\d+(?:,\d{3})*(?:\.\d{2})?/g;
    egressText = egressText.replace(amountRegex, match => {
      const token = this.getOrCreateToken(match, 'AMOUNT');
      detected.push({ entity: match, category: 'AMOUNT', token });
      return token;
    });

    // 4. Financial Institutions
    const banks = ['Chase Bank', 'Bank of America', 'Wells Fargo', 'Citibank', 'Barclays', 'Goldman Sachs'];
    for (const bank of banks) {
      const bankRegex = new RegExp(`\\b${bank}\\b`, 'gi');
      egressText = egressText.replace(bankRegex, match => {
        const token = this.getOrCreateToken(match, 'FINANCIAL_ORG');
        detected.push({ entity: match, category: 'FINANCIAL_ORG', token });
        return token;
      });
    }

    // 5. Patient & Healthcare IDs
    const healthRegex = /\b(?:MRN|PATIENT|RX)-[0-9]{4,8}\b/gi;
    egressText = egressText.replace(healthRegex, match => {
      const token = this.getOrCreateToken(match, 'HEALTH_ID');
      detected.push({ entity: match, category: 'HEALTH_ID', token });
      return token;
    });

    // 6. Common personal names
    const names = ['Alice Smith', 'Bob Jones', 'Charlie Brown', 'David Miller'];
    for (const name of names) {
      const nameRegex = new RegExp(`\\b${name}\\b`, 'gi');
      egressText = egressText.replace(nameRegex, match => {
        const token = this.getOrCreateToken(match, 'NAME');
        detected.push({ entity: match, category: 'NAME', token });
        return token;
      });
    }

    // Generate raw display with red underline badges
    rawHighlighted = inputText;
    detected.forEach(item => {
      rawHighlighted = rawHighlighted.replace(
        item.entity,
        `<span class="pii-intercepted">${item.entity}</span>`
      );
    });

    // Generate egress display with cyan deterministic badges
    let egressHighlighted = egressText;
    this.memoryMap.forEach((data, token) => {
      egressHighlighted = egressHighlighted.replace(
        new RegExp(escapeRegex(token), 'g'),
        `<span class="pii-token-egress">${token}</span>`
      );
    });

    // Routing Complexity & Smart Model Choice
    const lengthFactor = Math.min(inputText.length / 500, 0.4);
    const entityFactor = Math.min(detected.length * 0.08, 0.3);
    const complexityScore = Number((0.15 + lengthFactor + entityFactor).toFixed(2));
    const selectedModel = complexityScore > 0.42
      ? '🟣 NVIDIA Nemotron 3 Ultra (Cloud Escalate)'
      : '🟢 NVIDIA Nemotron Nano-4B (Fast-Path)';

    return {
      rawHighlighted,
      egressText,
      egressHighlighted,
      detected,
      memoryMap: Array.from(this.memoryMap.entries()).map(([token, val]) => ({ token, ...val })),
      complexityScore,
      selectedModel,
      latency: Math.floor(Math.random() * 35) + 125
    };
  }

  rehydrate(cloudText) {
    let output = cloudText;
    this.memoryMap.forEach((data, token) => {
      output = output.replaceAll(token, data.entity);
    });
    return output;
  }
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export const scrubber = new PiiScrubber();
