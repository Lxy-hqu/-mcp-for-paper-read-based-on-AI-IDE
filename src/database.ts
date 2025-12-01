import Database from "better-sqlite3";
import fs from "fs";
import path from "path";

const DB_PATH = path.join(process.cwd(), "papers.db");

export class PaperDatabase {
  private db: Database.Database;

  constructor() {
    this.db = new Database(DB_PATH);
    this.init();
  }

  private init() {
    // Papers Table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        title TEXT,
        authors TEXT,
        year INTEGER,
        abstract TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Symbols Table (for Math Explainer)
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER,
        symbol TEXT,
        definition TEXT,
        latex TEXT,
        FOREIGN KEY(paper_id) REFERENCES papers(id)
      );
    `);

    // Experiments Table (for Experiment Reproduction)
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER,
        dataset TEXT,
        metric_name TEXT,
        metric_value TEXT,
        hyperparameters TEXT,
        FOREIGN KEY(paper_id) REFERENCES papers(id)
      );
    `);
  }

  addPaper(path: string, title: string, authors: string, abstract: string) {
    const stmt = this.db.prepare(
      "INSERT OR IGNORE INTO papers (path, title, authors, abstract) VALUES (?, ?, ?, ?)"
    );
    return stmt.run(path, title, authors, abstract);
  }

  getPaperByPath(path: string): { id: number; path: string; title: string } | undefined {
    return this.db.prepare("SELECT * FROM papers WHERE path = ?").get(path) as any;
  }

  saveSymbols(paperId: number, symbols: any[]) {
    const stmt = this.db.prepare(
      "INSERT INTO symbols (paper_id, symbol, definition, latex) VALUES (?, ?, ?, ?)"
    );
    const insertMany = this.db.transaction((items: any[]) => {
      for (const item of items)
        stmt.run(paperId, item.symbol, item.definition, item.latex);
    });
    insertMany(symbols);
  }

  searchPapers(query: string) {
    return this.db
      .prepare(
        "SELECT * FROM papers WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?"
      )
      .all(`%${query}%`, `%${query}%`, `%${query}%`);
  }
}

export const db = new PaperDatabase();
