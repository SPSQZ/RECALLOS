// ==========================================================================
// RecallOS — Shared 3D Mechanical Interaction & Audio Engine
// Web Audio API Synthesizer (Dual-Tone Keycap Actuation) + Cursor Sheen
// ==========================================================================

export class MechanicalSoundEngine {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playClick(type = 'press') {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    const t = this.ctx.currentTime;
    
    // High-frequency switch leaf snap
    const oscHigh = this.ctx.createOscillator();
    const gainHigh = this.ctx.createGain();
    oscHigh.type = 'triangle';
    oscHigh.frequency.setValueAtTime(type === 'press' ? 1600 : 1200, t);
    oscHigh.frequency.exponentialRampToValueAtTime(300, t + 0.02);

    gainHigh.gain.setValueAtTime(0.16, t);
    gainHigh.gain.exponentialRampToValueAtTime(0.001, t + 0.025);

    oscHigh.connect(gainHigh);
    gainHigh.connect(this.ctx.destination);

    oscHigh.start(t);
    oscHigh.stop(t + 0.025);

    // Low-frequency chassis acoustic bottom-out
    const oscLow = this.ctx.createOscillator();
    const gainLow = this.ctx.createGain();
    oscLow.type = 'sine';
    oscLow.frequency.setValueAtTime(140, t);
    oscLow.frequency.exponentialRampToValueAtTime(45, t + 0.04);

    gainLow.gain.setValueAtTime(0.12, t);
    gainLow.gain.exponentialRampToValueAtTime(0.001, t + 0.04);

    oscLow.connect(gainLow);
    gainLow.connect(this.ctx.destination);

    oscLow.start(t);
    oscLow.stop(t + 0.04);
  }

  toggle() {
    this.enabled = !this.enabled;
    return this.enabled;
  }
}

// Global instance
export const soundEngine = new MechanicalSoundEngine();
window.soundEngine = soundEngine;
window.trigger3DClickSound = function(type = 'press') {
  soundEngine.playClick(type);
};

// Attach listeners for 3D buttons and cursor spotlight sheen
export function init3DInteractions() {
  document.querySelectorAll('.btn-3d, .switch-3d, .memory-chip-3d, .nav-link').forEach(el => {
    if (!el.dataset.soundBound) {
      el.dataset.soundBound = 'true';
      el.addEventListener('click', () => {
        soundEngine.playClick('press');
      });
    }
  });

  document.querySelectorAll('.card-3d-slab').forEach(card => {
    let sheen = card.querySelector('.cursor-sheen');
    if (!sheen) {
      sheen = document.createElement('div');
      sheen.className = 'cursor-sheen';
      card.prepend(sheen);
    }

    if (!card.dataset.sheenBound) {
      card.dataset.sheenBound = 'true';
      card.addEventListener('pointerenter', e => {
        sheen.style.setProperty('--sheen-opacity', '1');
        updateCardSheen(card, sheen, e);
      });

      card.addEventListener('pointermove', e => {
        updateCardSheen(card, sheen, e);
      });

      card.addEventListener('pointerleave', () => {
        sheen.style.setProperty('--sheen-opacity', '0');
      });
    }
  });
}

function updateCardSheen(card, sheen, event) {
  const rect = card.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  sheen.style.setProperty('--mouse-x', `${x}px`);
  sheen.style.setProperty('--mouse-y', `${y}px`);
}

document.addEventListener('DOMContentLoaded', init3DInteractions);
