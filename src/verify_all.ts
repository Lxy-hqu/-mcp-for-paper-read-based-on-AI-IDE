import { pdfLoader } from './providers/pdf_loader.js';
import { structureParser } from './providers/structure_parser.js';
import { summarizer } from './providers/summarizer.js';
import { mathExplainer } from './providers/math_explainer.js';
import { codeGenerator } from './providers/code_generator.js';
import { visualization } from './providers/visualization.js';
import { reportGenerator } from './providers/report_generator.js';
import { db } from './database.js';
import fs from 'fs';

async function runTests() {
    console.log("🚀 Starting System Verification...");
    let passed = 0;
    let failed = 0;

    function assert(condition: boolean, name: string, message?: string) {
        if (condition) {
            console.log(`✅ [PASS] ${name}`);
            passed++;
        } else {
            console.error(`❌ [FAIL] ${name} - ${message}`);
            failed++;
        }
    }

    // 1. Database
    try {
        console.log("\n--- Testing Database ---");
        db.addPaper("test_dummy.pdf", "Test Paper", "Me", "Abstract content");
        const p = db.getPaperByPath("test_dummy.pdf");
        assert(p?.title === "Test Paper", "Database Insert/Get");
    } catch (e) {
        assert(false, "Database Error", String(e));
    }

    // 2. Structure Parser
    try {
        console.log("\n--- Testing Structure Parser ---");
        const text = "Abstract\nHello\nMethod\nWorld";
        const res = await structureParser.handler({ text });
        const json = JSON.parse(res.content[0].text);
        assert(json.Abstract && json.Abstract.includes("Hello") && json.Method && json.Method.includes("World"), "Structure Parsing");
    } catch (e) {
        assert(false, "Structure Parser Error", String(e));
    }

    // 3. Summarizer
    try {
        console.log("\n--- Testing Summarizer ---");
        const res = await summarizer.handler({ text: "Content", mode: "summary" });
        assert(res.content[0].text.includes("Abstract") || res.content[0].text.includes("AI Generated"), "Summarizer Output");
    } catch (e) {
        assert(false, "Summarizer Error", String(e));
    }

    // 4. Math Explainer
    try {
        console.log("\n--- Testing Math Explainer ---");
        const res = await mathExplainer.handler({ text: "Let $E = mc^2$ be energy." });
        const json = JSON.parse(res.content[0].text);
        const vars = json.ast_analysis && json.ast_analysis[0] ? json.ast_analysis[0].variables : [];
        assert(vars.includes("E") || vars.includes("m") || vars.includes("c") || json.formulas_count > 0, "Math Extraction");
    } catch (e) {
        assert(false, "Math Explainer Error", String(e));
    }

    // 5. Code Generator
    try {
        console.log("\n--- Testing Code Generator ---");
        const res = await codeGenerator.handler({ task_type: "config_yaml", context: "50 epochs, learning rate 0.01" });
        assert(res.content[0].text.includes("epochs: 50"), "Code Generation");
    } catch (e) {
        assert(false, "Code Generator Error", String(e));
    }

    // 6. Visualization
    try {
        console.log("\n--- Testing Visualization ---");
        const res = await visualization.handler({ data: "A -> B", type: "flowchart" });
        assert(res.content[0].text.includes("graph TD"), "Visualization Generation");
    } catch (e) {
        assert(false, "Visualization Error", String(e));
    }

    // 7. Report Generator
    try {
        console.log("\n--- Testing Report Generator ---");
        // We expect it to fail reading the file, but gracefully return an error message
        const res = await reportGenerator.handler({ paper_path: "non_existent.pdf" });
        assert(res.content[0].text.includes("Error reading PDF"), "Report Generator Error Handling");
    } catch (e) {
        assert(false, "Report Generator Crash", String(e));
    }

    // 8. PDF Loader
    try {
        console.log("\n--- Testing PDF Loader ---");
        const res = await pdfLoader.handler({ paths: ["non_existent.pdf"] });
        const json = JSON.parse(res.content[0].text);
        assert(json.results && json.results[0].error !== undefined, "PDF Loader Error Handling");
    } catch (e) {
        assert(false, "PDF Loader Crash", String(e));
    }

    console.log(`\n🏁 Verification Complete: ${passed} Passed, ${failed} Failed`);
    if (failed > 0) process.exit(1);
}

runTests();
