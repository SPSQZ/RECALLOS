// ==========================================================================
// RecallOS — Interactive Force-Directed Knowledge Graph Canvas Engine
// ==========================================================================

export class KnowledgeGraphEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.animationId = null;
    this.hoveredNode = null;
    this.nodes = [];
    this.edges = [];
  }

  init() {
    if (!this.canvas || !this.ctx) return;
    this.resize();
    this.setupData();
    this.setupEvents();
    this.start();
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    this.canvas.width = parent.clientWidth || 900;
    this.canvas.height = 460;
  }

  setupData() {
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;

    this.nodes = [
      { id: 1, label: 'RecallOS Core', x: cx, y: cy, radius: 24, color: '#76B900', desc: 'Central orchestration hub connecting memory, router, and privacy shield.', vx: 0, vy: 0 },
      { id: 2, label: 'ChromaDB Local', x: cx - 180, y: cy - 90, radius: 18, color: '#8AE000', desc: 'Encrypted on-device vector database storing semantic embeddings.', vx: 0.15, vy: -0.1 },
      { id: 3, label: 'FastAPI Router', x: cx + 180, y: cy - 90, radius: 18, color: '#6366F1', desc: 'High-performance API server with tokenization interceptors.', vx: -0.1, vy: 0.15 },
      { id: 4, label: 'PII Shield Interceptor', x: cx - 210, y: cy + 110, radius: 17, color: '#06B6D4', desc: 'Deterministic tokenizer preventing sensitive entity leakage.', vx: 0.12, vy: 0.08 },
      { id: 5, label: 'Nebius Token Factory', x: cx + 220, y: cy + 100, radius: 18, color: '#818CF8', desc: 'Cloud serverless inference cluster powering Nemotron models.', vx: -0.12, vy: -0.1 },
      { id: 6, label: 'Nemotron Nano-4B', x: cx + 330, y: cy - 10, radius: 15, color: '#76B900', desc: 'Fast-path low latency model (<150ms) for everyday summarization.', vx: 0.08, vy: 0.06 },
      { id: 7, label: 'Nemotron 3 Ultra', x: cx + 340, y: cy + 120, radius: 15, color: '#6366F1', desc: 'Deep reasoning model escalated for multi-step complex workflows.', vx: -0.06, vy: -0.08 },
      { id: 8, label: 'NemoClaw Guardrails', x: cx, y: cy + 160, radius: 16, color: '#F59E0B', desc: 'Safety policy barrier enforcing human approval for agent actions.', vx: 0.05, vy: -0.05 },
      { id: 9, label: 'SQLite Relational DB', x: cx - 110, y: cy - 170, radius: 14, color: '#A3A3A3', desc: 'Local storage for tasks, milestones, and conversation logs.', vx: -0.08, vy: 0.06 },
      { id: 10, label: 'Tavily Search API', x: cx + 110, y: cy - 170, radius: 14, color: '#22D3EE', desc: 'Secure real-time web retrieval tool for agent queries.', vx: 0.06, vy: 0.08 }
    ];

    this.edges = [
      [1, 2], [1, 3], [1, 4], [1, 5], [1, 8], [1, 9],
      [3, 5], [5, 6], [5, 7], [4, 2], [8, 10], [9, 1]
    ];
  }

  setupEvents() {
    this.canvas.addEventListener('mousemove', e => {
      const rect = this.canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      let found = null;
      for (const node of this.nodes) {
        const dx = node.x - mx;
        const dy = node.y - my;
        if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 6) {
          found = node;
          break;
        }
      }
      this.hoveredNode = found;
      this.canvas.style.cursor = found ? 'pointer' : 'default';

      const hud = document.getElementById('graph-node-hud');
      if (hud && found) {
        hud.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span class="pill-3d green">${found.label}</span>
            <span style="font-size:0.75rem; color:#A3A3A3;">Node #${found.id}</span>
          </div>
          <p style="font-size:0.82rem; color:#E5E7EB;">${found.desc}</p>
        `;
      }
    });
  }

  start() {
    if (this.animationId) cancelAnimationFrame(this.animationId);

    const render = () => {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      // Draw Edges
      this.edges.forEach(([fromId, toId]) => {
        const from = this.nodes.find(n => n.id === fromId);
        const to = this.nodes.find(n => n.id === toId);
        if (!from || !to) return;

        this.ctx.beginPath();
        this.ctx.moveTo(from.x, from.y);
        this.ctx.lineTo(to.x, to.y);
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        this.ctx.lineWidth = 1.5;
        this.ctx.stroke();
      });

      // Animate & Draw Nodes
      this.nodes.forEach(node => {
        node.x += node.vx;
        node.y += node.vy;

        // Bounce bounds
        if (node.x < node.radius + 20 || node.x > this.canvas.width - node.radius - 20) node.vx *= -1;
        if (node.y < node.radius + 20 || node.y > this.canvas.height - node.radius - 20) node.vy *= -1;

        const isHovered = this.hoveredNode === node;

        // Outer glow halo
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + (isHovered ? 12 : 8), 0, Math.PI * 2);
        this.ctx.fillStyle = node.color + '26';
        this.ctx.fill();

        // Node center body
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + (isHovered ? 2 : 0), 0, Math.PI * 2);
        this.ctx.fillStyle = node.color;
        this.ctx.shadowColor = node.color;
        this.ctx.shadowBlur = isHovered ? 20 : 12;
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        // Label
        this.ctx.font = '600 11px Inter, sans-serif';
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(node.label, node.x, node.y + node.radius + 16);
      });

      this.animationId = requestAnimationFrame(render);
    };

    render();
  }
}
