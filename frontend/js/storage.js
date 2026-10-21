// ==========================================================================
// RecallOS — Local Relational & Vector Storage Layer
// Simulates local SQLite database and ChromaDB vector collections in browser
// ==========================================================================

const DEFAULT_MEMORIES = [
  {
    id: 'MEM-104',
    category: 'tech-stack',
    score: 0.96,
    text: 'Decided to build RecallOS using FastAPI for backend orchestration and React + Tailwind CSS for UI.',
    source: 'Conversation #12 ("Architecture Discussion")',
    timestamp: 'Saved 2 days ago',
    active: true
  },
  {
    id: 'MEM-108',
    category: 'security',
    score: 0.99,
    text: 'Never transmit client API keys, personal phone numbers, or credentials to external cloud endpoints.',
    source: 'Setup Protocol',
    timestamp: 'Saved Oct 14, 2026',
    active: true
  },
  {
    id: 'MEM-112',
    category: 'learning',
    score: 0.91,
    text: 'Started studying Data Structures & Algorithms in C++ (superseded basic Python loops).',
    source: 'Conversation #14',
    timestamp: 'Saved Yesterday',
    active: true
  }
];

const DEFAULT_TASKS = [
  { id: 'T-1', title: 'Provision Nebius Token Factory API keys', completed: true, timestamp: 'Completed Oct 16' },
  { id: 'T-2', title: 'Validate local ChromaDB vector environment', completed: true, timestamp: 'Completed Oct 16' },
  { id: 'T-3', title: 'Build Real-Time Privacy Audit UI Panel', completed: false, priority: 'HIGH', due: 'Oct 20' },
  { id: 'T-4', title: 'Script 3-minute video pitch (30s Problem, 90s Demo, 30s Architecture)', completed: false, priority: 'HIGH', due: 'Oct 28' }
];

export class LocalStorageManager {
  constructor() {
    this.MEMORIES_KEY = 'recallos_memories_v1';
    this.TASKS_KEY = 'recallos_tasks_v1';
    this.SETTINGS_KEY = 'recallos_settings_v1';
  }

  getMemories() {
    try {
      const data = localStorage.getItem(this.MEMORIES_KEY);
      return data ? JSON.parse(data) : DEFAULT_MEMORIES;
    } catch {
      return DEFAULT_MEMORIES;
    }
  }

  saveMemories(memories) {
    try {
      localStorage.setItem(this.MEMORIES_KEY, JSON.stringify(memories));
    } catch (e) {
      console.warn('Storage quota exceeded or unavailable', e);
    }
  }

  addMemory(text, category = 'general') {
    const list = this.getMemories();
    const newId = `MEM-${Math.floor(100 + Math.random() * 900)}`;
    const item = {
      id: newId,
      category,
      score: 0.95,
      text,
      source: 'Manual Memory Creation',
      timestamp: 'Just now',
      active: true
    };
    list.unshift(item);
    this.saveMemories(list);
    return item;
  }

  markSuperseded(id) {
    const list = this.getMemories().map(m => m.id === id ? { ...m, active: false } : m);
    this.saveMemories(list);
  }

  deleteMemory(id) {
    const list = this.getMemories().filter(m => m.id !== id);
    this.saveMemories(list);
  }

  getTasks() {
    try {
      const data = localStorage.getItem(this.TASKS_KEY);
      return data ? JSON.parse(data) : DEFAULT_TASKS;
    } catch {
      return DEFAULT_TASKS;
    }
  }

  saveTasks(tasks) {
    try {
      localStorage.setItem(this.TASKS_KEY, JSON.stringify(tasks));
    } catch (e) {
      console.warn(e);
    }
  }

  toggleTask(id) {
    const tasks = this.getTasks().map(t => t.id === id ? { ...t, completed: !t.completed } : t);
    this.saveTasks(tasks);
    return tasks;
  }

  addTask(title) {
    const tasks = this.getTasks();
    const newTask = {
      id: `T-${Date.now()}`,
      title,
      completed: false,
      priority: 'MEDIUM',
      due: 'Pending'
    };
    tasks.push(newTask);
    this.saveTasks(tasks);
    return newTask;
  }

  purgeAll() {
    localStorage.removeItem(this.MEMORIES_KEY);
    localStorage.removeItem(this.TASKS_KEY);
    localStorage.removeItem(this.SETTINGS_KEY);
  }
}

export const localStore = new LocalStorageManager();
