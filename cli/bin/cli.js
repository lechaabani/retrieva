#!/usr/bin/env node

"use strict";

const fs = require("fs");
const path = require("path");
const readline = require("readline");

// ── ANSI color helpers (zero dependencies) ──────────────────────────────────

const c = {
    reset: "\x1b[0m",
    bold: "\x1b[1m",
    dim: "\x1b[2m",
    underline: "\x1b[4m",
    red: "\x1b[31m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    blue: "\x1b[34m",
    magenta: "\x1b[35m",
    cyan: "\x1b[36m",
    white: "\x1b[37m",
    bgGreen: "\x1b[42m",
    bgBlue: "\x1b[44m",
};

function bold(s) { return c.bold + s + c.reset; }
function green(s) { return c.green + s + c.reset; }
function cyan(s) { return c.cyan + s + c.reset; }
function yellow(s) { return c.yellow + s + c.reset; }
function red(s) { return c.red + s + c.reset; }
function dim(s) { return c.dim + s + c.reset; }
function magenta(s) { return c.magenta + s + c.reset; }

// ── Template definitions ────────────────────────────────────────────────────

const TEMPLATES = [
    {
        id: "chatbot-fullpage",
        name: "Chatbot Full Page",
        description: "Full-page chat interface, ChatGPT-style. Great for support portals.",
    },
    {
        id: "search-portal",
        name: "Search Portal",
        description: "Semantic search portal with instant results. Perfect for documentation.",
    },
    {
        id: "faq-bot",
        name: "FAQ Bot",
        description: "Interactive FAQ with suggested questions and conversational answers.",
    },
];

const TEMPLATE_IDS = TEMPLATES.map((t) => t.id);

// ── Argument parsing ────────────────────────────────────────────────────────

function parseArgs(argv) {
    const args = {
        projectName: null,
        template: null,
        apiUrl: null,
        apiKey: null,
        widgetId: null,
        color: null,
        help: false,
    };

    const raw = argv.slice(2);

    for (let i = 0; i < raw.length; i++) {
        const arg = raw[i];

        if (arg === "--help" || arg === "-h") {
            args.help = true;
        } else if (arg === "--template" || arg === "-t") {
            args.template = raw[++i];
        } else if (arg === "--api-url") {
            args.apiUrl = raw[++i];
        } else if (arg === "--api-key") {
            args.apiKey = raw[++i];
        } else if (arg === "--widget-id") {
            args.widgetId = raw[++i];
        } else if (arg === "--color") {
            args.color = raw[++i];
        } else if (!arg.startsWith("-") && !args.projectName) {
            args.projectName = arg;
        }
    }

    return args;
}

// ── Interactive prompts using readline ──────────────────────────────────────

function createInterface() {
    return readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
}

function ask(rl, question, defaultValue) {
    return new Promise((resolve) => {
        const prompt = defaultValue
            ? `${question} ${dim(`(${defaultValue})`)}: `
            : `${question}: `;
        rl.question(prompt, (answer) => {
            resolve(answer.trim() || defaultValue || "");
        });
    });
}

function askChoice(rl, question, choices) {
    return new Promise((resolve) => {
        console.log();
        console.log(bold(question));
        choices.forEach((choice, i) => {
            console.log(`  ${cyan(`${i + 1})`)} ${bold(choice.name)} ${dim("- " + choice.description)}`);
        });
        console.log();

        function prompt() {
            rl.question(`  ${dim("Enter choice")} ${dim(`(1-${choices.length})`)}: `, (answer) => {
                const idx = parseInt(answer.trim(), 10) - 1;
                if (idx >= 0 && idx < choices.length) {
                    resolve(choices[idx].id);
                } else {
                    console.log(red("  Invalid choice. Please enter a number."));
                    prompt();
                }
            });
        }

        prompt();
    });
}

// ── Resolve a template id from user input ───────────────────────────────────

function resolveTemplateId(input) {
    if (!input) return null;
    const lower = input.toLowerCase().replace(/\s+/g, "-");

    // Exact match
    if (TEMPLATE_IDS.includes(lower)) return lower;

    // Partial / alias match
    const aliases = {
        chatbot: "chatbot-fullpage",
        chat: "chatbot-fullpage",
        "chatbot-full-page": "chatbot-fullpage",
        search: "search-portal",
        "search-portal": "search-portal",
        faq: "faq-bot",
        "faq-bot": "faq-bot",
    };

    return aliases[lower] || null;
}

// ── File operations ─────────────────────────────────────────────────────────

function copyDir(src, dest) {
    fs.mkdirSync(dest, { recursive: true });
    const entries = fs.readdirSync(src, { withFileTypes: true });

    for (const entry of entries) {
        const srcPath = path.join(src, entry.name);
        const destPath = path.join(dest, entry.name);

        if (entry.isDirectory()) {
            copyDir(srcPath, destPath);
        } else {
            fs.copyFileSync(srcPath, destPath);
        }
    }
}

function replaceInFile(filePath, replacements) {
    if (!fs.existsSync(filePath)) return;

    let content = fs.readFileSync(filePath, "utf-8");
    for (const [search, replace] of replacements) {
        content = content.split(search).join(replace);
    }
    fs.writeFileSync(filePath, content, "utf-8");
}

// ── Generate the project package.json ───────────────────────────────────────

function createProjectPackageJson(projectDir, projectName) {
    const pkg = {
        name: projectName,
        version: "0.1.0",
        private: true,
        description: `RAG application powered by Retrieva`,
        scripts: {
            serve: "npx serve .",
            start: "npx serve .",
        },
    };
    fs.writeFileSync(
        path.join(projectDir, "package.json"),
        JSON.stringify(pkg, null, 2) + "\n",
        "utf-8"
    );
}

// ── Print help ──────────────────────────────────────────────────────────────

function printHelp() {
    console.log(`
${bold("create-retrieva-app")} ${dim("v0.1.0")}

${bold("USAGE")}
  ${cyan("npx create-retrieva-app")} ${green("<project-name>")} ${dim("[options]")}

${bold("OPTIONS")}
  ${cyan("--template, -t")} ${dim("<name>")}    Template to use: chatbot-fullpage, search-portal, faq-bot
  ${cyan("--api-url")} ${dim("<url>")}           Retrieva API URL (default: http://localhost:8000)
  ${cyan("--api-key")} ${dim("<key>")}           Public API key (rtv_pub_xxx)
  ${cyan("--widget-id")} ${dim("<id>")}          Widget ID (optional)
  ${cyan("--color")} ${dim("<hex>")}             Primary color (default: #4F46E5)
  ${cyan("--help, -h")}                Show this help message

${bold("EXAMPLES")}
  ${dim("# Interactive mode")}
  npx create-retrieva-app my-rag-app

  ${dim("# Non-interactive with all flags")}
  npx create-retrieva-app my-rag-app \\
    --template chatbot-fullpage \\
    --api-url https://api.example.com \\
    --api-key rtv_pub_xxx \\
    --widget-id wgt_abc123

${bold("TEMPLATES")}
  ${cyan("chatbot-fullpage")}   Full-page chat interface, ChatGPT-style
  ${cyan("search-portal")}     Semantic search with instant results
  ${cyan("faq-bot")}           Interactive FAQ with suggested questions
`);
}

// ── Print success ───────────────────────────────────────────────────────────

function printSuccess(projectName, templateId) {
    const line = "=".repeat(50);
    console.log();
    console.log(green(line));
    console.log();
    console.log(`  ${green("Success!")} Created ${bold(projectName)} with the ${cyan(templateId)} template.`);
    console.log();
    console.log(`  ${bold("Next steps:")}`);
    console.log();
    console.log(`    ${cyan("cd")} ${projectName}`);
    console.log(`    ${cyan("npx serve .")}`);
    console.log();
    console.log(`  Then open ${cyan("http://localhost:3000")} in your browser.`);
    console.log();
    console.log(`  ${dim("Edit")} ${yellow("app.js")} ${dim("to update your Retrieva config.")}`);
    console.log(`  ${dim("Edit")} ${yellow("styles.css")} ${dim("to customize the theme.")}`);
    console.log();
    console.log(green(line));
    console.log();
}

// ── Validate color ──────────────────────────────────────────────────────────

function isValidColor(color) {
    return /^#[0-9A-Fa-f]{6}$/.test(color);
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
    const args = parseArgs(process.argv);

    if (args.help) {
        printHelp();
        process.exit(0);
    }

    console.log();
    console.log(`  ${bold(magenta("create-retrieva-app"))} ${dim("v0.1.0")}`);
    console.log();

    let projectName = args.projectName;
    let templateId = resolveTemplateId(args.template);
    let apiUrl = args.apiUrl;
    let apiKey = args.apiKey;
    let widgetId = args.widgetId;
    let color = args.color;

    // Check if we need interactive mode
    const needsInteractive = !projectName || !templateId || !apiUrl || !apiKey;

    let rl = null;
    if (needsInteractive) {
        rl = createInterface();
    }

    try {
        // 1. Project name
        if (!projectName) {
            projectName = await ask(rl, `  ${bold("Project name?")}`, "my-rag-app");
        }

        // Validate project name
        if (!projectName || /[<>:"/\\|?*]/.test(projectName)) {
            console.error(red("\n  Error: Invalid project name.\n"));
            process.exit(1);
        }

        // Check if directory already exists
        const projectDir = path.resolve(process.cwd(), projectName);
        if (fs.existsSync(projectDir)) {
            console.error(red(`\n  Error: Directory "${projectName}" already exists.\n`));
            process.exit(1);
        }

        // 2. Template
        if (!templateId) {
            templateId = await askChoice(rl, "  Choose a template:", TEMPLATES);
        }

        if (!TEMPLATE_IDS.includes(templateId)) {
            console.error(red(`\n  Error: Unknown template "${templateId}".`));
            console.error(dim(`  Available templates: ${TEMPLATE_IDS.join(", ")}\n`));
            process.exit(1);
        }

        // 3. API URL
        if (!apiUrl) {
            apiUrl = await ask(rl, `  ${bold("Retrieva API URL?")}`, "http://localhost:8000");
        }

        // 4. API Key
        if (!apiKey) {
            apiKey = await ask(rl, `  ${bold("Public API Key?")}`, "");
        }

        if (!apiKey) {
            apiKey = "YOUR_PUBLIC_API_KEY";
        }

        // 5. Widget ID
        if (!widgetId) {
            widgetId = await ask(rl, `  ${bold("Widget ID?")} ${dim("(optional, press Enter to skip)")}`, "");
        }

        if (!widgetId) {
            widgetId = "YOUR_WIDGET_ID";
        }

        // 6. Primary color
        if (!color) {
            color = await ask(rl, `  ${bold("Primary color?")}`, "#4F46E5");
        }

        if (!color) {
            color = "#4F46E5";
        }

        if (!isValidColor(color)) {
            console.error(red(`\n  Error: Invalid hex color "${color}". Use format #RRGGBB.\n`));
            process.exit(1);
        }

        // Close readline if we opened it
        if (rl) {
            rl.close();
        }

        // ── Scaffold the project ────────────────────────────────────────

        console.log();
        console.log(`  ${dim("Scaffolding project in")} ${cyan(projectDir)} ${dim("...")}`);

        // Resolve the template source directory
        const templatesRoot = path.join(__dirname, "..", "templates");
        const templateSrc = path.join(templatesRoot, templateId);

        if (!fs.existsSync(templateSrc)) {
            console.error(red(`\n  Error: Template directory not found at ${templateSrc}\n`));
            process.exit(1);
        }

        // Copy template files
        copyDir(templateSrc, projectDir);

        // Replace config placeholders in app.js
        const appJsPath = path.join(projectDir, "app.js");
        replaceInFile(appJsPath, [
            ['"http://localhost:8000"', JSON.stringify(apiUrl)],
            ['"YOUR_PUBLIC_API_KEY"', JSON.stringify(apiKey)],
            ['"YOUR_WIDGET_ID"', JSON.stringify(widgetId)],
        ]);

        // Replace primary color in styles.css
        if (color !== "#4F46E5") {
            const cssPath = path.join(projectDir, "styles.css");
            replaceInFile(cssPath, [
                ["--primary: #4F46E5;", `--primary: ${color};`],
            ]);

            // Also update hover color (darken by shifting slightly)
            // Simple approach: replace the default hover color too
            const hoverColor = darkenColor(color, 15);
            replaceInFile(cssPath, [
                ["--primary-hover: #4338CA;", `--primary-hover: ${hoverColor};`],
            ]);

            // Update the light variant
            const lightColor = lightenColor(color, 90);
            replaceInFile(cssPath, [
                ["--primary-light: #EEF2FF;", `--primary-light: ${lightColor};`],
            ]);
        }

        // Create package.json in the project directory
        createProjectPackageJson(projectDir, projectName);

        // Print success
        printSuccess(projectName, templateId);

    } catch (err) {
        if (rl) rl.close();
        console.error(red(`\n  Error: ${err.message}\n`));
        process.exit(1);
    }
}

// ── Color utilities ─────────────────────────────────────────────────────────

function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return [r, g, b];
}

function rgbToHex(r, g, b) {
    const toHex = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

function darkenColor(hex, percent) {
    const [r, g, b] = hexToRgb(hex);
    const factor = 1 - percent / 100;
    return rgbToHex(r * factor, g * factor, b * factor);
}

function lightenColor(hex, percent) {
    const [r, g, b] = hexToRgb(hex);
    const factor = percent / 100;
    return rgbToHex(
        r + (255 - r) * factor,
        g + (255 - g) * factor,
        b + (255 - b) * factor
    );
}

// ── Run ─────────────────────────────────────────────────────────────────────
main();
